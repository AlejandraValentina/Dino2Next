# Lossless portable material evidence

The large raw JSON files listed in portable-data-manifest.json are stored in portable-data.zip to avoid publishing tens of megabytes of repeated diagnostic text. The ZIP contains the exact original scientific bytes, including the pre-fix historical records. Author manifests and independent-review hashes retain their original meanings.

Run `python research/bcr_s06_material_resolution/local_material/restore_evidence.py` after checkout. It verifies archive/member hashes and restores the original relative paths. Existing differing files cause failure and are preserved. Extracted raw files are ignored by Git; their archive and complete hashes are versioned. This is a storage transformation, not a regenerated trajectory, altered diagnostic, or numerical PASS. Source and review files remain directly readable in the PR.
