"""Type stubs for zone.Zone -- the game's per-lot runtime container."""

from typing import Any, Optional


class Zone:
    """Represents a loaded game zone (lot + surrounding area).

    Key lifecycle methods that mods commonly hook:
        do_zone_spin_up()                        -- lot loading begins
        on_loading_screen_animation_finished()   -- lot fully loaded, gameplay starts
        on_cleanup_zone_objects()                 -- lot unloading / travel / quit
    """
    id: int
    world_id: int
    lot: Any
    is_zone_loading: bool
    is_zone_running: bool

    def do_zone_spin_up(self) -> None: ...
    def on_loading_screen_animation_finished(self) -> None: ...
    def on_cleanup_zone_objects(self) -> None: ...
    def on_teardown(self) -> None: ...
