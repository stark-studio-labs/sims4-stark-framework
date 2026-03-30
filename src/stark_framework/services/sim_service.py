"""
Sim Service -- typed helpers for accessing and manipulating Sim data.

Wraps the game's SimInfo and Sim objects with a clean API that handles
None checks, missing attributes, and common patterns that every mod needs.

Usage:
    from stark_framework.services.sim_service import SimService

    # Get all Sims in the current world
    all_sims = SimService.get_all_sim_infos()

    # Get a specific Sim by ID
    sim_info = SimService.get_sim_info(sim_id=12345)
    if sim_info:
        print(SimService.get_full_name(sim_info))

    # Check Sim state
    if SimService.is_teen_or_older(sim_info):
        print("Can apply adult interactions")

    # Get active Sim
    active = SimService.get_active_sim_info()
"""

from stark_framework.utils.logging import get_logger

log = get_logger("stark.services.sim")


class SimService:
    """Typed helpers for Sim data access.

    All methods handle missing game modules gracefully -- they return None
    or empty lists when called outside the game environment.
    """

    @staticmethod
    def get_all_sim_infos():
        """Get all SimInfo objects in the current save.

        Returns:
            List of SimInfo objects, or empty list if unavailable.

        Example:
            for sim_info in SimService.get_all_sim_infos():
                print(SimService.get_full_name(sim_info))
        """
        try:
            import services
            sim_info_manager = services.sim_info_manager()
            if sim_info_manager is None:
                return []
            return list(sim_info_manager.get_all())
        except (ImportError, AttributeError):
            log.warn("SimInfoManager not available (not in game?)")
            return []

    @staticmethod
    def get_sim_info(sim_id):
        """Get a SimInfo by its instance ID.

        Args:
            sim_id: The Sim's instance ID.

        Returns:
            SimInfo object, or None if not found.

        Example:
            info = SimService.get_sim_info(12345)
            if info:
                print(f"Found: {SimService.get_full_name(info)}")
        """
        try:
            import services
            sim_info_manager = services.sim_info_manager()
            if sim_info_manager is None:
                return None
            return sim_info_manager.get(sim_id)
        except (ImportError, AttributeError):
            return None

    @staticmethod
    def get_active_sim_info():
        """Get the currently active (player-controlled) Sim's info.

        Returns:
            SimInfo for the active Sim, or None.

        Example:
            active = SimService.get_active_sim_info()
            if active:
                print(f"Playing as {SimService.get_full_name(active)}")
        """
        try:
            import services
            client = services.client_manager().get_first_client()
            if client is None:
                return None
            active_sim = client.active_sim
            if active_sim is None:
                return None
            return active_sim.sim_info
        except (ImportError, AttributeError):
            return None

    @staticmethod
    def get_full_name(sim_info):
        """Get a Sim's full name as a string.

        Args:
            sim_info: A SimInfo object.

        Returns:
            "FirstName LastName" string, or "Unknown Sim" on failure.

        Example:
            name = SimService.get_full_name(sim_info)
            print(f"Hello, {name}!")
        """
        try:
            first = getattr(sim_info, "first_name", "")
            last = getattr(sim_info, "last_name", "")
            return f"{first} {last}".strip() or "Unknown Sim"
        except Exception:
            return "Unknown Sim"

    @staticmethod
    def get_age(sim_info):
        """Get a Sim's age enum value.

        Args:
            sim_info: A SimInfo object.

        Returns:
            Age enum value, or None.

        Example:
            age = SimService.get_age(sim_info)
            if age == Age.ELDER:
                print("This sim is elderly")
        """
        return getattr(sim_info, "age", None)

    @staticmethod
    def is_teen_or_older(sim_info):
        """Check if a Sim is Teen age or older.

        Useful for gating interactions that shouldn't apply to children.

        Args:
            sim_info: A SimInfo object.

        Returns:
            True if Teen, Young Adult, Adult, or Elder. False otherwise.
        """
        try:
            from sims.sim_info_types import Age
            age = getattr(sim_info, "age", None)
            if age is None:
                return False
            return age >= Age.TEEN
        except ImportError:
            return False

    @staticmethod
    def get_household_id(sim_info):
        """Get the household ID for a Sim.

        Args:
            sim_info: A SimInfo object.

        Returns:
            Household ID (int), or None.
        """
        return getattr(sim_info, "household_id", None)

    @staticmethod
    def get_traits(sim_info):
        """Get all traits on a Sim.

        Args:
            sim_info: A SimInfo object.

        Returns:
            List of trait objects, or empty list.

        Example:
            for trait in SimService.get_traits(sim_info):
                print(f"Trait: {trait.__class__.__name__}")
        """
        try:
            trait_tracker = getattr(sim_info, "trait_tracker", None)
            if trait_tracker is None:
                return []
            return list(trait_tracker.equipped_traits)
        except (AttributeError, TypeError):
            return []
