"""Normalization pipeline configuration."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DeduplicationThresholds:
    """Configurable fuzzy duplicate confidence thresholds."""

    exact_threshold: float = 0.98
    likely_threshold: float = 0.85
    possible_threshold: float = 0.60
    cross_source_max_confidence: float = 0.75


CURRENT_NORMALIZATION_VERSION = 1

DEFAULT_THRESHOLDS = DeduplicationThresholds()
