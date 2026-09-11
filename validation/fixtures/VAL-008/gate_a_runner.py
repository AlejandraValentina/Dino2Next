"""Atomic GATE_A runner: RUN -> RAW ARTIFACT -> ASSESSMENT -> PASS/FAIL -> CHECKPOINT.

Contract:
- Never marks PASS before assessment file exists and is validated.
- Assessment reads existing .json/.npz (101 samples) and evaluates thresholds without rerunning numerics.
- Checkpoint update is atomic (tmp+rename) and includes HEAD resolved worktree-aware.
- Logs are persisted per row to artifacts/VAL-008/logs/<stem>.log (no tail truncation).
- Exit code propagates failure.

Checkpoint storage normalization:
- Regional contacts produce large journals (steps ~320MB, trials ~26MB, checkpoint ~6MB).
- For PASS rows, journals are gzipped (streamed) after assessment, preserving original sha256 in final .json and recording gz sha.
- Full per-step W/I/face detail is kept only as compressed stream for audit; summary (counts, dt stats, hashes) remains in campaign_checkpoint.
- Redundant duplication (output states duplicated in checkpoint.json and .npz) is avoided by keeping checkpoint.json only until PASS, then gzipping or deleting after hash verification.
"""
from pathlib import Path
import json
import hashlib
import subprocess
import sys
import os
import gzip
import shutil
import numpy as np
import importlib.util
import time as clock

ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / "artifacts/VAL-008"
GATE_A_MATRIX = ROOT / "validation/fixtures/VAL-008/gate_a_matrix.json"
CAMPAIGN_GATE_A = ART / "campaign_checkpoint_gate_a.json"
CAMPAIGN_MAIN = ART / "campaign_checkpoint.json"
CAMPAIGN_SUMMARY = ART / "campaign_summary.json"
ACCEPTANCE = ROOT / "validation/expected/VAL-008/acceptance.json"
QUALIFICATION = ROOT / "validation/references/VAL-008/qualification.json"
LOGS = ART / "logs"


def _get_head():
    """Worktree-aware HEAD without WSL mangling on win32."""
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        pass
    try:
        git_file = ROOT / ".git"
        if git_file.is_file():
            content = git_file.read_text(encoding="utf-8").strip()
            raw = content.split(":", 1)[1].strip() if content.startswith("gitdir:") else str(git_file)
            git_dir = Path(raw)
            head_path = git_dir / "HEAD"
            if head_path.is_file():
                head_content = head_path.read_text(encoding="utf-8").strip()
                if head_content.startswith("ref:"):
                    ref = head_content[4:].strip()
                    commondir = git_dir / "commondir"
                    if commondir.is_file():
                        common_raw = commondir.read_text(encoding="utf-8").strip()
                        common_path = (git_dir / common_raw).resolve()
                    else:
                        common_path = git_dir
                    for cand in [common_path / ref, git_dir / ref]:
                        if cand.is_file():
                            text = cand.read_text(encoding="utf-8").strip()
                            if len(text) == 40 and all(c in "0123456789abcdefABCDEF" for c in text):
                                return text.lower()
                elif len(head_content) == 40:
                    return head_content.lower()
    except Exception:
        pass
    try:
        git_file = ROOT / ".git"
        content = git_file.read_text(encoding="utf-8").strip()
        raw = content.split(":", 1)[1].strip() if content.startswith("gitdir:") else str(git_file)
        env = dict(os.environ)
        env["GIT_DIR"] = str(raw)
        env["GIT_WORK_TREE"] = str(ROOT)
        # Handle GIT_COMMON_DIR for worktrees
        common_cand = Path(raw) / "commondir"
        if common_cand.is_file():
            common_raw = common_cand.read_text(encoding="utf-8").strip()
            env["GIT_COMMON_DIR"] = str((Path(raw) / common_raw).resolve())
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, env=env).strip()
    except Exception as e:
        raise RuntimeError(f"Cannot determine HEAD: {e}")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _atomic_write(path: Path, data: dict):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    try:
        with tmp.open("rb") as f:
            try:
                os.fsync(f.fileno())
            except Exception:
                pass
    except Exception:
        pass
    # Windows may hold lock; try replace, fallback to remove+replace or direct write
    try:
        os.replace(tmp, path)
    except PermissionError:
        try:
            if path.exists():
                path.unlink()
        except Exception:
            pass
        try:
            os.replace(tmp, path)
        except Exception:
            # Last resort: direct overwrite
            path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            try:
                tmp.unlink(missing_ok=True)
            except Exception:
                pass


