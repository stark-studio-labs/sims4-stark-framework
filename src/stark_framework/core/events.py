"""
Typed Event Bus -- the centerpiece of Stark Framework.

Provides a publish/subscribe event system that lets mods react to game events
without monkey-patching. Events are plain dataclasses -- type-safe, inspectable,
and composable.

Usage:
    from stark_framework.core.events import EventBus, Event
    from dataclasses import dataclass

    # Define a typed event
    @dataclass
    class SimLoadedEvent(Event):
        sim_id: int
        first_name: str
        last_name: str

    # Subscribe a handler -- decorator style
    @EventBus.on(SimLoadedEvent)
    def greet_sim(event: SimLoadedEvent):
        print(f"Welcome, {event.first_name} {event.last_name}!")

    # Subscribe with priority (lower runs first, default=100)
    @EventBus.on(SimLoadedEvent, priority=10)
    def log_sim_early(event: SimLoadedEvent):
        print(f"[EARLY] Sim {event.sim_id} loading...")

    # Subscribe programmatically
    EventBus.subscribe(SimLoadedEvent, my_handler, priority=50)

    # Publish an event -- all subscribers fire in priority order
    EventBus.publish(SimLoadedEvent(sim_id=42, first_name="Bella", last_name="Goth"))

    # Cancel further processing from a handler
    def cancel_handler(event: SimLoadedEvent):
        event.cancel()  # Remaining handlers won't fire

    # Unsubscribe
    EventBus.unsubscribe(SimLoadedEvent, greet_sim)

    # Check what's listening
    handlers = EventBus.get_subscribers(SimLoadedEvent)
"""


class Event:
    """Base class for all framework events.

    Subclass this with a dataclass to define typed events. Handlers receive
    the event instance and can inspect its fields or cancel propagation.

    Example:
        @dataclass
        class BuffAppliedEvent(Event):
            sim_id: int
            buff_name: str
            duration: float
    """

    def __init__(self):
        self._cancelled = False
        self._source_mod = None  # type: str | None

    @property
    def cancelled(self):
        """Whether a handler has cancelled this event."""
        return self._cancelled

    def cancel(self):
        """Cancel this event. Remaining handlers in the chain will not fire."""
        self._cancelled = True

    @property
    def source_mod(self):
        """The mod_id that published this event, if tracked."""
        return self._source_mod


class _Subscription:
    """Internal: a single handler subscription with priority and metadata."""

    __slots__ = ("handler", "priority", "mod_id")

    def __init__(self, handler, priority=100, mod_id=None):
        self.handler = handler
        self.priority = priority
        self.mod_id = mod_id

    def __repr__(self):
        return (
            f"Subscription({self.handler.__name__}, "
            f"priority={self.priority}, mod={self.mod_id})"
        )


class EventBus:
    """Global typed event bus. Mods subscribe to event classes and receive
    instances when those events are published.

    Thread safety: The Sims 4 is single-threaded for gameplay, so this bus
    does not use locks. If you call from a background thread, synchronize
    externally.
    """

    _subscribers = {}  # type: dict[type, list[_Subscription]]
    _event_log = []    # type: list[Event]
    _log_enabled = False

    # ── Subscribe ────────────────────────────────────────────────────

    @classmethod
    def on(cls, event_type, priority=100, mod_id=None):
        """Decorator to subscribe a handler to an event type.

        Args:
            event_type: The Event subclass to listen for.
            priority: Lower values run first. Default 100.
            mod_id: Optional mod identifier for diagnostics.

        Returns:
            The original function (unmodified).

        Example:
            @EventBus.on(SimDiedEvent, priority=10)
            def handle_death(event):
                print(event.sim_id)
        """
        def decorator(fn):
            cls.subscribe(event_type, fn, priority=priority, mod_id=mod_id)
            return fn
        return decorator

    @classmethod
    def subscribe(cls, event_type, handler, priority=100, mod_id=None):
        """Programmatically subscribe a handler to an event type.

        Args:
            event_type: The Event subclass to listen for.
            handler: Callable that accepts a single event instance.
            priority: Lower values run first. Default 100.
            mod_id: Optional mod identifier for diagnostics.
        """
        if not isinstance(event_type, type) or not issubclass(event_type, Event):
            raise TypeError(
                f"event_type must be an Event subclass, got {event_type!r}"
            )

        if event_type not in cls._subscribers:
            cls._subscribers[event_type] = []

        sub = _Subscription(handler, priority=priority, mod_id=mod_id)
        cls._subscribers[event_type].append(sub)
        cls._subscribers[event_type].sort(key=lambda s: s.priority)

    @classmethod
    def unsubscribe(cls, event_type, handler):
        """Remove a handler from an event type.

        Args:
            event_type: The Event subclass.
            handler: The function to remove.

        Returns:
            True if the handler was found and removed, False otherwise.
        """
        subs = cls._subscribers.get(event_type, [])
        for i, sub in enumerate(subs):
            if sub.handler is handler:
                subs.pop(i)
                return True
        return False

    # ── Publish ──────────────────────────────────────────────────────

    @classmethod
    def publish(cls, event, source_mod=None):
        """Publish an event to all subscribers.

        Handlers run synchronously in priority order (lowest first). If any
        handler calls event.cancel(), remaining handlers are skipped.

        Args:
            event: An Event instance.
            source_mod: Optional mod_id of the publisher.

        Returns:
            The event instance (with .cancelled reflecting final state).

        Example:
            result = EventBus.publish(SimDiedEvent(sim_id=42, cause="fire"))
            if result.cancelled:
                print("A mod prevented the death!")
        """
        if not isinstance(event, Event):
            raise TypeError(f"event must be an Event instance, got {type(event)!r}")

        if source_mod:
            event._source_mod = source_mod

        if cls._log_enabled:
            cls._event_log.append(event)

        event_type = type(event)
        subs = cls._subscribers.get(event_type, [])

        for sub in subs:
            if event.cancelled:
                break
            try:
                sub.handler(event)
            except Exception as exc:
                # Import here to avoid circular dependency at module level
                from stark_framework.core.diagnostics import Diagnostics
                Diagnostics.record_error(
                    mod_id=sub.mod_id or "unknown",
                    error=exc,
                    context=f"Handling {event_type.__name__}",
                )

        return event

    # ── Introspection ────────────────────────────────────────────────

    @classmethod
    def get_subscribers(cls, event_type):
        """Return list of subscriptions for an event type.

        Useful for diagnostics and conflict detection.
        """
        return list(cls._subscribers.get(event_type, []))

    @classmethod
    def clear(cls, event_type=None):
        """Remove all subscribers, or subscribers for a specific event type.

        Primarily for testing -- don't call this in production mods.
        """
        if event_type:
            cls._subscribers.pop(event_type, None)
        else:
            cls._subscribers.clear()

    @classmethod
    def enable_logging(cls, enabled=True):
        """Enable or disable event logging for diagnostics."""
        cls._log_enabled = enabled
        if not enabled:
            cls._event_log.clear()

    @classmethod
    def get_event_log(cls):
        """Return the event log (only populated when logging is enabled)."""
        return list(cls._event_log)
