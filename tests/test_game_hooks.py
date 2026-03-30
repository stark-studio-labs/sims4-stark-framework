"""Tests for game_hooks event definitions and import safety.

The actual hooks require the game's Python runtime and cannot be applied
in a test environment.  These tests verify:
  1. Event classes are importable and constructable
  2. Events integrate correctly with the EventBus
  3. Importing hook modules doesn't crash outside the game
"""

import pytest
from dataclasses import dataclass

from stark_framework.core.events import EventBus, Event


@pytest.fixture(autouse=True)
def clean_bus():
    EventBus.clear()
    yield
    EventBus.clear()


# ── Sim Hook Events ─────────────────────────────────────────────────────

class TestSimHookEvents:
    def test_sim_age_changed_event(self):
        from stark_framework.game_hooks.sim_hooks import SimAgeChangedEvent

        received = []

        @EventBus.on(SimAgeChangedEvent)
        def handler(event):
            received.append(event)

        event = SimAgeChangedEvent(sim_id=42, old_age="CHILD", new_age="TEEN", is_human=True)
        EventBus.publish(event)

        assert len(received) == 1
        assert received[0].sim_id == 42
        assert received[0].old_age == "CHILD"
        assert received[0].new_age == "TEEN"

    def test_sim_spawned_event(self):
        from stark_framework.game_hooks.sim_hooks import SimSpawnedEvent

        received = []

        @EventBus.on(SimSpawnedEvent)
        def handler(event):
            received.append(event.sim_id)

        EventBus.publish(SimSpawnedEvent(sim_id=99))
        assert received == [99]

    def test_sim_despawned_event(self):
        from stark_framework.game_hooks.sim_hooks import SimDespawnedEvent

        received = []

        @EventBus.on(SimDespawnedEvent)
        def handler(event):
            received.append(event.sim_id)

        EventBus.publish(SimDespawnedEvent(sim_id=7))
        assert received == [7]

    def test_sim_death_event_cancellable(self):
        from stark_framework.game_hooks.sim_hooks import SimDeathEvent

        @EventBus.on(SimDeathEvent)
        def save_sim(event):
            event.cancel()

        event = SimDeathEvent(sim_id=42, cause="fire")
        result = EventBus.publish(event)
        assert result.cancelled is True

    def test_baby_created_event(self):
        from stark_framework.game_hooks.sim_hooks import BabyCreatedEvent

        received = []

        @EventBus.on(BabyCreatedEvent)
        def handler(event):
            received.append((event.baby_sim_id, event.parent_a_id, event.parent_b_id))

        EventBus.publish(BabyCreatedEvent(baby_sim_id=100, parent_a_id=1, parent_b_id=2))
        assert received == [(100, 1, 2)]


# ── Zone Hook Events ────────────────────────────────────────────────────

class TestZoneHookEvents:
    def test_zone_spin_up_event(self):
        from stark_framework.game_hooks.zone_hooks import ZoneSpinUpEvent

        received = []

        @EventBus.on(ZoneSpinUpEvent)
        def handler(event):
            received.append(event.zone_id)

        EventBus.publish(ZoneSpinUpEvent(zone_id=12345))
        assert received == [12345]

    def test_zone_loading_finished_event(self):
        from stark_framework.game_hooks.zone_hooks import ZoneLoadingFinishedEvent

        received = []

        @EventBus.on(ZoneLoadingFinishedEvent)
        def handler(event):
            received.append(event.zone_id)

        EventBus.publish(ZoneLoadingFinishedEvent(zone_id=999))
        assert received == [999]

    def test_zone_cleanup_event(self):
        from stark_framework.game_hooks.zone_hooks import ZoneCleanupEvent

        received = []

        @EventBus.on(ZoneCleanupEvent)
        def handler(event):
            received.append(event.zone_id)

        EventBus.publish(ZoneCleanupEvent(zone_id=555))
        assert received == [555]


# ── Instance Hook Events ────────────────────────────────────────────────

class TestInstanceHookEvents:
    def test_tuning_loaded_event(self):
        from stark_framework.game_hooks.instance_hooks import TuningLoadedEvent

        received = []

        @EventBus.on(TuningLoadedEvent)
        def handler(event):
            received.append(event.manager_type)

        EventBus.publish(TuningLoadedEvent(
            manager_type="TRAIT",
            tuning_classes={"a": 1, "b": 2},
            instance_manager=None,
        ))
        assert received == ["TRAIT"]

    def test_tuning_loaded_mutable_classes(self):
        from stark_framework.game_hooks.instance_hooks import TuningLoadedEvent

        @EventBus.on(TuningLoadedEvent)
        def mutate(event):
            event.tuning_classes["injected"] = True

        classes = {"original": 1}
        event = TuningLoadedEvent(manager_type="OBJECT", tuning_classes=classes)
        EventBus.publish(event)

        assert "injected" in event.tuning_classes


# ── Funds Hook Events ───────────────────────────────────────────────────

class TestFundsHookEvents:
    def test_funds_changed_event(self):
        from stark_framework.game_hooks.funds_hooks import FundsChangedEvent

        received = []

        @EventBus.on(FundsChangedEvent)
        def handler(event):
            received.append(event.amount)

        EventBus.publish(FundsChangedEvent(
            household_id=1, amount=500, reason=None, sim_id=42,
        ))
        assert received == [500]

    def test_funds_event_cancellable(self):
        from stark_framework.game_hooks.funds_hooks import FundsChangedEvent

        @EventBus.on(FundsChangedEvent)
        def block(event):
            if event.amount > 1000:
                event.cancel()

        event = FundsChangedEvent(household_id=1, amount=5000, reason=None)
        result = EventBus.publish(event)
        assert result.cancelled is True

    def test_funds_event_amount_modifiable(self):
        from stark_framework.game_hooks.funds_hooks import FundsChangedEvent

        @EventBus.on(FundsChangedEvent)
        def double_pay(event):
            event.amount *= 2

        event = FundsChangedEvent(household_id=1, amount=100, reason=None)
        EventBus.publish(event)
        assert event.amount == 200


# ── Import Safety ───────────────────────────────────────────────────────

class TestImportSafety:
    """Importing hook modules outside the game must not raise."""

    def test_import_sim_hooks(self):
        import stark_framework.game_hooks.sim_hooks  # noqa: F401

    def test_import_zone_hooks(self):
        import stark_framework.game_hooks.zone_hooks  # noqa: F401

    def test_import_instance_hooks(self):
        import stark_framework.game_hooks.instance_hooks  # noqa: F401

    def test_import_funds_hooks(self):
        import stark_framework.game_hooks.funds_hooks  # noqa: F401

    def test_import_package(self):
        import stark_framework.game_hooks  # noqa: F401
