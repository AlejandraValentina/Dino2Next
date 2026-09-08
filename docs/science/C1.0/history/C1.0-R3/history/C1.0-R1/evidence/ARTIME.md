# Timestep and admissibility closure — derivation in progress

BLK-002 remains pending the coupled-reference gate and executed combined-source campaign. The following derivation is preparatory, not a prematurely selected timestep recipe.

For a conservative cell inventory (M,P,E,Mk), thermal admissibility cannot mean E−P²/(2M)>0: NASA formation energies may be negative. At fixed contractual Tmin, the correct lower thermal margin is

Dmin=E−P²/(2M)−ΣMk ek(Tmin).

For M>0 and Mk≥0, Dmin≥0 is equivalent to T≥Tmin because mixture cv>0. It is a concave function of conservative inventory, so its superlevel set is convex. The corresponding upper-temperature condition Dmax=ΣMk ek(Tmax)−E+P²/(2M)≥0 is not generally a convex admissible set. Consequently, SSP convex combinations alone do not prove the GEN1 upper temperature bound. Every relevant Euler stage and final combination must be checked with the actual EOS/domain. Pressure bounds and gas-phase limits must also be checked; they are not implied by positive density.

The SSPRK2 representation is y1=y+dt L(t,y), y2FE=y1+dt L(t+dt,y1), ynext=(y+y2FE)/2. The final recipe must check all three states, not merely y1 and ynext. Rejection restores the complete accepted inventory, ledgers, events and characterization state before any retry.

For each nonnegative species/tracer inventory with net derivative dM<0, the forward-Euler depletion time is M/(−dM). Summed outgoing donor contributions provide a stronger no-depletion diagnostic than net cancellation by inflow. A zero inventory with negative derivative is an inadmissible RHS, not something that can be repaired with a seed mass. Exact birth limits are required for an empty scavenging zone.

For W2 alone, u'=-b u|u|, b=λw/2. A forward-Euler source stage does not reverse the velocity if dt b|u|≤1. Its total energy remains fixed; the corresponding change in kinetic energy becomes internal energy. Distributed/local friction contributes to the same opposing-force budget. A combined-source upper-T check is still required, even when each individual force is passive. Heat and chemical composition changes require thermal margins computed with formation-aware EOS, rather than an arbitrary positive-energy floor.

References: [Gottlieb, Shu and Tadmor, 2001](https://drum.lib.umd.edu/bitstreams/faa96f40-0fbb-4af0-84a3-5e3b80c908df/download) establishes the conditional SSP inheritance of forward-Euler properties. [Zhang and Shu, Euler with sources](https://www.math.purdue.edu/~zhan1966/research/paper/euler-source.pdf) motivates explicit admissibility/source treatment; its e>0 iff p>0 assumption must not be transplanted to formation-inclusive NASA energy. The Tmin-shifted mixture inequality above is derived here for the selected EOS, not claimed as a verbatim theorem of that paper.

## Executed thermal-bound counterexample (AR019; downstream contract still pending)

The upper temperature bound is not a convex invariant set. Two admissible FE states in the phi.6 endpoint contact yielded a final SSPRK2 temperature2200.0000103732764K. Therefore the final conservative combination must be checked explicitly, in addition to both FE states. The research joint-flux guard now includes that actual combination through an `anchor` state; it does not remove the excess energy. Roundoff tests use the inherited64eps*2200K comparison consistently and leave state bytes unchanged.

The six operational400/1800K phi.6/.8 contacts complete in both directions without retries. Some300/2200 and301/2199K contacts exhaust the provisional global retry policy; these are failed runs with no accepted out-of-domain state, not evidence that the EOS domain has changed. The campaign must adjudicate the numerical failure envelope explicitly. A reference or method that only prevents negative density does not automatically preserve a finite upper NASA temperature limit.
