"""Tests for the debug module -- console, logger, and sim inspector."""

import pytest
import os
import logging
from types import SimpleNamespace

from stark_framework.debug.console import DebugConsole
from stark_framework.debug.logger import DebugLogger
from stark_framework.debug.inspector import SimInspector


# ── Fixtures ─────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clean_console():
    """Reset the debug console between tests."""
    DebugConsole.reset()
    yield
    DebugConsole.reset()


# ── DebugConsole: Logging ────────────────────────────────────────────

class TestConsoleLogging:
    def test_log_adds_entry(self):
        DebugConsole.log("INFO", "test-mod", "Hello")
        entries = DebugConsole.get_entries()
        assert len(entries) == 1
        assert entries[0]["level"] == "INFO"
        assert entries[0]["source"] == "test-mod"
        assert entries[0]["message"] == "Hello"

    def test_log_entry_has_timestamp(self):
        DebugConsole.log("DEBUG", "test-mod", "tick")
        entries = DebugConsole.get_entries()
        assert "timestamp" in entries[0]
        assert isinstance(entries[0]["timestamp"], float)

    def test_log_rejects_invalid_level(self):
        with pytest.raises(ValueError, match="Invalid log level"):
            DebugConsole.log("FATAL", "test-mod", "boom")

    def test_log_normalizes_level_case(self):
        DebugConsole.log("warn", "test-mod", "caution")
        entries = DebugConsole.get_entries()
        assert entries[0]["level"] == "WARN"

    def test_all_levels_accepted(self):
        for level in ("DEBUG", "INFO", "WARN", "ERROR"):
            DebugConsole.log(level, "test-mod", f"{level} message")
        assert len(DebugConsole.get_entries()) == 4


# ── DebugConsole: Circular Buffer ────────────────────────────────────

class TestConsoleBuffer:
    def test_buffer_limit(self):
        for i in range(600):
            DebugConsole.log("INFO", "test-mod", f"msg-{i}")

        entries = DebugConsole.get_entries()
        assert len(entries) == 500
        # Oldest entries should be trimmed -- first entry should be msg-100
        assert entries[0]["message"] == "msg-100"
        assert entries[-1]["message"] == "msg-599"

    def test_clear_empties_buffer(self):
        DebugConsole.log("INFO", "test-mod", "hello")
        assert len(DebugConsole.get_entries()) == 1

        DebugConsole.clear()
        assert len(DebugConsole.get_entries()) == 0


# ── DebugConsole: Filtering ──────────────────────────────────────────

class TestConsoleFiltering:
    def test_filter_by_level(self):
        DebugConsole.log("INFO", "mod-a", "info msg")
        DebugConsole.log("ERROR", "mod-a", "error msg")
        DebugConsole.log("INFO", "mod-b", "another info")

        errors = DebugConsole.filter_by_level("ERROR")
        assert len(errors) == 1
        assert errors[0]["message"] == "error msg"

        infos = DebugConsole.filter_by_level("INFO")
        assert len(infos) == 2

    def test_filter_by_source(self):
        DebugConsole.log("INFO", "mod-a", "from a")
        DebugConsole.log("INFO", "mod-b", "from b")
        DebugConsole.log("ERROR", "mod-a", "error from a")

        a_logs = DebugConsole.filter_by_source("mod-a")
        assert len(a_logs) == 2
        assert all(e["source"] == "mod-a" for e in a_logs)

    def test_filter_empty_result(self):
        DebugConsole.log("INFO", "mod-a", "hello")
        assert DebugConsole.filter_by_level("ERROR") == []
        assert DebugConsole.filter_by_source("nonexistent") == []


# ── DebugConsole: Dump to File ───────────────────────────────────────

class TestConsoleDump:
    def test_dump_to_file(self, tmp_path):
        DebugConsole.log("INFO", "mod-a", "first line")
        DebugConsole.log("ERROR", "mod-b", "second line")

        dump_path = str(tmp_path / "debug.log")
        DebugConsole.dump_to_file(dump_path)

        assert os.path.exists(dump_path)
        with open(dump_path) as f:
            lines = f.readlines()

        assert len(lines) == 2
        assert "[INFO]" in lines[0]
        assert "[mod-a]" in lines[0]
        assert "first line" in lines[0]
        assert "[ERROR]" in lines[1]
        assert "[mod-b]" in lines[1]
        assert "second line" in lines[1]

    def test_dump_empty_buffer(self, tmp_path):
        dump_path = str(tmp_path / "empty.log")
        DebugConsole.dump_to_file(dump_path)

        with open(dump_path) as f:
            content = f.read()
        assert content == ""


