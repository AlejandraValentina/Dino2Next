# Exact two-pointer overlap search: bounded author validation

Frozen prototype.py c2f9d81ce57a8cae741839b5522185e10485c7cabe1070a935500a13387d3eee and hybrid.py were not edited. The experimental subclass changes target enumeration only. Its generated method is retained for review. The same min/max overlap expressions, donor and ascending target order, amount arithmetic and final residual assignment remain intact.

For sorted disjoint partitions, targets ending at or before the donor's left endpoint cannot overlap this donor or any later donor. Advancing the persistent start index is therefore exact. Scanning until a target starts at or after the donor's right endpoint retains exactly the positive intersections in their original order. Total positive intersections between two partitions are linear in their combined interval count. Other work in reorganize, including label/exclusion handling and NASA recovery, is unchanged.

The adversarial test passed for 103 partition pairs: randomized uneven intervals, equal/touching edges, signed zero, a smallest-subnormal interval and one-to-many/many-to-one intersections. Target indices and overlap float bytes match the original exhaustive expression.

Eleven actual NASA reorganizations compare original and experimental solver: crossing and tiny material slab at N24/200/800/1600, plus smooth-composition single-label, aligned and negative-coordinate-domain cases. All inventory/edge arrays and labels match bitwise; all diagnostic JSON files also have identical byte hashes. Original input bytes remain unchanged. No integration was performed.

Measured reorganize-only costs (single pilot, includes unchanged NASA recovery):

| N | Crossing old → new (s) | Thin slab old → new (s) |
|---|---|---|
| 24 | 0.02066 → 0.01073 | 0.01057 → 0.01164 |
| 200 | 0.04856 → 0.02410 | 0.04478 → 0.02552 |
| 800 | 0.36133 → 0.06743 | 0.38884 → 0.05588 |
| 1600 | 1.30041 → 0.10096 | 1.20720 → 0.09461 |

Small cases dominated by common recovery can be slower within measured variability. N1600 improves about 12.8× in these pilots; this is not a complete solver speedup or independent review. No remap equation, material label, exclusion threshold, EOS or scientific gate changes. Artifacts fast-overlap-report.json, paired NPZ and diagnostic JSON, source manifest, generated method, logs and scripts provide the evidence. Parent decides integration only after independent review.
