"""Tests for the 3-tier settings engine."""

import json
import os
import pytest

from stark_framework.core.settings import Settings, Preset, _validate


# ── Validation ──────────────────────────────────────────────────────────


class TestValidation:
    def test_validate_bool_true(self):
        spec = {"type": "bool", "default": False}
        assert _validate(True, spec) is True
        assert _validate("true", spec) is True
        assert _validate("1", spec) is True
        assert _validate("yes", spec) is True

    def test_validate_bool_false(self):
        spec = {"type": "bool", "default": True}
        assert _validate(False, spec) is False
        assert _validate("false", spec) is False
        assert _validate("0", spec) is False

    def test_validate_int_clamped(self):
        spec = {"type": "int", "default": 5, "min": 1, "max": 10}
        assert _validate(7, spec) == 7
        assert _validate(0, spec) == 1
        assert _validate(100, spec) == 10
        assert _validate("3", spec) == 3

    def test_validate_float_clamped(self):
        spec = {"type": "float", "default": 1.0, "min": 0.0, "max": 5.0}
        assert _validate(2.5, spec) == 2.5
        assert _validate(-1.0, spec) == 0.0
        assert _validate(999.0, spec) == 5.0

    def test_validate_str(self):
        spec = {"type": "str", "default": "hello"}
        assert _validate("world", spec) == "world"
        assert _validate(42, spec) == "42"

    def test_validate_invalid_returns_default(self):
        spec = {"type": "int", "default": 5, "min": 0, "max": 10}
        assert _validate("not_a_number", spec) == 5

    def test_validate_list(self):
        spec = {"type": "list", "default": []}
        assert _validate([1, 2, 3], spec) == [1, 2, 3]
        assert _validate("not_a_list", spec) == []


# ── Preset Initialization ──────────────────────────────────────────────


class TestPresets:
    def test_standard_preset_uses_defaults(self, tmp_path):
        s = Settings(preset=Preset.STANDARD, config_dir=str(tmp_path))
        assert s.get("core.lifespan_multiplier") == 1.0
        assert s.get("core.death_enabled") is True
        assert s.get("core.career_pay_multiplier") == 1.0

    def test_casual_preset_overrides(self, tmp_path):
        s = Settings(preset=Preset.CASUAL, config_dir=str(tmp_path))
        assert s.get("core.lifespan_multiplier") == 2.0
        assert s.get("core.death_enabled") is False
        assert s.get("core.career_pay_multiplier") == 1.5
        assert s.get("core.motive_decay_multiplier") == 0.5

    def test_simulation_preset_overrides(self, tmp_path):
        s = Settings(preset=Preset.SIMULATION, config_dir=str(tmp_path))
        assert s.get("core.lifespan_multiplier") == 0.75
        assert s.get("core.career_pay_multiplier") == 0.8
        assert s.get("core.household_size_cap") == 10

    def test_switch_preset(self, tmp_path):
        s = Settings(preset=Preset.CASUAL, config_dir=str(tmp_path))
        assert s.get("core.death_enabled") is False

        s.set_preset(Preset.SIMULATION)
        assert s.get("core.death_enabled") is True
        assert s.get("core.lifespan_multiplier") == 0.75
        assert s.preset == Preset.SIMULATION


# ── Get / Set ───────────────────────────────────────────────────────────


class TestGetSet:
    def test_get_returns_validated(self, tmp_path):
        s = Settings(config_dir=str(tmp_path))
        assert s.get("core.aging_enabled") is True

    def test_get_unknown_key_returns_none(self, tmp_path):
        s = Settings(config_dir=str(tmp_path))
        assert s.get("nonexistent.key") is None

    def test_set_and_get(self, tmp_path):
        s = Settings(config_dir=str(tmp_path))
        s.set("core.lifespan_multiplier", 3.0)
        assert s.get("core.lifespan_multiplier") == 3.0

    def test_set_clamps_value(self, tmp_path):
        s = Settings(config_dir=str(tmp_path))
        s.set("core.lifespan_multiplier", 999.0)
        assert s.get("core.lifespan_multiplier") == 10.0

    def test_set_unknown_key(self, tmp_path):
        s = Settings(config_dir=str(tmp_path))
        result = s.set("nonexistent.key", 42)
        assert result is None

    def test_get_all(self, tmp_path):
        s = Settings(config_dir=str(tmp_path))
        all_settings = s.get_all()
        assert "core.lifespan_multiplier" in all_settings
        assert "core.aging_enabled" in all_settings
        assert len(all_settings) >= 10

    def test_list_keys(self, tmp_path):
        s = Settings(config_dir=str(tmp_path))
        core_keys = s.list_keys(prefix="core.")
        assert len(core_keys) >= 10
        assert all(k.startswith("core.") for k in core_keys)

    def test_list_all_keys(self, tmp_path):
        s = Settings(config_dir=str(tmp_path))
        all_keys = s.list_keys()
        assert len(all_keys) >= 10


