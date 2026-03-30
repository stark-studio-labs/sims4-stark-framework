"""Tests for the typed event bus -- the centerpiece of Stark Framework."""

import pytest
from dataclasses import dataclass
from stark_framework.core.events import EventBus, Event


# ── Test Event Types ─────────────────────────────────────────────────

@dataclass
class SimDiedEvent(Event):
    sim_id: int
    cause: str

    def __post_init__(self):
        super().__init__()


@dataclass
class BuffAppliedEvent(Event):
    sim_id: int
    buff_name: str

    def __post_init__(self):
        super().__init__()


# ── Fixtures ─────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clean_bus():
    """Reset the event bus between tests."""
    EventBus.clear()
    EventBus.enable_logging(False)
    yield
    EventBus.clear()


# ── Basic Pub/Sub ────────────────────────────────────────────────────

class TestBasicPubSub:
    def test_subscribe_and_publish(self):
        received = []

        @EventBus.on(SimDiedEvent)
        def handler(event):
            received.append(event)

        EventBus.publish(SimDiedEvent(sim_id=42, cause="fire"))

        assert len(received) == 1
        assert received[0].sim_id == 42
        assert received[0].cause == "fire"

    def test_multiple_subscribers(self):
        results = []

        @EventBus.on(SimDiedEvent)
        def handler_a(event):
            results.append("a")

        @EventBus.on(SimDiedEvent)
        def handler_b(event):
            results.append("b")

        EventBus.publish(SimDiedEvent(sim_id=1, cause="old_age"))

        assert results == ["a", "b"]

    def test_different_event_types_dont_cross(self):
        died_count = []
        buff_count = []

        @EventBus.on(SimDiedEvent)
        def on_death(event):
            died_count.append(1)

        @EventBus.on(BuffAppliedEvent)
        def on_buff(event):
            buff_count.append(1)

        EventBus.publish(SimDiedEvent(sim_id=1, cause="fire"))

        assert len(died_count) == 1
        assert len(buff_count) == 0

    def test_publish_with_no_subscribers(self):
        # Should not raise
        result = EventBus.publish(SimDiedEvent(sim_id=1, cause="fire"))
        assert result.sim_id == 1

    def test_publish_returns_event(self):
        result = EventBus.publish(SimDiedEvent(sim_id=99, cause="drowning"))
        assert isinstance(result, SimDiedEvent)
        assert result.sim_id == 99


# ── Priority Ordering ────────────────────────────────────────────────

class TestPriority:
    def test_lower_priority_runs_first(self):
        order = []

        @EventBus.on(SimDiedEvent, priority=50)
        def medium(event):
            order.append("medium")

        @EventBus.on(SimDiedEvent, priority=10)
        def early(event):
            order.append("early")

        @EventBus.on(SimDiedEvent, priority=200)
        def late(event):
            order.append("late")

        EventBus.publish(SimDiedEvent(sim_id=1, cause="test"))

        assert order == ["early", "medium", "late"]

    def test_default_priority_is_100(self):
        subs_before = EventBus.get_subscribers(SimDiedEvent)
        assert len(subs_before) == 0

        @EventBus.on(SimDiedEvent)
        def handler(event):
            pass

        subs = EventBus.get_subscribers(SimDiedEvent)
        assert len(subs) == 1
        assert subs[0].priority == 100


# ── Event Cancellation ───────────────────────────────────────────────

class TestCancellation:
    def test_cancel_stops_propagation(self):
        order = []

        @EventBus.on(SimDiedEvent, priority=10)
        def first(event):
            order.append("first")
            event.cancel()

        @EventBus.on(SimDiedEvent, priority=20)
        def second(event):
            order.append("second")

        result = EventBus.publish(SimDiedEvent(sim_id=1, cause="test"))

        assert order == ["first"]
        assert result.cancelled is True

    def test_uncancelled_event(self):
        @EventBus.on(SimDiedEvent)
        def handler(event):
            pass

        result = EventBus.publish(SimDiedEvent(sim_id=1, cause="test"))
        assert result.cancelled is False


# ── Unsubscribe ──────────────────────────────────────────────────────

