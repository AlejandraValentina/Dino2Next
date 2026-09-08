# Bounded exact overlap search optimization

Owner /root/s03_runtime_builder. Only new fast_overlap.py, test_fast_overlap.py and fast-overlap pilot/evidence files are owned. Frozen prototype.py and hybrid.py remain untouched. Baseline source SHA c2f9d81ce57a8cae741839b5522185e10485c7cabe1070a935500a13387d3eee.

Replace exhaustive target enumeration with two monotone indices over ordered disjoint donor and target partitions. Retain original donor order, ascending target order, min/max expressions, final-target remainder rule, amount arithmetic, accumulation and diagnostics. Experimental subclass compiles the original method with only this enumeration changed, and checks the source hash before doing so. No production integration or method change.

Checks: random/adversarial target lists bitwise, actual NASA remaps and records old/new for moved edges, labels, thin material slabs; timing reorganize only at N24/200/800/1600. No time integration, commits or numeric acceptance assertion.