# ── Mod Settings Registration ──────────────────────────────────────────


class TestModSettings:
    def test_register_and_read(self, tmp_path):
        s = Settings(config_dir=str(tmp_path))
        s.register_mod_settings("my_mod", {
            "tax_rate": {"type": "float", "default": 0.10, "min": 0.0, "max": 1.0},
            "enabled": {"type": "bool", "default": True},
        })
        assert s.get("my_mod.tax_rate") == 0.10
        assert s.get("my_mod.enabled") is True

    def test_set_mod_setting(self, tmp_path):
        s = Settings(config_dir=str(tmp_path))
        s.register_mod_settings("my_mod", {
            "tax_rate": {"type": "float", "default": 0.10, "min": 0.0, "max": 1.0},
        })
        s.set("my_mod.tax_rate", 0.5)
        assert s.get("my_mod.tax_rate") == 0.5


# ── Persistence ─────────────────────────────────────────────────────────


class TestPersistence:
    def test_save_and_load(self, tmp_path):
        s1 = Settings(config_dir=str(tmp_path))
        s1.set("core.lifespan_multiplier", 3.5)

        # Create a new Settings instance that loads from the same path
        s2 = Settings(config_dir=str(tmp_path))
        assert s2.get("core.lifespan_multiplier") == 3.5

    def test_only_saves_non_defaults(self, tmp_path):
        s = Settings(config_dir=str(tmp_path))
        s.set("core.lifespan_multiplier", 2.0)

        config_path = os.path.join(str(tmp_path), "stark_settings.json")
        with open(config_path) as f:
            data = json.load(f)

        # Should have the changed key but not all defaults
        assert "core.lifespan_multiplier" in data
        assert "core.aging_enabled" not in data  # unchanged from default

    def test_preset_persisted(self, tmp_path):
        s1 = Settings(preset=Preset.CASUAL, config_dir=str(tmp_path))
        s1.set("core.household_size_cap", 12)  # force a save

        s2 = Settings(config_dir=str(tmp_path))
        assert s2.preset == Preset.CASUAL


# ── Change Listeners ────────────────────────────────────────────────────


class TestListeners:
    def test_listener_fires_on_change(self, tmp_path):
        s = Settings(config_dir=str(tmp_path))
        changes = []
        s.on_change("core.lifespan_multiplier", lambda k, old, new: changes.append((k, old, new)))

        s.set("core.lifespan_multiplier", 2.0)

        assert len(changes) == 1
        assert changes[0] == ("core.lifespan_multiplier", 1.0, 2.0)

    def test_listener_not_fired_on_same_value(self, tmp_path):
        s = Settings(config_dir=str(tmp_path))
        changes = []
        s.on_change("core.aging_enabled", lambda k, old, new: changes.append(1))

        s.set("core.aging_enabled", True)  # same as default
        assert len(changes) == 0


# ── Migration ───────────────────────────────────────────────────────────


class TestMigration:
    def test_rename_setting(self, tmp_path):
        s = Settings(config_dir=str(tmp_path))
        # Simulate an old key
        s._values["old.key"] = 42
        s.register_mod_settings("new", {"key": {"type": "int", "default": 0}})

        count = s.migrate(renames={"old.key": "new.key"})
        assert count == 1
        assert s.get("new.key") == 42

    def test_remove_setting(self, tmp_path):
        s = Settings(config_dir=str(tmp_path))
        s._values["deprecated.key"] = "old_value"

        count = s.migrate(removals=["deprecated.key"])
        assert count == 1
        assert "deprecated.key" not in s._values
