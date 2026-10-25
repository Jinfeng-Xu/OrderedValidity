"""Ordered-validity evaluation for finite benchmark releases."""

from .adapters import Candidate, candidates_to_positions, load_candidate_csv
from .core import evaluate, write_evaluation
from .protocol import Protocol, load_protocol
from .schema import Position, ValidationError, load_positions, load_target_manifest

__all__ = [
    "Candidate",
    "Protocol",
    "Position",
    "ValidationError",
    "candidates_to_positions",
    "evaluate",
    "load_candidate_csv",
    "load_positions",
    "load_protocol",
    "load_target_manifest",
    "write_evaluation",
]

__version__ = "1.0.0"