# ── DebugConsole: Mod Registration ───────────────────────────────────

class TestModRegistration:
    def test_register_mod(self):
        DebugConsole.register_mod("my-mod", "1.0.0")

        status = DebugConsole.get_mod_status()
        assert "my-mod" in status
        assert status["my-mod"]["version"] == "1.0.0"
        assert status["my-mod"]["status"] == "ok"
        assert status["my-mod"]["errors"] == 0

    def test_register_logs_info(self):
        DebugConsole.register_mod("my-mod", "2.0.0")

        entries = DebugConsole.get_entries()
        assert len(entries) == 1
        assert entries[0]["level"] == "INFO"
        assert "my-mod" in entries[0]["message"]
        assert "2.0.0" in entries[0]["message"]

    def test_report_error_updates_status(self):
        DebugConsole.register_mod("buggy-mod", "0.1.0")
        DebugConsole.report_error("buggy-mod", "Something broke")

        status = DebugConsole.get_mod_status()
        assert status["buggy-mod"]["status"] == "error"
        assert status["buggy-mod"]["errors"] == 1

    def test_multiple_errors_increment(self):
        DebugConsole.register_mod("buggy-mod", "0.1.0")
        DebugConsole.report_error("buggy-mod", "Error 1")
        DebugConsole.report_error("buggy-mod", "Error 2")
        DebugConsole.report_error("buggy-mod", "Error 3")

        status = DebugConsole.get_mod_status()
        assert status["buggy-mod"]["errors"] == 3

    def test_report_error_logs_to_buffer(self):
        DebugConsole.register_mod("my-mod", "1.0.0")
        DebugConsole.report_error("my-mod", "Kaboom!")

        errors = DebugConsole.filter_by_level("ERROR")
        assert len(errors) == 1
        assert "Kaboom!" in errors[0]["message"]

    def test_report_error_unregistered_mod(self):
        # Should not raise -- just logs the error
        DebugConsole.report_error("unknown-mod", "Something happened")

        errors = DebugConsole.filter_by_level("ERROR")
        assert len(errors) == 1

    def test_get_mod_status_empty(self):
        assert DebugConsole.get_mod_status() == {}

    def test_multiple_mods(self):
        DebugConsole.register_mod("mod-a", "1.0.0")
        DebugConsole.register_mod("mod-b", "2.0.0")
        DebugConsole.report_error("mod-b", "oops")

        status = DebugConsole.get_mod_status()
        assert len(status) == 2
        assert status["mod-a"]["status"] == "ok"
        assert status["mod-b"]["status"] == "error"


# ── DebugLogger ──────────────────────────────────────────────────────

class TestDebugLogger:
    def test_logger_routes_to_console(self):
        logger = DebugLogger("test-mod")
        logger.info("hello from logger")

        entries = DebugConsole.get_entries()
        assert len(entries) == 1
        assert entries[0]["source"] == "test-mod"
        assert entries[0]["level"] == "INFO"
        assert entries[0]["message"] == "hello from logger"

    def test_all_levels(self):
        logger = DebugLogger("test-mod")
        logger.debug("d")
        logger.info("i")
        logger.warn("w")
        logger.error("e")

        entries = DebugConsole.get_entries()
        levels = [e["level"] for e in entries]
        assert levels == ["DEBUG", "INFO", "WARN", "ERROR"]

    def test_error_with_exception(self):
        logger = DebugLogger("test-mod")
        try:
            raise RuntimeError("test error")
        except RuntimeError as exc:
            logger.error("Operation failed", exc=exc)

        entries = DebugConsole.get_entries()
        assert len(entries) == 1
        assert "Operation failed: test error" in entries[0]["message"]

    def test_error_reports_to_console(self):
        DebugConsole.register_mod("test-mod", "1.0.0")
        logger = DebugLogger("test-mod")
        logger.error("broken")

        status = DebugConsole.get_mod_status()
        assert status["test-mod"]["status"] == "error"
        assert status["test-mod"]["errors"] == 1

    def test_logger_writes_to_python_logging(self, caplog):
        logger = DebugLogger("test-mod")
        with caplog.at_level(logging.DEBUG, logger="stark.test-mod"):
            logger.info("python log test")

        assert any("python log test" in r.message for r in caplog.records)

    def test_multiple_loggers_independent(self):
        log_a = DebugLogger("mod-a")
        log_b = DebugLogger("mod-b")

        log_a.info("from a")
        log_b.info("from b")

        a_entries = DebugConsole.filter_by_source("mod-a")
        b_entries = DebugConsole.filter_by_source("mod-b")
        assert len(a_entries) == 1
        assert len(b_entries) == 1


