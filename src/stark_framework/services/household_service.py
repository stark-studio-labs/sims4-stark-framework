"""
Household Service -- helpers for household management.

Wraps the game's HouseholdManager with a clean API for common operations
like listing household members, checking funds, and finding households.

Usage:
    from stark_framework.services.household_service import HouseholdService

    # Get the active household
    household = HouseholdService.get_active_household()
    if household:
        print(f"Funds: {HouseholdService.get_funds(household)}")

    # List household members
    for sim_info in HouseholdService.get_members(household):
        print(sim_info.first_name)

    # Get all households
    for hh in HouseholdService.get_all_households():
        print(f"{HouseholdService.get_name(hh)}: {HouseholdService.member_count(hh)} sims")
"""

from stark_framework.utils.logging import get_logger

log = get_logger("stark.services.household")


class HouseholdService:
    """Typed helpers for household data access."""

    @staticmethod
    def get_active_household():
        """Get the currently active (player-controlled) household.

        Returns:
            Household object, or None.

        Example:
            hh = HouseholdService.get_active_household()
            if hh:
                print(f"Playing as the {HouseholdService.get_name(hh)} household")
        """
        try:
            import services
            return services.active_household()
        except (ImportError, AttributeError):
            log.warn("Active household not available (not in game?)")
            return None

    @staticmethod
    def get_household(household_id):
        """Get a household by its ID.

        Args:
            household_id: The household's instance ID.

        Returns:
            Household object, or None.
        """
        try:
            import services
            household_manager = services.household_manager()
            if household_manager is None:
                return None
            return household_manager.get(household_id)
        except (ImportError, AttributeError):
            return None

    @staticmethod
    def get_all_households():
        """Get all households in the current save.

        Returns:
            List of Household objects, or empty list.
        """
        try:
            import services
            household_manager = services.household_manager()
            if household_manager is None:
                return []
            return list(household_manager.get_all())
        except (ImportError, AttributeError):
            return []

    @staticmethod
    def get_members(household):
        """Get all SimInfo objects in a household.

        Args:
            household: A Household object.

        Returns:
            List of SimInfo objects, or empty list.

        Example:
            members = HouseholdService.get_members(household)
            for sim_info in members:
                print(f"  - {sim_info.first_name} {sim_info.last_name}")
        """
        try:
            return list(household.sim_info_gen())
        except (AttributeError, TypeError):
            return []

    @staticmethod
    def member_count(household):
        """Get the number of Sims in a household.

        Args:
            household: A Household object.

        Returns:
            Integer count.
        """
        try:
            return len(list(household.sim_info_gen()))
        except (AttributeError, TypeError):
            return 0

    @staticmethod
    def get_name(household):
        """Get the household's display name.

        Args:
            household: A Household object.

        Returns:
            Household name string, or "Unknown Household".
        """
        return getattr(household, "name", "Unknown Household")

    @staticmethod
    def get_funds(household):
        """Get the household's current Simoleon balance.

        Args:
            household: A Household object.

        Returns:
            Integer balance, or 0.

        Example:
            funds = HouseholdService.get_funds(household)
            print(f"The {HouseholdService.get_name(household)} family has {funds} Simoleons")
        """
        try:
            funds = getattr(household, "funds", None)
            if funds is None:
                return 0
            return getattr(funds, "money", 0)
        except AttributeError:
            return 0

    @staticmethod
    def get_home_lot_id(household):
        """Get the lot ID of the household's home.

        Args:
            household: A Household object.

        Returns:
            Lot ID (int), or None if homeless.
        """
        return getattr(household, "home_zone_id", None)
