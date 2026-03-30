"""Type stubs for interactions.* -- interaction and death systems."""

from typing import Any, Optional


# ── interactions.utils.death ────────────────────────────────────────────

class DeathTracker:
    """Tracks death state for a Sim."""
    _sim_info: Any  # SimInfo

    def run_death_behavior(self, death_type: Any = ...) -> None: ...


class DeathType:
    """Common death type constants (tuning-defined, not a real enum)."""
    DEATH_FIRE: int
    DEATH_ELECTROCUTION: int
    DEATH_DROWNING: int
    DEATH_HUNGER: int
    DEATH_OLD_AGE: int
    DEATH_OVEREXERTION: int
    DEATH_COWPLANT: int
    DEATH_LAUGHTER: int
    DEATH_EMBARRASSMENT: int
    DEATH_ANGER: int


# ── interactions.base ───────────────────────────────────────────────────

class SuperInteraction:
    """Base class for all super interactions (pie-menu items)."""
    sim: Any
    target: Any
    guid64: int

    def _run_interaction_gen(self, timeline: Any) -> Any: ...
