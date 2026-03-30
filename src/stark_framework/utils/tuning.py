"""
XML Tuning Helpers -- utilities for working with Sims 4 tuning data.

The Sims 4 uses XML tuning files to define game data (traits, buffs, interactions,
etc.). These helpers make it easier to look up tuning by ID or name, read tuning
values, and work with the game's instance manager.

Usage:
    from stark_framework.utils.tuning import TuningHelper

    # Look up a tuning instance by its numeric ID
    trait = TuningHelper.get_tuning(manager_type="TRAIT", tuning_id=0x1A2B3C4D)
    if trait:
        print(f"Found trait: {trait.__name__}")

    # Look up by string name (slower, searches all instances)
    buff = TuningHelper.find_tuning_by_name(manager_type="BUFF", name="Buff_Happy")

    # Get all tuning instances of a type
    all_traits = TuningHelper.get_all_tuning(manager_type="TRAIT")
    print(f"Game has {len(all_traits)} traits loaded")

    # Convert a tuning name to its hash (game uses FNV32 hashing)
    hash_val = TuningHelper.fnv32("my_custom_trait")
"""

from stark_framework.utils.logging import get_logger

log = get_logger("stark.utils.tuning")


def fnv32(name):
    """Compute FNV-1 32-bit hash of a tuning name.

    The Sims 4 uses FNV32 to convert XML tuning filenames to numeric IDs.
    This is useful when you need to reference tuning by name but the game
    API expects a numeric ID.

    Args:
        name: The tuning name string (case-insensitive, lowercased before hashing).

    Returns:
        Integer hash value.

    Example:
        tuning_id = fnv32("buff_happy")
        print(f"Hash: 0x{tuning_id:08X}")
    """
    # FNV-1 32-bit
    FNV_PRIME = 0x01000193
    FNV_OFFSET = 0x811C9DC5

    h = FNV_OFFSET
    for byte in name.lower().encode("utf-8"):
        h = (h * FNV_PRIME) & 0xFFFFFFFF
        h = h ^ byte
    return h


def fnv64(name):
    """Compute FNV-1 64-bit hash of a tuning name.

    Some tuning types use 64-bit hashes instead of 32-bit.

    Args:
        name: The tuning name string.

    Returns:
        Integer hash value.

    Example:
        tuning_id = fnv64("my_custom_interaction")
        print(f"Hash: 0x{tuning_id:016X}")
    """
    FNV_PRIME = 0x00000100000001B3
    FNV_OFFSET = 0xCBF29CE484222325

    h = FNV_OFFSET
    for byte in name.lower().encode("utf-8"):
        h = (h * FNV_PRIME) & 0xFFFFFFFFFFFFFFFF
        h = h ^ byte
    return h


class TuningHelper:
    """Helpers for looking up and working with game tuning data."""

    # Map of friendly names to game InstanceManager types
    MANAGER_TYPES = {
        "TRAIT": "TRAIT",
        "BUFF": "BUFF",
        "INTERACTION": "INTERACTION",
        "OBJECT": "OBJECT",
        "SIM_INFO": "SIM_INFO",
        "SITUATION": "SITUATION",
        "ASPIRATION": "ASPIRATION",
        "CAREER": "CAREER",
        "SKILL": "SKILL",
        "LOT_TUNING": "LOT_TUNING",
        "RECIPE": "RECIPE",
    }

    @classmethod
    def get_instance_manager(cls, manager_type):
        """Get the InstanceManager for a tuning type.

        Args:
            manager_type: One of the MANAGER_TYPES keys (e.g. "TRAIT", "BUFF").

        Returns:
            InstanceManager object, or None.
        """
        try:
            import services
            from sims4.resources import Types
            type_enum = getattr(Types, manager_type, None)
            if type_enum is None:
                log.error("Unknown manager type", manager_type=manager_type)
                return None
            return services.get_instance_manager(type_enum)
        except (ImportError, AttributeError):
            log.warn("Instance managers not available (not in game?)")
            return None

    @classmethod
    def get_tuning(cls, manager_type, tuning_id):
        """Look up a tuning instance by its numeric ID.

        Args:
            manager_type: Tuning type (e.g. "TRAIT", "BUFF").
            tuning_id: The numeric instance ID (can be hex like 0x1A2B3C4D).

        Returns:
            The tuning instance, or None if not found.

        Example:
            trait = TuningHelper.get_tuning("TRAIT", 0x1A2B3C4D)
            if trait:
                print(f"Found: {trait.__name__}")
        """
        manager = cls.get_instance_manager(manager_type)
        if manager is None:
            return None
        try:
            return manager.get(tuning_id)
        except Exception:
            return None

    @classmethod
    def find_tuning_by_name(cls, manager_type, name):
        """Search for a tuning instance by its class/tuning name.

        This is slower than get_tuning() because it iterates all instances.
        Use for debugging or one-time lookups, not hot paths.

        Args:
            manager_type: Tuning type (e.g. "TRAIT", "BUFF").
            name: The tuning name to search for (case-insensitive).

        Returns:
            The first matching tuning instance, or None.

        Example:
            buff = TuningHelper.find_tuning_by_name("BUFF", "Buff_Happy")
        """
        manager = cls.get_instance_manager(manager_type)
        if manager is None:
            return None
        name_lower = name.lower()
        try:
            for key, instance in manager.types.items():
                instance_name = getattr(instance, "__name__", "")
                if instance_name.lower() == name_lower:
                    return instance
        except (AttributeError, TypeError):
            pass
        return None

    @classmethod
    def get_all_tuning(cls, manager_type):
        """Get all tuning instances of a given type.

        Args:
            manager_type: Tuning type (e.g. "TRAIT", "BUFF").

        Returns:
            List of tuning instances, or empty list.

        Example:
            all_skills = TuningHelper.get_all_tuning("SKILL")
            for skill in all_skills:
                print(skill.__name__)
        """
        manager = cls.get_instance_manager(manager_type)
        if manager is None:
            return []
        try:
            return list(manager.types.values())
        except (AttributeError, TypeError):
            return []

    @staticmethod
    def fnv32(name):
        """Compute FNV-1 32-bit hash. Convenience wrapper.

        Args:
            name: Tuning name string.

        Returns:
            Integer hash.
        """
        return fnv32(name)

    @staticmethod
    def fnv64(name):
        """Compute FNV-1 64-bit hash. Convenience wrapper.

        Args:
            name: Tuning name string.

        Returns:
            Integer hash.
        """
        return fnv64(name)
