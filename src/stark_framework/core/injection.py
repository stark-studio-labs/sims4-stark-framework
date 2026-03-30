"""
Clean Injection Decorators -- wrap game methods without monkey-patching.

Provides decorators that intercept Sims 4 game methods at well-defined points.
Each injection is tracked by the framework for diagnostics and conflict detection.

The key difference from S4CL: injections are declarative, reversible, and visible
to the diagnostics system. No silent overwrites.

Usage:
    from stark_framework.core.injection import inject_before, inject_after, inject_replace

    # Run code BEFORE a game method (original still runs after)
    @inject_before("sims.sim.Sim", "on_add")
    def before_sim_add(original, self, *args, **kwargs):
        print(f"Sim about to be added!")
        return original(self, *args, **kwargs)

    # Run code AFTER a game method (receives original's return value)
    @inject_after("sims.sim.Sim", "on_remove")
    def after_sim_remove(original, self, *args, **kwargs):
        result = original(self, *args, **kwargs)
        print(f"Sim was removed, cleaning up...")
        return result

    # Fully replace a game method (you control whether original runs)
    @inject_replace("sims.sim_info.SimInfo", "get_name")
    def custom_name(original, self, *args, **kwargs):
        real_name = original(self, *args, **kwargs)
        return f"[Modded] {real_name}"

    # Undo all injections from a specific mod
    InjectionManager.revert_all(mod_id="my_mod")

    # List all active injections
    for inj in InjectionManager.list_injections():
        print(f"{inj['target']}.{inj['method']} -- {inj['kind']} by {inj['mod_id']}")
"""

import functools
import importlib


class InjectionError(Exception):
    """Raised when an injection fails (bad target, method not found, etc.)."""
    pass


class _InjectionRecord:
    """Internal: tracks a single injection for diagnostics and revert."""

    __slots__ = (
        "target_path", "method_name", "kind", "mod_id",
        "wrapper_fn", "original_fn", "target_class",
    )

    def __init__(self, target_path, method_name, kind, mod_id,
                 wrapper_fn, original_fn, target_class):
        self.target_path = target_path
        self.method_name = method_name
        self.kind = kind
        self.mod_id = mod_id
        self.wrapper_fn = wrapper_fn
        self.original_fn = original_fn
        self.target_class = target_class


class InjectionManager:
    """Tracks and manages all method injections."""

    _injections = []  # type: list[_InjectionRecord]

    @classmethod
    def _resolve_target(cls, target_path):
        """Resolve a dotted path like 'sims.sim.Sim' to the actual class.

        In the real game environment, these modules are available at runtime.
        Outside the game (testing), this will raise ImportError -- use mocks.
        """
        parts = target_path.rsplit(".", 1)
        if len(parts) != 2:
            raise InjectionError(
                f"target_path must be 'module.path.ClassName', got '{target_path}'"
            )
        module_path, class_name = parts
        try:
            module = importlib.import_module(module_path)
        except ImportError:
            raise InjectionError(
                f"Could not import module '{module_path}'. "
                f"Are you running inside The Sims 4?"
            )
        target_class = getattr(module, class_name, None)
        if target_class is None:
            raise InjectionError(
                f"Class '{class_name}' not found in module '{module_path}'."
            )
        return target_class

    @classmethod
    def inject(cls, target_path, method_name, wrapper_fn, kind="before", mod_id=None):
        """Apply an injection to a game method.

        Args:
            target_path: Dotted path to the target class (e.g. "sims.sim.Sim").
            method_name: Name of the method to inject into.
            wrapper_fn: The wrapper function. Signature: (original, self, *args, **kwargs).
            kind: One of "before", "after", "replace".
            mod_id: Optional mod identifier for diagnostics.

        Returns:
            The _InjectionRecord for this injection.
        """
        target_class = cls._resolve_target(target_path)
        original_fn = getattr(target_class, method_name, None)

        if original_fn is None:
            raise InjectionError(
                f"Method '{method_name}' not found on {target_path}."
            )

        @functools.wraps(original_fn)
        def injected_method(self, *args, **kwargs):
            return wrapper_fn(original_fn, self, *args, **kwargs)

        setattr(target_class, method_name, injected_method)

        record = _InjectionRecord(
            target_path=target_path,
            method_name=method_name,
            kind=kind,
            mod_id=mod_id,
            wrapper_fn=wrapper_fn,
            original_fn=original_fn,
            target_class=target_class,
        )
        cls._injections.append(record)
        return record

    @classmethod
    def revert(cls, record):
        """Revert a single injection, restoring the original method.

        Args:
            record: The _InjectionRecord returned by inject().
        """
        setattr(record.target_class, record.method_name, record.original_fn)
        cls._injections.remove(record)

    @classmethod
    def revert_all(cls, mod_id=None):
        """Revert all injections, optionally filtered by mod_id.

        Args:
            mod_id: If provided, only revert injections from this mod.
                    If None, revert everything.
        """
        to_revert = [
            r for r in cls._injections
            if mod_id is None or r.mod_id == mod_id
        ]
        for record in reversed(to_revert):  # Revert in reverse order
            setattr(record.target_class, record.method_name, record.original_fn)
            cls._injections.remove(record)

    @classmethod
    def list_injections(cls, mod_id=None):
        """List all active injections.

        Args:
            mod_id: If provided, filter to this mod only.

        Returns:
            List of dicts with injection details.
        """
        results = []
        for r in cls._injections:
            if mod_id and r.mod_id != mod_id:
                continue
            results.append({
                "target": r.target_path,
                "method": r.method_name,
                "kind": r.kind,
                "mod_id": r.mod_id,
            })
        return results

    @classmethod
    def clear(cls):
        """Remove all injection records. For testing only."""
        cls._injections.clear()


# ── Decorator API ────────────────────────────────────────────────────


def inject_before(target_path, method_name, mod_id=None):
    """Decorator: inject a wrapper that runs BEFORE the original method.

    The wrapper receives (original, self, *args, **kwargs) and MUST call
    original(self, *args, **kwargs) to let the game method run.

    Example:
        @inject_before("sims.sim.Sim", "on_add", mod_id="my_mod")
        def before_add(original, self, *args, **kwargs):
            print("About to add sim!")
            return original(self, *args, **kwargs)
    """
    def decorator(fn):
        InjectionManager.inject(
            target_path, method_name, fn, kind="before", mod_id=mod_id
        )
        return fn
    return decorator


def inject_after(target_path, method_name, mod_id=None):
    """Decorator: inject a wrapper that runs AFTER the original method.

    The wrapper receives (original, self, *args, **kwargs). Call original
    first, then do your work.

    Example:
        @inject_after("sims.sim.Sim", "on_remove", mod_id="my_mod")
        def after_remove(original, self, *args, **kwargs):
            result = original(self, *args, **kwargs)
            print("Sim removed, cleaning up.")
            return result
    """
    def decorator(fn):
        InjectionManager.inject(
            target_path, method_name, fn, kind="after", mod_id=mod_id
        )
        return fn
    return decorator


def inject_replace(target_path, method_name, mod_id=None):
    """Decorator: fully replace a game method.

    You control whether the original runs. Use with caution -- this is the
    most likely to conflict with other mods.

    Example:
        @inject_replace("sims.sim_info.SimInfo", "get_name", mod_id="my_mod")
        def custom_name(original, self, *args, **kwargs):
            return f"[Modded] {original(self, *args, **kwargs)}"
    """
    def decorator(fn):
        InjectionManager.inject(
            target_path, method_name, fn, kind="replace", mod_id=mod_id
        )
        return fn
    return decorator
