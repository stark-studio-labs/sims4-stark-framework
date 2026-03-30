"""
Settings Engine -- 3-tier preset system with typed config and persistence.

Inspired by MCCC's 682-getter settings architecture, but designed for
clarity instead of obfuscation.  Provides:

  - Three built-in presets: CASUAL, STANDARD, SIMULATION
  - Typed setting definitions with validation, min/max bounds, and defaults
  - Per-mod setting namespaces to avoid collisions
  - JSON persistence to the Sims 4 mod data directory
  - Migration support for renamed/removed settings across versions

Presets:
    CASUAL      -- relaxed gameplay, longer lifespans, less punishing economy
    STANDARD    -- EA defaults, balanced gameplay (the default)
    SIMULATION  -- hardcore realism, shorter lifespans, tight economy, more drama

Usage:
    from stark_framework.core.settings import Settings, Preset

    # Initialize with a preset
    settings = Settings(preset=Preset.STANDARD)

    # Read a setting (typed, cached, validated)
    lifespan = settings.get("core.lifespan_multiplier")

    # Write a setting (persisted, validated, notifies listeners)
    settings.set("core.lifespan_multiplier", 1.5)

    # Register a mod's custom settings
    settings.register_mod_settings("my_economy_mod", {
        "tax_rate": {"type": "float", "default": 0.10, "min": 0.0, "max": 1.0},
        "payday_bonus": {"type": "int", "default": 0, "min": 0, "max": 10000},
    })

    # Read mod settings
    rate = settings.get("my_economy_mod.tax_rate")

    # Subscribe to setting changes
    settings.on_change("core.lifespan_multiplier", my_callback)
"""

import json
import os
from enum import Enum

from stark_framework.utils.logging import get_logger

log = get_logger("stark.core.settings")


class Preset(Enum):
    """Built-in difficulty / playstyle presets."""
    CASUAL = "casual"
    STANDARD = "standard"
    SIMULATION = "simulation"


# ── Preset Definitions ──────────────────────────────────────────────────
# Each preset defines overrides on top of the STANDARD baseline.

_CORE_DEFAULTS = {
    "core.lifespan_multiplier": {
        "type": "float", "default": 1.0, "min": 0.1, "max": 10.0,
        "description": "Multiplier applied to all age durations.",
    },
    "core.aging_enabled": {
        "type": "bool", "default": True,
        "description": "Whether Sims age at all.",
    },
    "core.auto_bills": {
        "type": "bool", "default": True,
        "description": "Whether household bills are processed automatically.",
    },
    "core.career_pay_multiplier": {
        "type": "float", "default": 1.0, "min": 0.0, "max": 5.0,
        "description": "Multiplier on career pay (applied via funds hook).",
    },
    "core.relationship_decay_rate": {
        "type": "float", "default": 1.0, "min": 0.0, "max": 3.0,
        "description": "Multiplier on relationship decay speed.",
    },
    "core.household_size_cap": {
        "type": "int", "default": 8, "min": 1, "max": 25,
        "description": "Maximum number of Sims per household.",
    },
    "core.npc_story_progression": {
        "type": "bool", "default": True,
        "description": "Whether NPC households progress (age, marry, etc.).",
    },
    "core.autonomous_actions": {
        "type": "bool", "default": True,
        "description": "Whether Sims perform autonomous interactions.",
    },
    "core.death_enabled": {
        "type": "bool", "default": True,
        "description": "Whether Sims can die from non-old-age causes.",
    },
    "core.motive_decay_multiplier": {
        "type": "float", "default": 1.0, "min": 0.0, "max": 3.0,
        "description": "Speed of need/motive decay.",
    },
}

_CASUAL_OVERRIDES = {
    "core.lifespan_multiplier": 2.0,
    "core.career_pay_multiplier": 1.5,
    "core.relationship_decay_rate": 0.5,
    "core.death_enabled": False,
    "core.motive_decay_multiplier": 0.5,
}

_SIMULATION_OVERRIDES = {
    "core.lifespan_multiplier": 0.75,
    "core.career_pay_multiplier": 0.8,
    "core.relationship_decay_rate": 1.5,
    "core.household_size_cap": 10,
    "core.motive_decay_multiplier": 1.3,
}


