# Volumetric timestep advisor: scientific proposal requiring adjudication

This increment adds advisor.py and an experimental subclass; it does not alter frozen area_solver.py f23a7442 or any flux, source, EOS, geometry/remap or H/L guard formula. The complete pre-advisor evidence remains under historical/before-volume-advisor. Its status is a proposed scientific coupling of the W coordinate to time-step selection, not a software defect fix.

For region i, let V_i=W_R−W_L, dx_i=x_R−x_L, A_L,A_R>0, numerical face speed s_f=Wdot_f/A_f and regional sound speed a_i from accepted NASA. Define λ_L=a_i+|u_i−s_L|, λ_R=a_i+|u_i−s_R|. Evaluate the following at both the initial state and first FE endpoint:

    dt_x = 0.2 dx_i / max(λ_L,λ_R)
    dt_V = 0.2 V_i / max(A_L λ_L,A_R λ_R)
    dt_shrink = 0.5 V_i / (−Vdot_i) if Vdot_i<0, else +infinity
    Vdot_i = Wdot_R−Wdot_L
    dt_limit = min over all regions and all three bounds.

The factors 0.2 and 0.5 are retained. The acoustic factor multiplies the quotient after division. No tolerance, physical input or acceptance threshold changes. The inherited length-based predictor is retained rather than presumed redundant. The volumetric bound gives dt*A_f*λ_f/V_i ≤0.2 at either face: both face rates combined are bounded by 0.4 at the frozen stage. This is a local geometric/transport predictor, **not a proof of invariant-domain positivity for nonlinear NASA fluxes or sources**.

For a shrinking region, the frozen-stage FE geometry obeys V_FE=V+dt Vdot≥V/2 in exact arithmetic under dt_shrink. Applying this check to Y0 and again to Y1 with the same trial dt covers both Euler volume endpoints; their convex combination then has positive volume. Structural/roundoff checks remain necessary. The final physical state and both FE states still undergo the existing geometry/EOS/constituent H/L guards. No projection or inventory repair is performed.

The same dt must satisfy the bound at Y0 and Y1. If Y1 fails, reject the complete trial and let the existing caller retry with a smaller dt. Do not shorten dt after building Y1 or commit an earlier ledger. Each check records transaction ID, stage, requested dt, all component bounds, volume rates and areas. These are bound-check records; the associated transaction record determines whether the overall trial was accepted.

Neither added bound is silently assumed sufficient or universally redundant. Steep A changes V/max(A_f) relative to dx, so the old dx-only predictor can miss the stricter volume-based scale. Conversely, when moving material faces have s≈u at high velocity in decreasing area, Vdot can be large and negative even though |u−s| is small; the shrinking-volume check then supplies a different restriction. Tests exhibit both cases and the constant-area reduction. An inherited geometric source or complicated state can still fail EOS despite all predictors: the H/L/FE/final guards remain mandatory.

Seven tests cover the two distinct restrictions, constant-area equivalence of bounds, positive increasing/decreasing/steep polynomials with actual moving material states, rejection immediately above a stage-0 bound, and an explicitly injected second-stage bound failure with unchanged input and unchanged trial dt. The injected case tests transactional control flow and is not a physical solution. The three physical polynomials are A=1+20x², A=4−3x+x², and A=0.1+10x; their positivity is accepted by PolynomialSegment. Actual controls use both signs of velocity and accepted NASA thermal/composition states, checking one complete advised step and its records rather than claiming a uniform moving-flow oracle.

This addresses the preliminary dx-only limitation identified in area_hybrid. It does not close physical endpoint birth/exit, segment joins, or variable-area wave convergence. The proposed dt coordinate coupling must be accepted in the BCR and independently reviewed before broader use. No prior PASS is relabeled and no full VAL gate is claimed.
