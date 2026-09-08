# AREA03: bulk recovery uses the primary volume

Research proposal consistency correction, not a production change or a new gate.
The area's primary geometry remains W. Both bulk Q=I/dx and its Mesh1D area average
now use the same volume: average=diff(W)/dx. Face area A(x), perimeter, momentum
source p diff(A), inverse certificates, all stage guards and NASA are unchanged.
The average is the represented volume per derived length; it is explicitly not
the separately rounded integral between inverse-rounded coordinates. Their
difference is already accounted by AreaState inverse residuals. No inventory,
energy, or physical endpoint is corrected.

Recovery audit: bulk divides Q by this average; reconstruction ghosts directly
divide I by diff(W); regional recovery passes I*(dx/diff(W)) to the unit-area
solver, which divides by dx. The latter and bulk retain ordinary floating
multiply/divide roundoff (2.22e-16 relative in the thin-cell probe), not the
1.70e-7 geometric inconsistency. Initialization and stage guards continue using
the same authoritative volumes. No assertion of bitwise equivalence between
different arithmetic routes is made.

`area03_audit.py` executes the archived and corrected implementations on the
actual NASA thin-cell reproducer. Bulk pressure changes from approximately
99999.983 Pa to 100000.00000012126 Pa, equal to regional recovery in both cells.
17 area/advisor tests pass, including the instrumented actual kernel path,
immutable inventory, endpoint certificates, remap, both FE guards and A=1
bitwise route comparison. Six advisor controls remain bitwise identical.
The ten-step rest control was rerun: final inventory differs by at most
2.23e-15 and accumulated faces by 4.04e-11 from the archived result; these are
new results, not reused bitwise evidence. The archive is
`historical/before-bulk-W-volume`. `area03-audit.json` binds sources and arrays.
Variable-area wave acceptance and physical boundary births/exits remain open.
