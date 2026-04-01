"""
Debug Console -- centralized logging hub for all Stark Framework mods.

Provides a singleton console that collects log entries from every mod into a
circular buffer. Mod developers register on load, report errors, and query
the log by level or source.

Usage:
    from stark_framework.debug.console import DebugConsole

    # Mods register themselves on load
    DebugConsole.register_mod("economy-sim", "1.0.0")
    DebugConsole.register_mod("drama-engine", "0.3.1")

    # Log messages (any mod or framework code)
    DebugConsole.log("INFO", "economy-sim", "Market prices recalculated")
    DebugConsole.log("ERROR", "drama-engine", "Failed to trigger scandal event")

    # Query logs
    errors = DebugConsole.filter_by_level("ERROR")
    economy_logs = DebugConsole.filter_by_source("economy-sim")

    # Mod health overview
    status = DebugConsole.get_mod_status()
    # {"economy-sim": {"version": "1.0.0", "status": "ok"},
    #  "drama-engine": {"version": "0.3.1", "status": "error", "errors": 1}}

    # Dump to file for bug reports
    DebugConsole.dump_to_file("/tmp/stark-debug.log")
"""

import time


class DebugConsole:
    """Singleton debug console with a 500-entry circular log buffer.

    All state is class-level -- there is exactly one console per process,
    matching the single-threaded nature of The Sims 4.
    """

    LEVELS = ("DEBUG", "INFO", "WARN", "ERROR")

    _buffer = []       # type: list[dict]
    _max_entries = 500
    _mods = {}         # type: dict[str, dict]

    # ── Logging ─────────────────────────────────────────────────────

    @classmethod
    def log(cls, level, source, message):
        """Add a log entry to the circular buffer.

        Args:
            level: One of DEBUG, INFO, WARN, ERROR.
            source: Mod name or framework component.
            message: Human-readable log message.

        Raises:
            ValueError: If level is not recognized.
        """
        level = level.upper()
        if level not in cls.LEVELS:
            raise ValueError(
                f"Invalid log level '{level}'. "
                f"Must be one of: {', '.join(cls.LEVELS)}"
            )

        entry = {
            "timestamp": time.time(),
            "level": level,
            "source": source,
            "message": message,
        }
        cls._buffer.append(entry)

        # Circular buffer -- trim from the front
        if len(cls._buffer) > cls._max_entries:
            cls._buffer = cls._buffer[-cls._max_entries:]

    # ── Filtering ───────────────────────────────────────────────────

    @classmethod
    def filter_by_level(cls, level):
        """Return log entries matching the given level.

        Args:
            level: DEBUG, INFO, WARN, or ERROR.

        Returns:
            List of matching log entry dicts.
        """
        level = level.upper()
        return [e for e in cls._buffer if e["level"] == level]

    @classmethod
    def filter_by_source(cls, source):
        """Return log entries from a specific mod or component.

        Args:
            source: The mod name or component identifier.

        Returns:
            List of matching log entry dicts.
        """
        return [e for e in cls._buffer if e["source"] == source]

    # ── Buffer Management ───────────────────────────────────────────

    @classmethod
    def clear(cls):
        """Clear all log entries from the buffer."""
        cls._buffer.clear()

    @classmethod
    def dump_to_file(cls, path):
        """Write the current log buffer to a file.

        Each entry is written as one line:
            [timestamp] [LEVEL] [source] message

        Args:
            path: File path to write to.
        """
        with open(path, "w") as f:
            for entry in cls._buffer:
                ts = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(entry["timestamp"])
                )
                f.write(
                    f"[{ts}] [{entry['level']}] "
                    f"[{entry['source']}] {entry['message']}\n"
                )

    @classmethod
    def get_entries(cls):
        """Return a copy of all log entries.

        Returns:
            List of log entry dicts.
        """
        return list(cls._buffer)

    # ── Mod Registration ────────────────────────────────────────────

    @classmethod
    def register_mod(cls, name, version):
        """Register a mod with the debug console.

        Mods should call this on load so the console can track their status.

        Args:
            name: Unique mod identifier (e.g. "economy-sim").
            version: Version string (e.g. "1.0.0").
        """
        cls._mods[name] = {
            "version": version,
            "status": "ok",
            "errors": 0,
        }
        cls.log("INFO", name, f"Mod registered: {name} v{version}")

    @classmethod
    def report_error(cls, mod_name, error):
        """Report an error from a mod.

        Updates the mod's status to 'error' and increments its error count.
        Also logs the error to the buffer.

        Args:
            mod_name: The mod reporting the error.
            error: The exception or error message.
        """
        if mod_name in cls._mods:
            cls._mods[mod_name]["status"] = "error"
            cls._mods[mod_name]["errors"] += 1

        cls.log("ERROR", mod_name, str(error))

    @classmethod
    def get_mod_status(cls):
        """Return a dict of all registered mods and their current status.

        Returns:
            Dict mapping mod name to status info:
            {"mod_name": {"version": "1.0", "status": "ok", "errors": 0}}
        """
        return dict(cls._mods)

    # ── Reset (testing) ─────────────────────────────────────────────

    @classmethod
    def reset(cls):
        """Clear all state -- buffer and mod registry. For testing only."""
        cls._buffer.clear()
        cls._mods.clear()
