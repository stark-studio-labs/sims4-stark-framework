"""
Game Hooks -- pre-built injections targeting real Sims 4 class methods.

These hooks are derived from bytecode analysis of how production mods (MCCC,
S4CL, etc.) interface with the game engine.  Each module targets a specific
domain of the game runtime and fires Stark Framework events that downstream
mods can subscribe to.

Modules:
    sim_hooks       -- SimInfo / Sim lifecycle (age-up, trait changes, spawn/despawn)
    zone_hooks      -- Zone spin-up, loading screen transitions, lot readiness
    instance_hooks  -- InstanceManager.load_data_into_class_instances (tuning load)
    funds_hooks     -- _Funds.add / career pay interception

Usage:
    # Import the hooks you need -- they auto-register on import.
    from stark_framework.game_hooks import sim_hooks
    from stark_framework.game_hooks import zone_hooks

    # Then subscribe to the events they publish:
    from stark_framework.core.events import EventBus

    @EventBus.on(sim_hooks.SimAgeChangedEvent)
    def on_age_change(event):
        print(f"Sim {event.sim_id} aged from {event.old_age} to {event.new_age}")
"""