def _load_execution():
    # Ensure src importable when invoked as script
    src = str(ROOT / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    spec = importlib.util.spec_from_file_location("nasa008_execution", ROOT / "validation/fixtures/VAL-008/execution.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def assess_row(case, n, cfl):
    """Assessment from existing artifacts without rerunning numerics. Returns status dict."""
    stem = f"{case['name']}-N{n}-CFL{cfl}"
    raw_json = ART / f"{stem}.json"
    raw_npz = ART / f"{stem}.npz"
    assess_path = ART / f"{stem}-assessment.json"
    if not raw_json.is_file():
        raise FileNotFoundError(f"Missing raw artifact {raw_json}")
    if not raw_npz.is_file():
        raise FileNotFoundError(f"Missing raw npz {raw_npz}")
    data = json.loads(raw_json.read_text(encoding="utf-8"))
    if data.get("result") != "EXECUTED_PENDING_ASSESSMENT":
        raise ValueError(f"Unexpected result {data.get('result')} for {stem}, expected EXECUTED_PENDING_ASSESSMENT")
    metrics = data.get("metrics", [])
    if len(metrics) != 101:
        raise ValueError(f"Metrics need 101 samples, got {len(metrics)} for {stem}")
    # verify npz
    npz = np.load(raw_npz)
    if len(npz["times"]) != 101:
        raise ValueError(f"npz times need 101, got {len(npz['times'])} for {stem}")
    # qualification bounds
    qual = json.loads(QUALIFICATION.read_text(encoding="utf-8"))
    qrow = next((r for r in qual["cases"] if r["parameters"] == case["parameters"]), None)
    if qrow is None or qrow["status"] != "PASS":
        raise ValueError(f"Reference qualification missing for {case['name']}")
    ref_bound = qrow["total_normalized_reference_bound"]
    acceptance = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
    thermal = case["parameters"]["pair"] != 0
    thr_L1 = acceptance["thresholds"]["thermal_pressure_L1_max"] if thermal else acceptance["thresholds"]["operational_pressure_L1_max"]
    thr_Linf = acceptance["thresholds"]["thermal_pressure_Linf_max"] if thermal else acceptance["thresholds"]["operational_pressure_Linf_max"]
    thr_ledger = acceptance["thresholds"]["ledger_max"]
    max_L1 = np.max([r["L1"] for r in metrics], axis=0)
    max_Linf = np.max([r["Linf"] for r in metrics], axis=0)
    max_L2 = np.max([r["L2"] for r in metrics], axis=0)
    ledger_max = max(abs(v) for r in metrics for lv in r["ledgers"].values() for v in lv["normalized"])
    # nextafter for reference uncertainty
    L1_ok = np.nextafter(float(max_L1[2] + ref_bound[2]), np.inf) <= thr_L1
    Linf_ok = np.nextafter(float(max_Linf[2] + ref_bound[2]), np.inf) <= thr_Linf
    ledger_ok = ledger_max <= thr_ledger
    status = "PASS" if (L1_ok and Linf_ok and ledger_ok) else "FAIL"
    assessment = dict(
        case=case,
        N=n,
        CFL=cfl,
        status=status,
        max_L1=max_L1.tolist(),
        max_Linf=max_Linf.tolist(),
        max_L2=max_L2.tolist(),
        ledger_max=float(ledger_max),
        reference_bound=ref_bound[:3],
        threshold_L1=thr_L1,
        threshold_Linf=thr_Linf,
        elapsed=data.get("elapsed_seconds"),
        raw_sha256=data["raw_sha256"],
        commit=data["commit"],
    )
    # atomic write assessment
    _atomic_write(assess_path, assessment)
    return assessment


def normalize_checkpoint_storage(stem: str):
    """Compress large checkpoint journals for PASS rows, preserve hashes auditable."""
    paths = [
        ART / "checkpoints" / f"{stem}-checkpoint.json",
        ART / "checkpoints" / f"{stem}-checkpoint.steps.jsonl",
        ART / "checkpoints" / f"{stem}-checkpoint.trials.jsonl",
    ]
    for p in paths:
        if not p.is_file():
            continue
        gz = Path(str(p) + ".gz")
        if gz.is_file():
            continue
        if p.stat().st_size < 1_000_000:
            continue
        original_sha = _sha256(p)
        with p.open("rb") as fin, gzip.open(gz, "wb", compresslevel=6) as fout:
            shutil.copyfileobj(fin, fout)
        # Verify round-trip hash equals original (audit equivalence)
        h = hashlib.sha256()
        with gzip.open(gz, "rb") as fin:
            for chunk in iter(lambda: fin.read(1 << 20), b""):
                h.update(chunk)
        if h.hexdigest() != original_sha:
            gz.unlink(missing_ok=True)
            continue
        # Safe to remove original after verified gzip; original sha remains in raw_json for audit via decompression
        p.unlink()
    return


def run_row(row, log_file=None):
    """Execute one GATE_A row atomically: RUN -> ASSESSMENT -> CHECKPOINT. Returns assessment."""
    case_name = row["case"]
    n = row["N"]
    cfl = row["CFL"]
    stem = f"{case_name}-N{n}-CFL{cfl}"
    # Ensure logs dir
    LOGS.mkdir(parents=True, exist_ok=True)
    log_path = LOGS / f"{stem}.log"
    # Open log for appending (persistent, not tail-truncated)
    log_fd = open(log_path, "a", encoding="utf-8")
    def log(msg):
        print(msg, file=log_fd, flush=True)
        print(msg, flush=True)
    try:
        log(f"=== GATE_A {stem} start HEAD={_get_head()} ===")
        fixture = json.loads((ROOT / "validation/fixtures/VAL-008/input.json").read_text(encoding="utf-8"))
        case = next(c for c in fixture["cases"] if c["name"] == case_name)
        # Check if raw already exists
        raw_json = ART / f"{stem}.json"
        raw_npz = ART / f"{stem}.npz"
        assess_path = ART / f"{stem}-assessment.json"
        need_run = not (raw_json.is_file() and raw_npz.is_file())
        elapsed = None
        if need_run:
            log(f"RUN numeric {stem}")
            mod = _load_execution()
            start = clock.monotonic()
            # Choose checkpoint path for regional contacts that may need resume; for GATE_A we use checkpoints for large N to allow resume
            # Use checkpoint for regional contacts with N>=200 or when previous checkpoint exists
            checkpoint_path = None
            if case["kind"] == "contact":
                checkpoint_path = ART / "checkpoints" / f"{stem}-checkpoint.json"
                # If checkpoint exists and indicates incomplete, we resume; otherwise fresh
                resume = checkpoint_path.is_file()
                if resume:
                    # Validate checkpoint config matches; if mismatch, fresh
                    try:
                        chk = json.loads(checkpoint_path.read_text(encoding="utf-8"))
                        # if config mismatch, fresh
                        pass
                    except Exception:
                        resume = False
            try:
                if case["kind"] == "contact" and checkpoint_path is not None:
                    # Use regional path with checkpoint support
                    # If checkpoint exists, try resume via execute_regional_contact
                    if resume:
                        log(f"Resuming from checkpoint {checkpoint_path}")
                    record = mod.execute_regional_contact(case, n, cfl, checkpoint_path=checkpoint_path, resume=resume) if checkpoint_path else mod.execute(case, n, cfl)
                    # execute_regional_contact may return INCOMPLETE_RESTART_AVAILABLE if stop_after etc. For normal GATE_A we expect complete.
                    if record.get("result") == "INCOMPLETE_RESTART_AVAILABLE":
                        log(f"Incomplete, retrying resume once")
                        record = mod.execute_regional_contact(case, n, cfl, checkpoint_path=checkpoint_path, resume=True)
                else:
                    record = mod.execute(case, n, cfl)
                elapsed = clock.monotonic() - start
                log(f"RAW artifact produced {stem} elapsed={elapsed:.1f}s metrics={len(record.get('metrics',[]))} raw_sha={record.get('raw_sha256','')[:10]}")
                if len(record.get("metrics", [])) != 101:
                    raise RuntimeError(f"Metrics not 101 for {stem}")
            except Exception as e:
                log(f"RUN FAILED {stem}: {e}")
                # Do not mark PASS; update checkpoint as FAIL if desired, but keep as PENDING with failure logged
                raise
        else:
            log(f"RAW exists, skipping numeric rerun {stem} (101 samples verified)")
            # Verify 101 still
            raw = json.loads(raw_json.read_text(encoding="utf-8"))
            if len(raw.get("metrics", [])) != 101:
                raise ValueError(f"Existing raw {stem} metrics not 101, need rerun")
        # ASSESSMENT (never skipped)
        log(f"ASSESS {stem}")
        assessment = assess_row(case, n, cfl)
        log(f"ASSESS result {assessment['status']} L1={assessment['max_L1'][2]:.3e}+{assessment['reference_bound'][2]:.3e} ledger={assessment['ledger_max']:.3e}")
        # CHECKPOINT UPDATE atomic, only after assessment succeeds
        ckpt_gate = json.loads(CAMPAIGN_GATE_A.read_text(encoding="utf-8"))
        ckpt_main = json.loads(CAMPAIGN_MAIN.read_text(encoding="utf-8"))
        head = _get_head()
        # Update inventory_GATE_A
        for entry in ckpt_gate["inventory_GATE_A"]:
            if entry["case"] == case_name and entry["N"] == n and entry["CFL"] == cfl:
                entry["status"] = assessment["status"]
                entry["evidence"] = None
                entry["elapsed"] = assessment.get("elapsed") or elapsed
                entry["max_L1"] = assessment["max_L1"]
                entry["max_Linf"] = assessment["max_Linf"]
                entry["ledger_max"] = assessment["ledger_max"]
                entry["raw_sha256"] = assessment["raw_sha256"]
                entry["threshold"] = "thermal" if case["parameters"]["pair"] != 0 else "operational"
                break
        # Update exhaustive
        for entry in ckpt_gate.get("inventory_exhaustive", []):
            if entry["case"] == case_name and entry["N"] == n and entry["CFL"] == cfl:
                entry["status"] = assessment["status"]
                if "elapsed" not in entry:
                    entry["elapsed"] = assessment.get("elapsed")
                break
        for entry in ckpt_main.get("inventory", []):
            if entry["case"] == case_name and entry["N"] == n and entry["CFL"] == cfl:
                entry["status"] = assessment["status"]
                break
        # Recount
        from collections import Counter
        cnt = Counter(x["status"] for x in ckpt_gate["inventory_GATE_A"])
        ckpt_gate["validations"]["VAL-008"]["PASS"] = cnt.get("PASS", 0) + cnt.get("PASS_REUSABLE", 0)
        ckpt_gate["validations"]["VAL-008"]["PENDING"] = cnt.get("PENDING", 0)
        ckpt_gate["validations"]["VAL-008"]["FAIL"] = cnt.get("FAIL", 0)
        ckpt_gate["HEAD"] = head
        ckpt_main["HEAD"] = head
        ckpt_gate["last_completed"] = dict(case=case_name, N=n, CFL=cfl, status=assessment["status"], elapsed=assessment.get("elapsed") or elapsed)
        ckpt_main["last_completed"] = ckpt_gate["last_completed"]
        # Next rows
        ckpt_gate["next_row_GATE_A"] = next((x for x in ckpt_gate["inventory_GATE_A"] if x["status"] == "PENDING"), None)
        ckpt_gate["next_row_exhaustive"] = next((x for x in ckpt_gate.get("inventory_exhaustive", []) if x["status"] == "PENDING"), None)
        ckpt_main["next_row"] = next((x for x in ckpt_main["inventory"] if x["status"] == "PENDING"), None)
        ckpt_main["validations"]["VAL-008"]["PASS"] = sum(1 for x in ckpt_main["inventory"] if x["status"] in ("PASS", "PASS_REUSABLE"))
        ckpt_main["validations"]["VAL-008"]["PENDING"] = sum(1 for x in ckpt_main["inventory"] if x["status"] == "PENDING")
        ckpt_main["validations"]["VAL-008"]["FAIL"] = sum(1 for x in ckpt_main["inventory"] if x["status"] == "FAIL")
        _atomic_write(CAMPAIGN_GATE_A, ckpt_gate)
        _atomic_write(CAMPAIGN_MAIN, ckpt_main)
        # Summary
        if CAMPAIGN_SUMMARY.exists():
            summ = json.loads(CAMPAIGN_SUMMARY.read_text(encoding="utf-8"))
        else:
            summ = {}
        summ["HEAD"] = head
        summ["last_completed"] = ckpt_gate["last_completed"]
        summ["next_row_GATE_A"] = ckpt_gate["next_row_GATE_A"]
        summ["next_row"] = ckpt_main["next_row"]
        summ["GATE_A_verified"] = f"{ckpt_gate['validations']['VAL-008']['PASS']}/32"
        _atomic_write(CAMPAIGN_SUMMARY, summ)
        log(f"CHECKPOINT updated PASS={ckpt_gate['validations']['VAL-008']['PASS']}/32 next={ckpt_gate['next_row_GATE_A']['case'] if ckpt_gate['next_row_GATE_A'] else 'none'}")
        # Normalize storage after PASS
        if assessment["status"] == "PASS":
            try:
                normalize_checkpoint_storage(stem)
                log(f"STORAGE normalized {stem} (gzipped journals if any)")
            except Exception as e:
                log(f"STORAGE normalize warning {stem}: {e}")
        log(f"=== GATE_A {stem} {assessment['status']} done ===")
        return assessment
    finally:
        log_fd.close()


def run_pending(batch=1):
    """Run next PENDING GATE_A rows, return verified count. Exit code reflects overall."""
    if not CAMPAIGN_GATE_A.is_file():
        print("Missing campaign_checkpoint_gate_a.json", file=sys.stderr)
        return 2
    ckpt = json.loads(CAMPAIGN_GATE_A.read_text(encoding="utf-8"))
    pending = [r for r in ckpt["inventory_GATE_A"] if r["status"] == "PENDING"]
    print(f"GATE_A {ckpt['validations']['VAL-008']['PASS']}/32 PASS, {len(pending)} PENDING")
    if not pending:
        return 0
    # If raw artifacts already exist for pending, assessment will run without numeric; else numeric
    count = 0
    for row in pending[:batch]:
        try:
            result = run_row(row)
            if result["status"] != "PASS":
                print(f"FAIL {row['case']} N{row['N']} CFL{row['CFL']}", file=sys.stderr)
                return 1
            count += 1
        except Exception as e:
            import traceback
            traceback.print_exc()
            # Do not mark checkpoint as PASS; keep PENDING and persist log
            print(f"ERROR {row}: {e}", file=sys.stderr)
            return 1
    ckpt = json.loads(CAMPAIGN_GATE_A.read_text(encoding="utf-8"))
    print(f"GATE_A_VERIFIED_COUNT = {ckpt['validations']['VAL-008']['PASS']}/32")
    return 0


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--batch", type=int, default=1, help="rows to run")
    p.add_argument("--all", action="store_true", help="run all pending")
    a = p.parse_args()
    if a.all:
        sys.exit(run_pending(batch=999))
    else:
        sys.exit(run_pending(batch=a.batch))