# ── Type Validators ─────────────────────────────────────────────────────

def _validate(value, spec):
    """Validate and coerce a value against a setting spec.

    Returns the validated value, or the spec default on failure.
    """
    expected_type = spec.get("type", "str")
    default = spec.get("default")

    try:
        if expected_type == "bool":
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes")
            return bool(value)

        if expected_type == "int":
            v = int(value)
            v = max(v, spec.get("min", v))
            v = min(v, spec.get("max", v))
            return v

        if expected_type == "float":
            v = float(value)
            v = max(v, spec.get("min", v))
            v = min(v, spec.get("max", v))
            return v

        if expected_type == "str":
            return str(value)

        if expected_type == "list":
            if isinstance(value, list):
                return value
            return default

    except (ValueError, TypeError):
        pass

    return default


# ── Settings Class ──────────────────────────────────────────────────────


class Settings:
    """Typed, preset-aware settings engine with persistence.

    Args:
        preset: Initial preset (default STANDARD).
        config_dir: Path to save/load config JSON.  Defaults to the current
                    working directory.  In-game, pass the mod data folder.
    """

    def __init__(self, preset=Preset.STANDARD, config_dir=None):
        self._specs = dict(_CORE_DEFAULTS)  # key -> spec dict
        self._values = {}                    # key -> current value
        self._cache = {}                     # key -> validated value
        self._listeners = {}                 # key -> [callback, ...]
        self._preset = preset
        self._config_dir = config_dir or os.getcwd()
        self._config_path = os.path.join(self._config_dir, "stark_settings.json")

        # Initialize defaults
        for key, spec in self._specs.items():
            self._values[key] = spec["default"]

        # Apply preset overrides
        self._apply_preset(preset)

        # Load persisted overrides (if file exists)
        self._load()

    # ── Preset Management ────────────────────────────────────────────

    def _apply_preset(self, preset):
        """Apply a preset's overrides on top of defaults."""
        overrides = {}
        if preset == Preset.CASUAL:
            overrides = _CASUAL_OVERRIDES
        elif preset == Preset.SIMULATION:
            overrides = _SIMULATION_OVERRIDES
        # STANDARD uses defaults -- no overrides

        for key, value in overrides.items():
            if key in self._specs:
                self._values[key] = value

        self._cache.clear()

    def set_preset(self, preset):
        """Switch to a new preset, resetting all core settings.

        Mod-registered settings are not affected.
        """
        self._preset = preset
        # Reset core settings to defaults first
        for key, spec in _CORE_DEFAULTS.items():
            self._values[key] = spec["default"]
        self._apply_preset(preset)
        self._save()
        log.info("Preset applied", preset=preset.value)

    @property
    def preset(self):
        """The currently active preset."""
        return self._preset

    # ── Read / Write ─────────────────────────────────────────────────

    def get(self, key):
        """Get a setting value (validated and cached).

        Args:
            key: Setting key (e.g. "core.lifespan_multiplier").

        Returns:
            The validated setting value, or None if key is unknown.
        """
        if key in self._cache:
            return self._cache[key]

        spec = self._specs.get(key)
        if spec is None:
            log.warn("Unknown setting key", key=key)
            return None

        raw = self._values.get(key, spec.get("default"))
        validated = _validate(raw, spec)
        self._cache[key] = validated
        return validated

    def set(self, key, value):
        """Set a setting value (validated, persisted, notifies listeners).

        Args:
            key: Setting key.
            value: New value (will be validated against the spec).

        Returns:
            The validated value that was actually stored.
        """
        spec = self._specs.get(key)
        if spec is None:
            log.warn("Cannot set unknown setting", key=key)
            return None

        validated = _validate(value, spec)
        old = self._values.get(key)
        self._values[key] = validated
        self._cache.pop(key, None)

        if old != validated:
            self._save()
            self._notify(key, old, validated)
            log.info("Setting changed", key=key, old=old, new=validated)

        return validated

    def get_all(self):
        """Return all settings as a dict of {key: validated_value}."""
        return {key: self.get(key) for key in self._specs}

    def get_spec(self, key):
        """Return the spec dict for a setting key, or None."""
        return self._specs.get(key)

    def list_keys(self, prefix=None):
        """List all setting keys, optionally filtered by prefix.

        Args:
            prefix: e.g. "core." or "my_mod."

        Returns:
            List of matching keys.
        """
        if prefix:
            return [k for k in self._specs if k.startswith(prefix)]
        return list(self._specs.keys())

    # ── Mod Settings Registration ────────────────────────────────────

    def register_mod_settings(self, mod_id, definitions):
        """Register custom settings for a mod.

        Args:
            mod_id: The mod's unique identifier (used as namespace prefix).
            definitions: Dict of {setting_name: spec_dict}.

        Each spec_dict should have at minimum ``type`` and ``default``.
        Supported types: "bool", "int", "float", "str", "list".

        Example:
            settings.register_mod_settings("my_mod", {
                "tax_rate": {"type": "float", "default": 0.10, "min": 0.0, "max": 1.0},
                "enabled": {"type": "bool", "default": True},
            })
        """
        for name, spec in definitions.items():
            key = f"{mod_id}.{name}"
            if key in self._specs:
                log.warn("Overwriting existing setting spec", key=key)
            self._specs[key] = spec
            if key not in self._values:
                self._values[key] = spec.get("default")

        log.info("Mod settings registered", mod_id=mod_id, count=len(definitions))

    # ── Change Listeners ─────────────────────────────────────────────

    def on_change(self, key, callback):
        """Subscribe to changes for a specific setting.

        Args:
            key: Setting key to watch.
            callback: Called with (key, old_value, new_value) on change.
        """
        self._listeners.setdefault(key, []).append(callback)

    def _notify(self, key, old_value, new_value):
        """Notify listeners of a setting change."""
        for callback in self._listeners.get(key, []):
            try:
                callback(key, old_value, new_value)
            except Exception as exc:
                log.error(
                    "Setting change listener error",
                    key=key, error=str(exc),
                )

    # ── Persistence ──────────────────────────────────────────────────

    def _save(self):
        """Persist current settings to JSON."""
        try:
            data = {
                "_preset": self._preset.value,
                "_version": 1,
            }
            # Only save values that differ from spec defaults
            for key, value in self._values.items():
                spec = self._specs.get(key, {})
                if value != spec.get("default"):
                    data[key] = value

            os.makedirs(os.path.dirname(self._config_path) or ".", exist_ok=True)
            with open(self._config_path, "w") as f:
                json.dump(data, f, indent=2, default=str)

        except Exception as exc:
            log.error("Failed to save settings", error=str(exc))

    def _load(self):
        """Load persisted settings from JSON."""
        if not os.path.exists(self._config_path):
            return

        try:
            with open(self._config_path, "r") as f:
                data = json.load(f)

            # Restore preset if saved
            saved_preset = data.pop("_preset", None)
            data.pop("_version", None)

            if saved_preset:
                try:
                    self._preset = Preset(saved_preset)
                    self._apply_preset(self._preset)
                except ValueError:
                    pass

            # Apply saved overrides
            for key, value in data.items():
                if key in self._specs:
                    self._values[key] = _validate(value, self._specs[key])

            self._cache.clear()
            log.info("Settings loaded", path=self._config_path)

        except Exception as exc:
            log.error("Failed to load settings, using defaults", error=str(exc))

    # ── Migration ────────────────────────────────────────────────────

    def migrate(self, renames=None, removals=None):
        """Migrate settings across version changes.

        Modeled after MCCC's _alter_obsolete_settings -- renames old keys
        and removes deprecated keys from the persisted config.

        Args:
            renames: Dict of {old_key: new_key} to migrate.
            removals: List of keys to remove.

        Returns:
            Number of changes applied.
        """
        changes = 0
        renames = renames or {}
        removals = removals or []

        for old_key, new_key in renames.items():
            if old_key in self._values and new_key in self._specs:
                self._values[new_key] = self._values.pop(old_key)
                self._cache.pop(old_key, None)
                self._cache.pop(new_key, None)
                changes += 1
                log.info("Setting migrated", old_key=old_key, new_key=new_key)

        for key in removals:
            if key in self._values:
                self._values.pop(key, None)
                self._cache.pop(key, None)
                changes += 1
                log.info("Setting removed", key=key)

        if changes > 0:
            self._save()

        return changes
