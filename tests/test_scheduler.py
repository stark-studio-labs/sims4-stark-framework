"""Tests for the game-time scheduler."""

import pytest
from stark_framework.core.scheduler import GameScheduler


@pytest.fixture
def scheduler():
    s = GameScheduler()
    yield s
    s.reset()


class TestDailyTasks:
    def test_daily_fires_at_correct_time(self, scheduler):
        fired = []
        scheduler.daily(hour=6, callback=lambda: fired.append(1), label="morning")

        # Tick through to 6:00 on day 0
        for h in range(6):
            for m in range(60):
                scheduler.tick(h, m, current_day=0)

        assert len(fired) == 0  # hasn't reached 6:00 yet

        scheduler.tick(6, 0, current_day=0)
        assert len(fired) == 1

    def test_daily_does_not_fire_twice_same_day(self, scheduler):
        fired = []
        scheduler.daily(hour=12, callback=lambda: fired.append(1), label="noon")

        scheduler.tick(12, 0, current_day=0)
        scheduler.tick(12, 0, current_day=0)  # same day, same time

        assert len(fired) == 1

    def test_daily_fires_again_next_day(self, scheduler):
        fired = []
        scheduler.daily(hour=0, callback=lambda: fired.append(1), label="midnight")

        scheduler.tick(0, 0, current_day=0)
        assert len(fired) == 1

        scheduler.tick(0, 0, current_day=1)
        assert len(fired) == 2

    def test_daily_with_minute(self, scheduler):
        fired = []
        scheduler.daily(hour=8, minute=30, callback=lambda: fired.append(1), label="830")

        scheduler.tick(8, 0, current_day=0)
        assert len(fired) == 0

        scheduler.tick(8, 30, current_day=0)
        assert len(fired) == 1


class TestIntervalTasks:
    def test_interval_fires_after_n_ticks(self, scheduler):
        fired = []
        scheduler.interval(sim_minutes=10, callback=lambda: fired.append(1), label="check")

        for i in range(11):
            scheduler.tick(0, i, current_day=0)

        # First tick sets last_run_tick, then fires after 10 more ticks
        assert len(fired) == 1

    def test_interval_fires_repeatedly(self, scheduler):
        fired = []
        scheduler.interval(sim_minutes=5, callback=lambda: fired.append(1), label="fast")

        for i in range(26):
            scheduler.tick(0, i % 60, current_day=0)

        # Should fire multiple times (at tick 6, 11, 16, 21, 26 roughly)
        assert len(fired) >= 4


class TestOnceTasks:
    def test_once_fires_and_removes(self, scheduler):
        fired = []
        scheduler.once(hour=15, minute=0, callback=lambda: fired.append(1), label="once")

        scheduler.tick(15, 0, current_day=0)
        assert len(fired) == 1

        # Task should be removed
        assert scheduler.list_tasks() == []

        scheduler.tick(15, 0, current_day=1)
        assert len(fired) == 1  # not fired again


class TestCancelAndList:
    def test_cancel_task(self, scheduler):
        fired = []
        scheduler.daily(hour=6, callback=lambda: fired.append(1), label="cancel_me")

        scheduler.cancel("cancel_me")
        scheduler.tick(6, 0, current_day=0)

        assert len(fired) == 0

    def test_cancel_returns_false_for_unknown(self, scheduler):
        assert scheduler.cancel("nonexistent") is False

    def test_list_tasks(self, scheduler):
        scheduler.daily(hour=6, callback=lambda: None, label="morning")
        scheduler.interval(sim_minutes=30, callback=lambda: None, label="check")
        scheduler.once(hour=12, callback=lambda: None, label="noon")

        tasks = scheduler.list_tasks()
        assert len(tasks) == 3
        labels = {t["label"] for t in tasks}
        assert labels == {"morning", "check", "noon"}


class TestErrorHandling:
    def test_failing_callback_doesnt_crash_scheduler(self, scheduler):
        def bad():
            raise ValueError("boom")

        scheduler.daily(hour=0, callback=bad, label="bad")
        # Should not raise
        scheduler.tick(0, 0, current_day=0)


class TestReset:
    def test_reset_clears_everything(self, scheduler):
        scheduler.daily(hour=6, callback=lambda: None, label="morning")
        scheduler.reset()
        assert scheduler.list_tasks() == []