# ── SimInspector ─────────────────────────────────────────────────────

def _make_mock_sim(**overrides):
    """Create a mock sim_info with sensible defaults."""
    defaults = {
        "sim_id": 42,
        "first_name": "Bella",
        "last_name": "Goth",
        "traits": ["Romantic", "Gloomy", "Bookworm"],
        "buffs": SimpleNamespace(active_buffs=["Happy", "Inspired"]),
        "skills": ["Cooking (Lv 5)", "Painting (Lv 3)"],
        "career": "Scientist",
        "household": SimpleNamespace(name="Goth", funds=50000),
        "relationships": ["Mortimer (Spouse)", "Alexander (Child)"],
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class TestSimInspector:
    def test_inspect_basic_sim(self):
        sim = _make_mock_sim()
        inspector = SimInspector()
        data = inspector.inspect_sim(sim)

        assert data["name"] == "Bella Goth"
        assert data["sim_id"] == 42

    def test_inspect_traits_direct(self):
        sim = _make_mock_sim()
        inspector = SimInspector()
        data = inspector.inspect_sim(sim)

        assert len(data["traits"]) == 3
        assert "Romantic" in data["traits"]

    def test_inspect_traits_via_tracker(self):
        tracker = SimpleNamespace(equipped_traits=["Evil", "Genius"])
        sim = _make_mock_sim(trait_tracker=tracker, traits=None)
        inspector = SimInspector()
        data = inspector.inspect_sim(sim)

        assert "Evil" in data["traits"]
        assert "Genius" in data["traits"]

    def test_inspect_buffs(self):
        sim = _make_mock_sim()
        inspector = SimInspector()
        data = inspector.inspect_sim(sim)

        # Buffs accessed via .buffs.active_buffs
        assert "Happy" in [str(b) for b in data["buffs"]]

    def test_inspect_funds(self):
        sim = _make_mock_sim()
        inspector = SimInspector()
        data = inspector.inspect_sim(sim)

        assert data["funds"] == 50000

    def test_inspect_household(self):
        sim = _make_mock_sim()
        inspector = SimInspector()
        data = inspector.inspect_sim(sim)

        assert data["household"] == "Goth"

    def test_inspect_missing_attributes(self):
        """Inspector should not crash on a minimal sim with missing attrs."""
        sim = SimpleNamespace(sim_id=99)
        inspector = SimInspector()
        data = inspector.inspect_sim(sim)

        assert data["sim_id"] == 99
        assert data["name"] == "Unknown"
        assert data["traits"] == []
        assert data["buffs"] == []
        assert data["funds"] == 0

    def test_inspect_funds_as_money_object(self):
        """Funds might be an object with a .money attribute."""
        funds_obj = SimpleNamespace(money=75000)
        household = SimpleNamespace(name="Landgraab", funds=funds_obj)
        sim = _make_mock_sim(household=household)
        inspector = SimInspector()
        data = inspector.inspect_sim(sim)

        assert data["funds"] == 75000

    def test_format_report_basic(self):
        sim = _make_mock_sim()
        inspector = SimInspector()
        data = inspector.inspect_sim(sim)
        report = inspector.format_report(data)

        assert "Bella Goth" in report
        assert "Sim ID: 42" in report
        assert "Traits (3):" in report
        assert "Romantic" in report
        assert "Funds: 50,000" in report
        assert "=== End Report ===" in report

    def test_format_report_empty_sim(self):
        sim = SimpleNamespace(sim_id=1)
        inspector = SimInspector()
        data = inspector.inspect_sim(sim)
        report = inspector.format_report(data)

        assert "(none)" in report
        assert "Funds: 0" in report

    def test_format_report_contains_all_sections(self):
        sim = _make_mock_sim()
        inspector = SimInspector()
        data = inspector.inspect_sim(sim)
        report = inspector.format_report(data)

        assert "Traits" in report
        assert "Buffs" in report
        assert "Skills" in report
        assert "Career" in report
        assert "Household" in report
        assert "Funds" in report
        assert "Relationships" in report
