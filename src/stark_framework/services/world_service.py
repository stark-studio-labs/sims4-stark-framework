"""
World Service -- helpers for world, lot, and zone access.

Wraps the game's zone and lot systems with a clean API for querying the
current world state, finding lots, and working with zones.

Usage:
    from stark_framework.services.world_service import WorldService

    # Get current zone info
    zone = WorldService.get_current_zone()
    if zone:
        print(f"Current zone ID: {WorldService.get_zone_id(zone)}")

    # Check if a lot is residential
    if WorldService.is_residential_lot():
        print("On a residential lot")

    # Get all objects on the current lot
    objects = WorldService.get_lot_objects()
    print(f"{len(objects)} objects on this lot")
"""

from stark_framework.utils.logging import get_logger

log = get_logger("stark.services.world")


class WorldService:
    """Typed helpers for world, lot, and zone access."""

    @staticmethod
    def get_current_zone():
        """Get the current active zone.

        Returns:
            Zone object, or None.

        Example:
            zone = WorldService.get_current_zone()
            if zone:
                lot = WorldService.get_current_lot()
        """
        try:
            import services
            return services.current_zone()
        except (ImportError, AttributeError):
            log.warn("Zone not available (not in game?)")
            return None

    @staticmethod
    def get_zone_id(zone=None):
        """Get the zone ID for a zone (defaults to current).

        Args:
            zone: Optional Zone object. Uses current zone if None.

        Returns:
            Zone ID (int), or None.
        """
        if zone is None:
            zone = WorldService.get_current_zone()
        if zone is None:
            return None
        return getattr(zone, "id", None)

    @staticmethod
    def get_current_lot():
        """Get the current lot object.

        Returns:
            Lot object, or None.

        Example:
            lot = WorldService.get_current_lot()
            if lot:
                print(f"Lot size: {WorldService.get_lot_size(lot)}")
        """
        try:
            import services
            zone = services.current_zone()
            if zone is None:
                return None
            return getattr(zone, "lot", None)
        except (ImportError, AttributeError):
            return None

    @staticmethod
    def get_lot_objects(lot=None):
        """Get all game objects on a lot.

        Args:
            lot: Optional Lot object. Uses current lot if None.

        Returns:
            List of game objects, or empty list.

        Example:
            for obj in WorldService.get_lot_objects():
                print(f"Object: {obj.__class__.__name__}")
        """
        try:
            import services
            object_manager = services.object_manager()
            if object_manager is None:
                return []
            return list(object_manager.get_all())
        except (ImportError, AttributeError):
            return []

    @staticmethod
    def is_residential_lot():
        """Check if the current lot is residential.

        Returns:
            True if residential, False otherwise.

        Example:
            if WorldService.is_residential_lot():
                enable_home_features()
        """
        try:
            import services
            zone = services.current_zone()
            if zone is None:
                return False
            lot = getattr(zone, "lot", None)
            if lot is None:
                return False
            return getattr(lot, "is_residential", False)
        except (ImportError, AttributeError):
            return False

    @staticmethod
    def get_world_id():
        """Get the current world/neighborhood ID.

        Returns:
            World ID (int), or None.
        """
        try:
            import services
            zone = services.current_zone()
            if zone is None:
                return None
            return getattr(zone, "world_id", None)
        except (ImportError, AttributeError):
            return None

    @staticmethod
    def get_sims_on_lot():
        """Get all Sims currently on the active lot.

        Returns:
            List of Sim objects (instanced sims, not SimInfo), or empty list.

        Example:
            sims_here = WorldService.get_sims_on_lot()
            print(f"{len(sims_here)} sims on this lot right now")
        """
        try:
            import services
            sim_info_manager = services.sim_info_manager()
            if sim_info_manager is None:
                return []
            instanced = []
            for sim_info in sim_info_manager.instanced_sims_gen():
                if sim_info.is_on_active_lot():
                    instanced.append(sim_info)
            return instanced
        except (ImportError, AttributeError):
            return []

    @staticmethod
    def get_lot_size(lot=None):
        """Get the lot size tuple (width, height) if available.

        Args:
            lot: Optional Lot object. Uses current lot if None.

        Returns:
            Tuple (width, height), or None.
        """
        if lot is None:
            lot = WorldService.get_current_lot()
        if lot is None:
            return None
        size_x = getattr(lot, "size_x", None)
        size_z = getattr(lot, "size_z", None)
        if size_x is not None and size_z is not None:
            return (size_x, size_z)
        return None
