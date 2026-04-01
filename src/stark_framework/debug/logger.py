"""
Per-Mod Debug Logger -- convenience wrapper around DebugConsole.

Each mod creates its own DebugLogger instance, which prefixes messages with the
mod name and routes everything to the centralized DebugConsole. Also mirrors
output to Python's standard logging module for compatibility with external tools.

Usage:
    from stark_framework.debug.logger import DebugLogger

    logger = DebugLogger("economy-sim")

    logger.debug("Recalculating market prices...")
    logger.info("Market open: 42 items listed")
    logger.warn("Price cap reached for item 'Diamond Ring'")
    logger.error("Division by zero in tax calculator", exc=err)
"""

import logging

from stark_framework.debug.console import DebugConsole


class DebugLogger:
    """Per-mod logger that routes to DebugConsole and Python logging.

    Args:
        mod_name: Unique mod identifier (e.g. "economy-sim"). Used as the
            source field in all log entries and as the Python logger name.
    """

    def __init__(self, mod_name):
        self.mod_name = mod_name
        self._py_logger = logging.getLogger(f"stark.{mod_name}")

    def debug(self, msg):
        """Log a DEBUG-level message.

        Args:
            msg: The log message.
        """
        DebugConsole.log("DEBUG", self.mod_name, msg)
        self._py_logger.debug("[%s] %s", self.mod_name, msg)

    def info(self, msg):
        """Log an INFO-level message.

        Args:
            msg: The log message.
        """
        DebugConsole.log("INFO", self.mod_name, msg)
        self._py_logger.info("[%s] %s", self.mod_name, msg)

    def warn(self, msg):
        """Log a WARN-level message.

        Args:
            msg: The log message.
        """
        DebugConsole.log("WARN", self.mod_name, msg)
        self._py_logger.warning("[%s] %s", self.mod_name, msg)

    def error(self, msg, exc=None):
        """Log an ERROR-level message and report it to the console.

        Args:
            msg: The log message.
            exc: Optional exception instance for context.
        """
        full_msg = msg
        if exc is not None:
            full_msg = f"{msg}: {exc}"

        DebugConsole.report_error(self.mod_name, full_msg)
        self._py_logger.error("[%s] %s", self.mod_name, full_msg, exc_info=exc)
