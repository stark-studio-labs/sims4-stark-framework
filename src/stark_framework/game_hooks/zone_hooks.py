"""
Zone Hooks -- injections targeting Zone lifecycle methods.

Derived from MCCC bytecode analysis of inject_load_options, inject_start_
services, and the zone spin-up / loading-screen callbacks.

Targets:
    zone.Zone.do_zone_spin_up
    zone.Zone.on_loading_screen_animation_finished
    zone.Zone.on_cleanup_zone_objects

Events published:
    ZoneSpinUpEvent               -- zone is spinning up (lot loading)
    ZoneLoadingFinishedEvent      -- loading screen dismissed, lot playable
    ZoneCleanupEvent              -- zone objects being cleaned up (travel/quit)
"""

from dataclasses import dataclass

from stark_framework.core.events import EventBus, Event
from stark_framework.core.injection import InjectionManager, InjectionError
from stark_framework.utils.logging import get_logger

log = get_logger("stark.hooks.zone")

MOD_ID = "stark_framework.game_hooks.zone"


# ── Events ──────────────────────────────────────────────────────────────


@dataclass
class ZoneSpinUpEvent(Event):
    """Published when Zone.do_zone_spin_up runs -- the lot is loading."""
    zone_id: int

    def __post_init__(self):
        super().__init__()


@dataclass
class ZoneLoadingFinishedEvent(Event):
    """Published when on_loading_screen_animation_finished runs.

    At this point the lot is fully loaded and gameplay is active.  This is
    the safest place for mods to run initialization that needs game data.
    """
    zone_id: int

    def __post_init__(self):
        super().__init__()


@dataclass
class ZoneCleanupEvent(Event):
    """Published when on_cleanup_zone_objects runs -- zone teardown."""
    zone_id: int

    def __post_init__(self):
        super().__init__()


# ── Hook Registration ───────────────────────────────────────────────────

_hooks_active = False


def register_hooks():
    """Apply all zone hooks.  Safe to call multiple times."""
    global _hooks_active
    if _hooks_active:
        return
    _hooks_active = True

    # -- Zone.do_zone_spin_up ---------------------------------------------
    def _on_zone_spin_up(original, self, *args, **kwargs):
        zone_id = getattr(self, "id", 0)
        result = original(self, *args, **kwargs)
        EventBus.publish(
            ZoneSpinUpEvent(zone_id=zone_id), source_mod=MOD_ID,
        )
        return result

    try:
        InjectionManager.inject(
            "zone.Zone", "do_zone_spin_up",
            _on_zone_spin_up, kind="after", mod_id=MOD_ID,
        )
        log.info("Hooked Zone.do_zone_spin_up")
    except InjectionError as exc:
        log.debug("Skip zone_spin_up hook (not in game)", reason=str(exc))

    # -- Zone.on_loading_screen_animation_finished -------------------------
    def _on_loading_finished(original, self, *args, **kwargs):
        result = original(self, *args, **kwargs)
        zone_id = getattr(self, "id", 0)
        EventBus.publish(
            ZoneLoadingFinishedEvent(zone_id=zone_id), source_mod=MOD_ID,
        )
        return result

    try:
        InjectionManager.inject(
            "zone.Zone", "on_loading_screen_animation_finished",
            _on_loading_finished, kind="after", mod_id=MOD_ID,
        )
        log.info("Hooked Zone.on_loading_screen_animation_finished")
    except InjectionError as exc:
        log.debug("Skip loading_finished hook (not in game)", reason=str(exc))

    # -- Zone.on_cleanup_zone_objects --------------------------------------
    def _on_zone_cleanup(original, self, *args, **kwargs):
        zone_id = getattr(self, "id", 0)
        EventBus.publish(
            ZoneCleanupEvent(zone_id=zone_id), source_mod=MOD_ID,
        )
        return original(self, *args, **kwargs)

    try:
        InjectionManager.inject(
            "zone.Zone", "on_cleanup_zone_objects",
            _on_zone_cleanup, kind="before", mod_id=MOD_ID,
        )
        log.info("Hooked Zone.on_cleanup_zone_objects")
    except InjectionError as exc:
        log.debug("Skip zone_cleanup hook (not in game)", reason=str(exc))


try:
    register_hooks()
except Exception as exc:
    log.debug("Zone hooks not registered (not in game environment)", reason=str(exc))
