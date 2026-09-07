# Single-zone inventory contracts 1.0

All public values are frozen and detach caller-owned vectors. JSON exports have
schema_version="1.0" and return detached copies. Species order is
isooctane,O2,N2,CO2,H2O; provenance order is F0,F1,R,X. These are separate ledgers.

VolumeInventory(species_mass, internal_energy, tracer_mass) stores five chemical
masses and four origin masses in kg, and total formation-inclusive internal
energy in J. A negative numeric energy is valid. Nonnegative masses, positive
total mass and agreeing chemical/origin totals are checked. An empty two-zone
birth is owned by S12; it is not synthesized here.

state(inventory, StageVolume, ThermoModel) returns VolumeState, binding the
unchanged inventory, geometry, recovered NASA state, origin fractions and
fraction roundoff record. TS-004 permits dividing derived fractions by their
sum only when the sum discrepancy is within 256 machine epsilons. Every such
operation is recorded; stored masses and energy are never changed. NASA errors
become INVENTORY_INADMISSIBLE with their original cause code retained.

StageVolume(volume, dV_dt, time, stage_id, volume_id) carries m3, m3/s and s.
StageVolume.from_geometry(GeometryModel, theta, omega, time=..., stage_id=...,
volume_id=..., kind="cylinder"|"crankcase") consumes S02 stage volume and its
angle derivative, multiplying by the supplied rad/s speed once.
pressure_work(VolumeState) creates StageWork from the recovered same-stage
pressure and geometry. Work is p*dV_dt, positive out of the gas, in W.
Direct StageWork(StagePressure, StageVolume) construction checks matching
volume ID, stage ID and exact time; pressures in Pa remain explicitly staged.

InventoryIncrement stores signed extensive kg/J values. InventoryRate
stores signed kg/s/W values and separate transfer energy, heat and pressure work.
Its total energy rate must equal transfer+heat-work. No heat or moving work is
hidden inside an interface transfer. rate.integrated(dt) explicitly converts
to an extensive increment over positive dt. apply_increment(inventory,
increment) constructs a new inventory, rejecting a rate argument or a depleted
constituent. It does not perform an EOS recovery without geometry; callers must
check state on trial inventories before accepting a step.

pair_transfer(id, source_id, receiver_id, stage_id, time_interval, stage_time,
to_receiver) evaluates no physical flux: it takes an already shared extensive
increment and creates source/receiver copies by exact sign reversal. The signed
incoming energy represents transported total enthalpy, including formation; its
numeric sign need not match the direction of mass transfer. Each TransferLedger
contains endpoint IDs, integration interval in seconds, stage ID/time and the
increment with ordering, units and positive-into-volume convention. The stage
time must be an interval endpoint, as required by the two common SSPRK2 stages.
Use distinct transfer IDs for distinct stage contributions.

validate_transfer_pairs(records) requires exactly two copies per ID, identical
stage/time/interval metadata, distinct source/receiver endpoints and exact
componentwise opposite extensive changes. balance_rates(records, heat,
p_dV, volume_id=...) requires all pairs and consistent common-stage metadata,
selects that volume's signed copies, and explicitly divides each extensive
increment by its interval duration to recover the supplied stage-equivalent
rate. A stage ledger must contain dt times its stage flux; an already combined
dt*(F0+F1)/2 accepted-step ledger must be applied as an increment, not fed back
as a stage flux. Rate and extensive types prevent accidental interchange.

Stable failures are VOLUME_NONPOSITIVE, INVENTORY_INADMISSIBLE and
TRANSFER_LEDGER_MISMATCH, using ValueContractError(component="volumes")
with paths and evidence. No clipping, seed mass, energy offset, two-zone
closure, rollback orchestrator or constant-gamma production EOS is supplied.

VAL-002 explicitly exercises the constant-gamma mathematical limit in its owned
validation adapter. It uses these production inventory/work/RHS primitives and
the frozen SSPRK2 tableau, with an independently generated Decimal80 analytic
isentrope qualified against Decimal60. The production state API continues to
require the accepted NASA ThermoModel. This is numerical verification; it
supplies no experimental or predictive validation.
