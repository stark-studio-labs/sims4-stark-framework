"""
Game-Time Scheduler -- run tasks on the Sim clock, not wall-clock time.

The Sims 4 has its own clock system where game time passes at variable
speed (normal, fast, ultra-speed, paused).  This scheduler lets mods
register callbacks that fire at specific game-time intervals or at
fixed game-time points (e.g. midnight, noon, 6 AM).

Outside the game, the scheduler falls back to a simple tick-based system
for testing.

Usage:
    from stark_framework.core.scheduler import GameScheduler

    scheduler = GameScheduler()

    # Run at midnight every day
    scheduler.daily(hour=0, callback=run_midnight_check, label="midnight_bills")

    # Run every 60 Sim-minutes
    scheduler.interval(sim_minutes=60, callback=check_needs, label="need_check")

    # Run once at a specific game time
    scheduler.once(hour=8, minute=30, callback=morning_greeting, label="morning")

    # Cancel a scheduled task
    scheduler.cancel("midnight_bills")

    # Tick the scheduler (called from zone hooks or alarm system)
    scheduler.tick(current_hour=23, current_minute=59)
"""

from stark_framework.utils.logging import get_logger

log = get_logger("stark.core.scheduler")


class _ScheduledTask:
    """Internal representation of a scheduled task."""

    __slots__ = (
        "label", "callback", "kind", "hour", "minute",
        "interval_minutes", "last_run_day", "last_run_tick",
        "once_fired",
    )

    def __init__(self, label, callback, kind, hour=0, minute=0,
                 interval_minutes=0):
        self.label = label
        self.callback = callback
        self.kind = kind  # "daily", "interval", "once"
        self.hour = hour
        self.minute = minute
        self.interval_minutes = interval_minutes
        self.last_run_day = -1
        self.last_run_tick = -1
        self.once_fired = False


class GameScheduler:
    """Game-time aware task scheduler.

    The scheduler does not run its own loop.  It exposes a ``tick()`` method
    that must be called each game-time minute (or on zone load / hour change).
    The recommended pattern is to hook Zone.on_loading_screen_animation_finished
    and set up an in-game alarm that calls ``tick()`` each Sim-minute.
    """

    def __init__(self):
        self._tasks = {}  # label -> _ScheduledTask
        self._current_day = 0
        self._total_ticks = 0

    # ── Registration ─────────────────────────────────────────────────

    def daily(self, hour, callback, label, minute=0):
        """Schedule a task to run once per game day at a specific time.

        Args:
            hour: Hour to fire (0-23).
            callback: Callable to run (no arguments).
            label: Unique label for this task (used to cancel).
            minute: Minute to fire (0-59, default 0).
        """
        if label in self._tasks:
            log.warn("Overwriting existing task", label=label)

        self._tasks[label] = _ScheduledTask(
            label=label, callback=callback, kind="daily",
            hour=hour, minute=minute,
        )
        log.info("Daily task registered", label=label, time=f"{hour:02d}:{minute:02d}")

    def interval(self, sim_minutes, callback, label):
        """Schedule a task to run every N Sim-minutes.

        Args:
            sim_minutes: Interval in Sim-minutes.
            callback: Callable to run.
            label: Unique label.
        """
        if label in self._tasks:
            log.warn("Overwriting existing task", label=label)

        self._tasks[label] = _ScheduledTask(
            label=label, callback=callback, kind="interval",
            interval_minutes=sim_minutes,
        )
        log.info("Interval task registered", label=label, interval=sim_minutes)

    def once(self, hour, callback, label, minute=0):
        """Schedule a task to run once at the next occurrence of a time.

        The task is automatically removed after it fires.

        Args:
            hour: Hour to fire (0-23).
            callback: Callable to run.
            label: Unique label.
            minute: Minute to fire (0-59, default 0).
        """
        if label in self._tasks:
            log.warn("Overwriting existing task", label=label)

        self._tasks[label] = _ScheduledTask(
            label=label, callback=callback, kind="once",
            hour=hour, minute=minute,
        )
        log.info("Once task registered", label=label, time=f"{hour:02d}:{minute:02d}")

    def cancel(self, label):
        """Cancel a scheduled task by label.

        Args:
            label: The task label to cancel.

        Returns:
            True if the task existed and was removed, False otherwise.
        """
        if label in self._tasks:
            del self._tasks[label]
            log.info("Task cancelled", label=label)
            return True
        return False

    def list_tasks(self):
        """List all scheduled tasks.

        Returns:
            List of dicts with task metadata.
        """
        result = []
        for task in self._tasks.values():
            entry = {
                "label": task.label,
                "kind": task.kind,
            }
            if task.kind == "interval":
                entry["interval_minutes"] = task.interval_minutes
            else:
                entry["time"] = f"{task.hour:02d}:{task.minute:02d}"
            result.append(entry)
        return result

    # ── Tick Processing ──────────────────────────────────────────────

    def tick(self, current_hour, current_minute, current_day=None):
        """Advance the scheduler by one game-time minute.

        Should be called each Sim-minute by an in-game alarm or zone hook.

        Args:
            current_hour: Current game hour (0-23).
            current_minute: Current game minute (0-59).
            current_day: Current day number (monotonically increasing).
                         If None, auto-increments when hour wraps past 0.
        """
        self._total_ticks += 1

        if current_day is not None:
            self._current_day = current_day
        elif current_hour == 0 and current_minute == 0:
            self._current_day += 1

        to_remove = []

        for label, task in self._tasks.items():
            should_fire = False

            if task.kind == "daily":
                if (current_hour == task.hour and
                        current_minute == task.minute and
                        task.last_run_day != self._current_day):
                    should_fire = True
                    task.last_run_day = self._current_day

            elif task.kind == "interval":
                if task.last_run_tick < 0:
                    task.last_run_tick = self._total_ticks
                elapsed = self._total_ticks - task.last_run_tick
                if elapsed >= task.interval_minutes:
                    should_fire = True
                    task.last_run_tick = self._total_ticks

            elif task.kind == "once":
                if (not task.once_fired and
                        current_hour == task.hour and
                        current_minute == task.minute):
                    should_fire = True
                    task.once_fired = True
                    to_remove.append(label)

            if should_fire:
                try:
                    task.callback()
                except Exception as exc:
                    log.error(
                        "Scheduled task failed",
                        label=label,
                        error=str(exc),
                    )

        for label in to_remove:
            self._tasks.pop(label, None)

    def reset(self):
        """Clear all tasks and reset state.  For testing."""
        self._tasks.clear()
        self._current_day = 0
        self._total_ticks = 0
