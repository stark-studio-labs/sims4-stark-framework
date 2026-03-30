"""
Instance Hooks -- injection for InstanceManager.load_data_into_class_instances.

This is the single most important hook point in the game.  MCCC's entire
tuning-mutation architecture routes through it.  When the game loads XML
tuning for a given resource type (TRAIT, BUFF, CAREER, OBJECT, etc.), this
method is called for each InstanceManager.  Hooking it lets a mod:

  - Inspect or modify tuning classes as they load
  - Inject affordances into objects
  - Patch career / population / pregnancy tuning at load time
  - Register custom tuning without XML overrides

The hook fires a TuningLoadedEvent with the manager type and the dict of
loaded tuning classes.  Subscribers can mutate tuning_classes in-place.

Targets:
    resources.instance_manager.InstanceManager.load_data_into_class_instances

Events published:
    TuningLoadedEvent  -- after an InstanceManager finishes loading tuning
"""

from dataclasses import dataclass, field

from stark_framework.core.events import EventBus, Event
from stark_framework.core.injection import InjectionManager, InjectionError
from stark_framework.utils.logging import get_logger

log = get_logger("stark.hooks.instance")

MOD_ID = "stark_framework.game_hooks.instance"


# ── Events ──────────────────────────────────────────────────────────────


@dataclass
class TuningLoadedEvent(Event):
    """Published after InstanceManager.load_data_into_class_instances.

    Attributes:
        manager_type: The resource type enum (e.g. Types.OBJECT, Types.CAREER).
                      Comparison: ``event.manager_type == Types.CAREER``
        tuning_classes: Dict of {tuning_id: tuning_class}.  Mods may mutate
                        this dict to inject or patch tuning.
        instance_manager: The InstanceManager instance itself.
    """
    manager_type: object  # sims4.resources.Types enum value
    tuning_classes: dict = field(default_factory=dict)
    instance_manager: object = None

    def __post_init__(self):
        super().__init__()


# ── Hook Registration ───────────────────────────────────────────────────

_hooks_active = False


def register_hooks():
    """Apply the InstanceManager hook.  Safe to call multiple times."""
    global _hooks_active
    if _hooks_active:
        return
    _hooks_active = True

    def _on_load_data(original, self, *args, **kwargs):
        # Let the game load tuning first
        result = original(self, *args, **kwargs)

        manager_type = getattr(self, "TYPE", None)
        tuned_classes = {}
        try:
            tuned_classes = dict(getattr(self, "_tuned_classes", {}) or {})
        except Exception:
            pass

        EventBus.publish(
            TuningLoadedEvent(
                manager_type=manager_type,
                tuning_classes=tuned_classes,
                instance_manager=self,
            ),
            source_mod=MOD_ID,
        )

        return result

    try:
        InjectionManager.inject(
            "resources.instance_manager.InstanceManager",
            "load_data_into_class_instances",
            _on_load_data,
            kind="after",
            mod_id=MOD_ID,
        )
        log.info("Hooked InstanceManager.load_data_into_class_instances")
    except InjectionError as exc:
        log.debug("Skip instance_manager hook (not in game)", reason=str(exc))


try:
    register_hooks()
except Exception as exc:
    log.debug("Instance hooks not registered (not in game environment)", reason=str(exc))
