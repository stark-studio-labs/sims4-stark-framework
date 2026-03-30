"""
Structured Logging -- mod-aware logging with context fields.

Provides a logging interface that tags every message with the mod name,
supports structured key-value fields, and routes to both the game's
exception log and an in-memory buffer for diagnostics.

Usage:
    from stark_framework.utils.logging import get_logger

    log = get_logger("my_awesome_mod")

    # Basic logging
    log.info("Mod initialized")
    log.warn("Unusual state detected")
    log.error("Failed to apply buff")

    # Structured fields -- key=value pairs appended to the message
    log.info("Sim loaded", sim_id=12345, name="Bella Goth")
    log.error("Injection failed", target="sims.sim.Sim", method="on_add")

    # Debug (only visible when debug mode is enabled)
    log.debug("Cache miss", key="trait_lookup")

    # Get the in-memory log buffer (useful for health reports)
    from stark_framework.utils.logging import LogBuffer
    recent = LogBuffer.get_entries(limit=20)
"""

import sys
import time


class LogBuffer:
    """In-memory rolling buffer of log entries for diagnostics."""

    _entries = []    # type: list[dict]
    _max_entries = 1000

    @classmethod
    def append(cls, entry):
        """Add a log entry to the buffer."""
        cls._entries.append(entry)
        if len(cls._entries) > cls._max_entries:
            cls._entries = cls._entries[-cls._max_entries:]

    @classmethod
    def get_entries(cls, limit=50, level=None, mod_name=None):
        """Get recent log entries.

        Args:
            limit: Max entries to return (newest first).
            level: Filter by log level ("INFO", "WARN", "ERROR", "DEBUG").
            mod_name: Filter by mod/logger name.

        Returns:
            List of log entry dicts, newest first.
        """
        entries = cls._entries
        if level:
            entries = [e for e in entries if e["level"] == level]
        if mod_name:
            entries = [e for e in entries if e["mod_name"] == mod_name]
        return list(reversed(entries[-limit:]))

    @classmethod
    def clear(cls):
        """Clear the buffer. For testing only."""
        cls._entries.clear()


class Logger:
    """Structured logger for a specific mod or component.

    Do not instantiate directly -- use get_logger().
    """

    _debug_enabled = False  # Class-level debug toggle

    def __init__(self, name):
        self._name = name

    def info(self, message, **fields):
        """Log an informational message.

        Args:
            message: The log message.
            **fields: Key-value pairs to attach as structured context.

        Example:
            log.info("Buff applied", sim_id=42, buff="happy_buff", duration=120.0)
        """
        self._log("INFO", message, fields)

    def warn(self, message, **fields):
        """Log a warning.

        Args:
            message: The warning message.
            **fields: Structured context.

        Example:
            log.warn("Tuning override detected", tuning_id="0x1A2B3C4D")
        """
        self._log("WARN", message, fields)

    def error(self, message, **fields):
        """Log an error.

        Args:
            message: The error message.
            **fields: Structured context.

        Example:
            log.error("Injection failed", target="sims.sim.Sim", exc=str(e))
        """
        self._log("ERROR", message, fields)

    def debug(self, message, **fields):
        """Log a debug message (only when debug mode is enabled).

        Args:
            message: The debug message.
            **fields: Structured context.

        Example:
            log.debug("Cache lookup", key="trait_42", hit=False)
        """
        if self._debug_enabled:
            self._log("DEBUG", message, fields)

    def _log(self, level, message, fields):
        """Internal: format and output a log entry."""
        timestamp = time.time()

        # Build structured message
        field_str = ""
        if fields:
            pairs = [f"{k}={v!r}" for k, v in fields.items()]
            field_str = " | " + ", ".join(pairs)

        formatted = f"[{level}] [{self._name}] {message}{field_str}"

        # Write to stderr (shows in game console / exception log)
        try:
            print(formatted, file=sys.stderr)
        except Exception:
            pass

        # Buffer for diagnostics
        LogBuffer.append({
            "timestamp": timestamp,
            "level": level,
            "mod_name": self._name,
            "message": message,
            "fields": fields,
            "formatted": formatted,
        })

    @classmethod
    def set_debug(cls, enabled=True):
        """Enable or disable debug logging globally.

        Args:
            enabled: True to show debug messages, False to suppress.
        """
        cls._debug_enabled = enabled


def get_logger(name):
    """Create a logger for a mod or component.

    Args:
        name: Logger name (typically your mod_id or "stark.component_name").

    Returns:
        A Logger instance.

    Example:
        from stark_framework.utils.logging import get_logger
        log = get_logger("my_mod")
        log.info("Hello from my mod!")
    """
    return Logger(name)
