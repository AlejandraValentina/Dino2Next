# Current hybrid evidence, with historical failures retained

Author evidence awaiting independent coverage review. The existing local/Y2,
hybrid-function and exact-overlap reviews have narrower scopes; none approves
the final GEN1 recipe or the complete VAL008 matrix.

The current FastHybrid method was freshly executed for all nine physical
contact combinations: three original composition/temperature pairs and
u=0,+100,-100 m/s. They use the same small 24-cell prototype setup, .001 s,
declared initial interface .5+1e-10 m and fixed zero-gradient control ends.
This is not the original guarded N100/200/400 validation geometry. No claim
that checking characteristic speeds alone qualifies that prototype domain
under SV008 is made. The future original fixture must retain its full guards.

All nine completed in 98.17 s. Maximum accepted-state pressure error was
3.786e-7 Pa. Every accepted state, stage flux, guard candidate, transaction and
initial inventory is retained. A separate, no-RHS audit replays the remap and
logged stage transfers, verifies each accepted state bitwise, then checks
all 1953 selected initial/Y0/Y1/Y2/final physical states. Including FE states,
the maximum pressure error is 9.493e-7 Pa (also outside the contact-adjacent
intervals); maximum velocity error is 7.10e-10 m/s. Maximum |u|+a is 913.546
m/s, below the checked 1293 envelope. Stage GCL residual is 9.37e-17 m.

The audit checks exact zero mass/species/origin transfer across the moving
material face separately from global conservation. ST003 residuals are at
most 1.55e-16 over the computational domain and 3.42e-16 in the fixed [0,1]
window. Window transfers are measured at actual integration faces 0 and 1,
which remain ordinary fixed faces in these runs. Qref, ambient inputs and
absolute throughput are explicit in the raw reports. The larger FE pressure
maximum is retained; it is not replaced by the smaller accepted-state maximum.

One directed shock parameter set, original pair0/ratio2, was executed with
the original SV008 2544 m/s guard setup at N80 and N160, .0002 s and all 101
sample times. Costs were 52.73 s and 135.13 s. The already qualified independent
NASA Riemann reference was reused with its full source/certificate hashes.
No new oracle or change in pressure meaning was introduced. Candidate pressure
and velocity are physical regional averages, not EOS of aggregate conserved
averages. Postprocessing measures all 101 states and reconstructs all 489/861
selected physical stages exactly from logged fluxes without rerunning an RHS.
Maximum characteristic speeds are below 639 m/s; both computational and
fixed-window ledgers satisfy ST003.

Time-maximum normalized L1 errors (rho,u,p), including reference uncertainty:

| N | rho | u | p |
|---|---|---|---|
| 80 | .01031722 | .00928684 | .02001531 |
| 160 | .00514545 | .00460913 | .00993794 |

Observed two-level orders are 1.00369, 1.01069 and 1.01008. This is decreasing
error for one directed shock set, not the complete last-two-level contractual
sequence, not global second-order accuracy and not full VAL008 acceptance.
Other shock composition/ratio combinations, N320/N640 and the original CFL
coverage remain obligations for the integrated method. The original ordinary
kernel failures and every earlier prototype result remain preserved.

`coverage-manifest.json` binds the current contact source/raw summaries and
stage audit; `shock-summary.json` binds both directed shock runs and all-time
assessments. `hybrid-provenance.json` resolves the original basename collision
between material/prototype.py and local_material/prototype.py without changing
or rerunning its historical trajectory. Current reports use distinct paths.
The evidence remains synthetic numerical verification. No experimental or
predictive validation is asserted.
