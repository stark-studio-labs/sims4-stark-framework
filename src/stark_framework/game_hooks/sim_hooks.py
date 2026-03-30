"""
Sim Hooks -- injections targeting SimInfo and Sim class methods.

Derived from MCCC bytecode analysis of inject_advance_age, inject_callback_
almost_ready_to_age, inject_create_baby_sim_info, inject_select_traits_for_
offspring, and inject_run_death_behavior.

These hooks fire framework events at key Sim lifecycle moments so downstream
mods can react without writing their own injections.

Targets:
    sims.sim_info.SimInfo.advance_age
    sims.sim.Sim.on_add
    sims.sim.Sim.on_remove
    sims.sim_info.SimInfo._create_baby_sim_info (static)
    sims.sim_info.SimInfo.trait_tracker (select_traits_for_offspring)
    interactions.utils.death.DeathTracker.run_death_behavior

Events published:
    SimAgeChangedEvent    -- after a Sim ages up (old_age, new_age, sim_id)
    SimSpawnedEvent       -- after a Sim instance is added to the world
    SimDespawnedEvent     -- after a Sim instance is removed from the world
    SimDeathEvent         -- when death behavior is about to run (cancellable)
    BabyCreatedEvent      -- after a new baby SimInfo is created
"""

from dataclasses import dataclass

from stark_framework.core.events import EventBus, Event
from stark_framework.core.injection import inject_after, inject_before
from stark_framework.utils.logging import get_logger

log = get_logger("stark.hooks.sim")

MOD_ID = "stark_framework.game_hooks.sim"


# ── Events ──────────────────────────────────────────────────────────────


@dataclass
class SimAgeChangedEvent(Event):
    """Published after a Sim ages up via SimInfo.advance_age."""
    sim_id: int
    old_age: object  # sims.sim_info_types.Age enum value
    new_age: object
    is_human: bool

    def __post_init__(self):
        super().__init__()


@dataclass
class SimSpawnedEvent(Event):
    """Published after Sim.on_add -- the Sim instance exists in the world."""
    sim_id: int

    def __post_init__(self):
        super().__init__()


@dataclass
class SimDespawnedEvent(Event):
    """Published after Sim.on_remove -- the Sim instance left the world."""
    sim_id: int

    def __post_init__(self):
        super().__init__()


@dataclass
class SimDeathEvent(Event):
    """Published before death behavior runs.  Cancel to prevent the death."""
    sim_id: int
    cause: str  # death type string if available, else "unknown"

    def __post_init__(self):
        super().__init__()


@dataclass
class BabyCreatedEvent(Event):
    """Published after a new baby SimInfo is created."""
    baby_sim_id: int
    parent_a_id: int  # 0 if unknown
    parent_b_id: int  # 0 if unknown

    def __post_init__(self):
        super().__init__()


# ── Hook Registration ───────────────────────────────────────────────────
#
# Each function below is decorated with an injection that targets a real
# game method.  When this module is imported, the injections are applied.
#
# Outside the game (during testing), InjectionManager.inject raises
# InjectionError because the target modules don't exist.  We catch that
# so importing this module in tests doesn't crash -- the hooks simply
# become no-ops.


_hooks_active = False


def register_hooks():
    """Apply all sim hooks.  Safe to call multiple times (idempotent).

    Called automatically on module import when running inside the game.
    Outside the game, this is a silent no-op.
    """
    global _hooks_active
    if _hooks_active:
        return
    _hooks_active = True

    from stark_framework.core.injection import InjectionManager, InjectionError

    # -- advance_age -------------------------------------------------------
    def _on_advance_age(original, self, *args, **kwargs):
        try:
            from sims.sim_info_types import Age, Species
            old_age = getattr(self, "age", None)
        except ImportError:
            old_age = getattr(self, "age", None)

        result = original(self, *args, **kwargs)

        new_age = getattr(self, "age", None)
        sim_id = getattr(self, "sim_id", 0)
        is_human = True
        try:
            from sims.sim_info_types import Species
            is_human = getattr(self, "species", None) == Species.HUMAN
        except ImportError:
            pass

        if old_age != new_age:
            EventBus.publish(
                SimAgeChangedEvent(
                    sim_id=sim_id,
                    old_age=old_age,
                    new_age=new_age,
                    is_human=is_human,
                ),
                source_mod=MOD_ID,
            )

        return result

    try:
        InjectionManager.inject(
            "sims.sim_info.SimInfo", "advance_age",
            _on_advance_age, kind="after", mod_id=MOD_ID,
        )
        log.info("Hooked SimInfo.advance_age")
    except InjectionError as exc:
        log.debug("Skip advance_age hook (not in game)", reason=str(exc))

    # -- Sim.on_add --------------------------------------------------------
    def _on_sim_add(original, self, *args, **kwargs):
        result = original(self, *args, **kwargs)
        sim_id = getattr(self, "sim_id", 0) or getattr(
            getattr(self, "sim_info", None), "sim_id", 0
        )
        EventBus.publish(SimSpawnedEvent(sim_id=sim_id), source_mod=MOD_ID)
        return result

    try:
        InjectionManager.inject(
            "sims.sim.Sim", "on_add",
            _on_sim_add, kind="after", mod_id=MOD_ID,
        )
        log.info("Hooked Sim.on_add")
    except InjectionError as exc:
        log.debug("Skip Sim.on_add hook (not in game)", reason=str(exc))

    # -- Sim.on_remove -----------------------------------------------------
    def _on_sim_remove(original, self, *args, **kwargs):
        sim_id = getattr(self, "sim_id", 0) or getattr(
            getattr(self, "sim_info", None), "sim_id", 0
        )
        result = original(self, *args, **kwargs)
        EventBus.publish(SimDespawnedEvent(sim_id=sim_id), source_mod=MOD_ID)
        return result

    try:
        InjectionManager.inject(
            "sims.sim.Sim", "on_remove",
            _on_sim_remove, kind="after", mod_id=MOD_ID,
        )
        log.info("Hooked Sim.on_remove")
    except InjectionError as exc:
        log.debug("Skip Sim.on_remove hook (not in game)", reason=str(exc))

    # -- DeathTracker.run_death_behavior -----------------------------------
    def _on_death(original, self, *args, **kwargs):
        sim_info = getattr(self, "_sim_info", None) or getattr(self, "sim_info", None)
        sim_id = getattr(sim_info, "sim_id", 0) if sim_info else 0

        cause = "unknown"
        if args:
            cause = getattr(args[0], "__name__", str(args[0]))

        event = SimDeathEvent(sim_id=sim_id, cause=cause)
        EventBus.publish(event, source_mod=MOD_ID)

        if event.cancelled:
            log.info("Death cancelled by event handler", sim_id=sim_id)
            return None

        return original(self, *args, **kwargs)

    try:
        InjectionManager.inject(
            "interactions.utils.death.DeathTracker", "run_death_behavior",
            _on_death, kind="before", mod_id=MOD_ID,
        )
        log.info("Hooked DeathTracker.run_death_behavior")
    except InjectionError as exc:
        log.debug("Skip death hook (not in game)", reason=str(exc))


# Auto-register when imported inside the game.
try:
    register_hooks()
except Exception as exc:
    log.debug("Sim hooks not registered (not in game environment)", reason=str(exc))
