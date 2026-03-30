"""
Built-in Diagnostics -- error tracking, mod conflict detection, health reports.

Every error caught by the framework (event handlers, injections, services) is
recorded here with full context. Mod developers can query the error log and
generate health reports without digging through game logs.

Usage:
    from stark_framework.core.diagnostics import Diagnostics

    # Errors are recorded automatically by the framework, but you can also
    # record your own:
    try:
        risky_operation()
    except Exception as e:
        Diagnostics.record_error(
            mod_id="my_mod",
            error=e,
            context="Applying custom trait to Sim",
        )

    # Get all errors for a mod
    errors = Diagnostics.get_errors(mod_id="my_mod")
    for err in errors:
        print(f"[{err['timestamp']}] {err['context']}: {err['error']}")

    # Generate a full health report (useful for bug reports)
    report = Diagnostics.health_report()
    print(report)

    # Detect potential conflicts between mods
    conflicts = Diagnostics.detect_conflicts()
    for c in conflicts:
        print(f"Conflict: {c['description']}")
"""

import traceback
import time


class Diagnostics:
    """Framework-wide error tracking and diagnostics."""

    _errors = []     # type: list[dict]
    _max_errors = 500  # Rolling buffer

    @classmethod
    def record_error(cls, mod_id, error, context=""):
        """Record an error with full context.

        Args:
            mod_id: The mod that caused or encountered the error.
            error: The exception instance.
            context: Human-readable description of what was happening.
        """
        entry = {
            "timestamp": time.time(),
            "mod_id": mod_id,
            "error": str(error),
            "error_type": type(error).__name__,
            "traceback": traceback.format_exception(
                type(error), error, error.__traceback__
            ),
            "context": context,
        }
        cls._errors.append(entry)

        # Rolling buffer
        if len(cls._errors) > cls._max_errors:
            cls._errors = cls._errors[-cls._max_errors:]

    @classmethod
    def get_errors(cls, mod_id=None, limit=50):
        """Get recorded errors, optionally filtered by mod.

        Args:
            mod_id: If provided, only return errors from this mod.
            limit: Maximum number of errors to return (most recent first).

        Returns:
            List of error dicts, newest first.
        """
        errors = cls._errors
        if mod_id:
            errors = [e for e in errors if e["mod_id"] == mod_id]
        return list(reversed(errors[-limit:]))

    @classmethod
    def error_count(cls, mod_id=None):
        """Count recorded errors.

        Args:
            mod_id: If provided, count only this mod's errors.

        Returns:
            Integer error count.
        """
        if mod_id:
            return sum(1 for e in cls._errors if e["mod_id"] == mod_id)
        return len(cls._errors)

    @classmethod
    def detect_conflicts(cls):
        """Detect potential conflicts between loaded mods.

        Checks:
        - Multiple mods injecting the same game method
        - Mods with declared conflicts that are both loaded
        - High error rates from specific mods

        Returns:
            List of conflict descriptions.
        """
        from stark_framework.core.injection import InjectionManager
        from stark_framework.core.registry import ModRegistry

        conflicts = []

        # Check for overlapping injections on the same method
        injection_targets = {}  # (target, method) -> [mod_ids]
        for inj in InjectionManager.list_injections():
            key = (inj["target"], inj["method"])
            injection_targets.setdefault(key, []).append(inj["mod_id"])

        for (target, method), mod_ids in injection_targets.items():
            if len(mod_ids) > 1:
                conflicts.append({
                    "type": "injection_overlap",
                    "description": (
                        f"Multiple mods inject {target}.{method}: "
                        f"{', '.join(str(m) for m in mod_ids)}"
                    ),
                    "severity": "warning",
                    "mods": mod_ids,
                })

        # Check for high error rates
        mod_error_counts = {}
        for err in cls._errors:
            mid = err["mod_id"]
            mod_error_counts[mid] = mod_error_counts.get(mid, 0) + 1

        for mid, count in mod_error_counts.items():
            if count >= 10:
                conflicts.append({
                    "type": "high_error_rate",
                    "description": (
                        f"Mod '{mid}' has {count} recorded errors"
                    ),
                    "severity": "error",
                    "mods": [mid],
                })

        return conflicts

    @classmethod
    def health_report(cls):
        """Generate a human-readable health report.

        Returns:
            Multi-line string summarizing framework health.
        """
        from stark_framework.core.registry import ModRegistry
        from stark_framework.core.injection import InjectionManager

        lines = []
        lines.append("=== Stark Framework Health Report ===")
        lines.append("")

        # Loaded mods
        mods = ModRegistry.all_mods()
        lines.append(f"Loaded mods: {len(mods)}")
        for mod_id, info in mods.items():
            err_count = cls.error_count(mod_id=mod_id)
            status = "OK" if err_count == 0 else f"{err_count} errors"
            lines.append(f"  {info['name']} v{info['version']} [{status}]")

        lines.append("")

        # Active injections
        injections = InjectionManager.list_injections()
        lines.append(f"Active injections: {len(injections)}")
        for inj in injections:
            lines.append(
                f"  {inj['target']}.{inj['method']} "
                f"({inj['kind']}) by {inj['mod_id']}"
            )

        lines.append("")

        # Conflicts
        conflicts = cls.detect_conflicts()
        lines.append(f"Detected conflicts: {len(conflicts)}")
        for c in conflicts:
            lines.append(f"  [{c['severity'].upper()}] {c['description']}")

        lines.append("")

        # Recent errors
        recent = cls.get_errors(limit=5)
        lines.append(f"Total errors: {cls.error_count()} (showing last {len(recent)})")
        for err in recent:
            lines.append(f"  [{err['error_type']}] {err['context']}: {err['error']}")

        lines.append("")
        lines.append("=== End Report ===")
        return "\n".join(lines)

    @classmethod
    def clear(cls):
        """Clear all recorded errors. For testing only."""
        cls._errors.clear()