class TestUnsubscribe:
    def test_unsubscribe_handler(self):
        received = []

        @EventBus.on(SimDiedEvent)
        def handler(event):
            received.append(1)

        EventBus.publish(SimDiedEvent(sim_id=1, cause="test"))
        assert len(received) == 1

        EventBus.unsubscribe(SimDiedEvent, handler)
        EventBus.publish(SimDiedEvent(sim_id=2, cause="test"))
        assert len(received) == 1  # No new events

    def test_unsubscribe_returns_false_for_unknown(self):
        def not_subscribed(event):
            pass

        result = EventBus.unsubscribe(SimDiedEvent, not_subscribed)
        assert result is False


# ── Programmatic Subscribe ───────────────────────────────────────────

class TestProgrammaticSubscribe:
    def test_subscribe_function(self):
        received = []

        def handler(event):
            received.append(event.sim_id)

        EventBus.subscribe(SimDiedEvent, handler, priority=50)
        EventBus.publish(SimDiedEvent(sim_id=7, cause="test"))

        assert received == [7]

    def test_subscribe_rejects_non_event_type(self):
        with pytest.raises(TypeError, match="Event subclass"):
            EventBus.subscribe(str, lambda e: None)

    def test_publish_rejects_non_event_instance(self):
        with pytest.raises(TypeError, match="Event instance"):
            EventBus.publish("not an event")


# ── Source Mod Tracking ──────────────────────────────────────────────

class TestSourceMod:
    def test_source_mod_tracking(self):
        received_source = []

        @EventBus.on(SimDiedEvent)
        def handler(event):
            received_source.append(event.source_mod)

        EventBus.publish(
            SimDiedEvent(sim_id=1, cause="test"),
            source_mod="alice_vampire_mod",
        )

        assert received_source == ["alice_vampire_mod"]


# ── Event Logging ────────────────────────────────────────────────────

class TestEventLogging:
    def test_logging_disabled_by_default(self):
        EventBus.publish(SimDiedEvent(sim_id=1, cause="test"))
        assert EventBus.get_event_log() == []

    def test_logging_captures_events(self):
        EventBus.enable_logging(True)
        EventBus.publish(SimDiedEvent(sim_id=1, cause="fire"))
        EventBus.publish(BuffAppliedEvent(sim_id=2, buff_name="happy"))

        log = EventBus.get_event_log()
        assert len(log) == 2
        assert isinstance(log[0], SimDiedEvent)
        assert isinstance(log[1], BuffAppliedEvent)

    def test_disable_logging_clears_log(self):
        EventBus.enable_logging(True)
        EventBus.publish(SimDiedEvent(sim_id=1, cause="test"))
        assert len(EventBus.get_event_log()) == 1

        EventBus.enable_logging(False)
        assert EventBus.get_event_log() == []


# ── Introspection ────────────────────────────────────────────────────

class TestIntrospection:
    def test_get_subscribers(self):
        @EventBus.on(SimDiedEvent, mod_id="mod_a")
        def handler_a(event):
            pass

        @EventBus.on(SimDiedEvent, mod_id="mod_b")
        def handler_b(event):
            pass

        subs = EventBus.get_subscribers(SimDiedEvent)
        assert len(subs) == 2
        assert subs[0].mod_id == "mod_a"
        assert subs[1].mod_id == "mod_b"

    def test_get_subscribers_empty(self):
        subs = EventBus.get_subscribers(BuffAppliedEvent)
        assert subs == []

    def test_clear_specific_event(self):
        @EventBus.on(SimDiedEvent)
        def handler(event):
            pass

        @EventBus.on(BuffAppliedEvent)
        def other_handler(event):
            pass

        EventBus.clear(SimDiedEvent)

        assert EventBus.get_subscribers(SimDiedEvent) == []
        assert len(EventBus.get_subscribers(BuffAppliedEvent)) == 1


# ── Error Handling ───────────────────────────────────────────────────

class TestErrorHandling:
    def test_handler_exception_doesnt_crash_bus(self):
        """A failing handler should not prevent other handlers from running."""
        results = []

        @EventBus.on(SimDiedEvent, priority=10, mod_id="bad_mod")
        def bad_handler(event):
            raise ValueError("Something broke")

        @EventBus.on(SimDiedEvent, priority=20)
        def good_handler(event):
            results.append("ok")

        # Should not raise -- error is caught and recorded
        EventBus.publish(SimDiedEvent(sim_id=1, cause="test"))

        assert results == ["ok"]
