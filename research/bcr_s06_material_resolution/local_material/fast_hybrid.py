"""Reviewed exact overlap search composed with the frozen hybrid prototype."""
from hashlib import sha256
from pathlib import Path
from prototype import LocalSolver
from hybrid import HybridSolver
from fast_overlap import experimental_solver

HERE=Path(__file__).resolve().parent
assert sha256((HERE/'fast_overlap.py').read_bytes()).hexdigest()=='3a7a9f5f76d8f7eec0ea35589c6b749836b9e0e7107233231a0bdf66e517dd28'


class FastHybridSolver(HybridSolver):
    # This function retains baseline globals but all self.method calls dispatch
    # through FastHybridSolver's MRO, including recovery and transaction state.
    reorganize=experimental_solver(LocalSolver).reorganize
