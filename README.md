<div align="center">

# Stark Framework

**A modern, typed modding framework for The Sims 4.**

*Clean architecture. Zero monkey-patching. First-class developer experience.*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)]()
[![Tests](https://img.shields.io/badge/tests-80%20passing-brightgreen)]()
[![Made by Stark Studio Labs](https://img.shields.io/badge/made%20by-Stark%20Studio%20Labs-blueviolet)](https://github.com/stark-studio-labs)

*Built by [Stark Studio Labs](https://github.com/stark-studio-labs)*

</div>

---

## Stark Labs Ecosystem

> Everything we build for The Sims 4 modding community -- open source, interconnected, and community-driven.

| Repo | What It Does | Status |
|------|-------------|--------|
| **[awesome-sims4-mods](https://github.com/stark-studio-labs/awesome-sims4-mods)** | Curated mod directory with compatibility tracking | Active |
| **[sims4-stark-framework](https://github.com/stark-studio-labs/sims4-stark-framework)** | Modern typed modding framework (replaces S4CL patterns) | Active |
| **[sims4-stark-devkit](https://github.com/stark-studio-labs/sims4-stark-devkit)** | CLI toolkit -- decompile, package, scaffold, test | Active |
| **[sims4-mod-manager](https://github.com/stark-studio-labs/sims4-mod-manager)** | Scan, organize, and detect conflicts in your mod collection | Alpha |
| **[sims4-mod-builder](https://github.com/stark-studio-labs/sims4-mod-builder)** | Visual mod creation tool -- no XML knowledge needed | In Dev |
| **[sims4-mod-revival](https://github.com/stark-studio-labs/sims4-mod-revival)** | Decompile and revive abandoned community mods | Active |
| **[sims4-economy-sim](https://github.com/stark-studio-labs/sims4-economy-sim)** | Banking, bills, jobs, and stock market overhaul mod | Pre-Alpha |

---

## Table of Contents

- [Honest Comparison: Stark vs S4CL vs Raw Modding](#honest-comparison-stark-vs-s4cl-vs-raw-modding)
- [How It Compares](#️-how-it-compares)
- [Roadmap](#️-roadmap)
- [The Problem](#the-problem)
- [The Stark Way](#the-stark-way)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
  - [Events](#events)
  - [Injection](#injection)
  - [Registry](#registry)
  - [Diagnostics](#diagnostics)
  - [Services](#services)
  - [Settings](#settings)
  - [Scheduler](#scheduler)
  - [Game Hooks](#game-hooks)
  - [Type Stubs](#type-stubs)
  - [Logging](#logging)
- [Architecture](#architecture)
- [S4CL Compatibility](#s4cl-compatibility)
- [For Framework Contributors](#for-framework-contributors)

---

## Honest Comparison: Stark vs S4CL vs Raw Modding

We believe in honest tools.  Here is where each approach actually stands.

| Capability | Raw Modding | S4CL (v3.6+) | Stark Framework (v0.2) |
|-----------|-------------|---------------|------------------------|
| **Maturity** | As old as TS4 itself | Battle-tested, 128K+ LoC, years of community use | New -- alpha, not battle-tested yet |
| **Community adoption** | Universal baseline | De facto standard, hundreds of mods depend on it | Zero mods in the wild (this is v0.2) |
| **Method injection** | `setattr` / monkey-patch | `inject_safely_into` decorator | `inject_before/after/replace` with tracking |
| **Injection tracking** | None | None | Full -- list, revert, conflict-detect |
| **Error handling** | `except: pass` is common | `except: pass` in injection wrapper | Caught, recorded with traceback + context |
| **Event system** | Roll your own | Custom events exist but no typed bus | Typed `EventBus` with priority, cancellation |
| **Mod registry** | None | `CommonModIdentity` class | `ModRegistry` with conflict + dependency check |
| **Diagnostics** | `print()` and pray | Some logging utilities | Health reports, error attribution, conflict detection |
| **Settings engine** | Roll your own JSON | Not included | 3-tier presets, typed validation, persistence, migration |
| **Game-time scheduler** | Alarm system (manual) | Some alarm wrappers | `GameScheduler` with daily/interval/once tasks |
| **Pre-built game hooks** | Write your own | Some common hooks | 11 hooks on real game classes (from bytecode analysis) |
| **Type stubs** | Not included | Not included | Full `.pyi` stubs for IDE autocompletion |
| **Sim/Household helpers** | Write your own | Extensive (biggest strength) | Basic -- `SimService`, `HouseholdService`, `WorldService` |
| **CAS / Outfit helpers** | Write your own | Extensive | Not yet |
| **Interaction helpers** | Write your own | Extensive | Not yet |
| **Dialogue / UI utilities** | Write your own | Extensive | Not yet |
| **Trait / Buff helpers** | Write your own | Extensive | Partial (via `TuningHelper`) |
| **Documentation** | EA's are sparse | Good API docs | This README + inline docstrings |
| **Test suite** | N/A | Some tests | 80 tests, all passing |
| **Python version** | 3.7 (game runtime) | 3.7 | 3.7 (stdlib only, zero dependencies) |

**Bottom line:**

- **S4CL is proven and comprehensive.** If you need Sim helpers, CAS utilities, dialogue wrappers, or interaction tools today, S4CL has years of battle-tested code. We don't pretend otherwise.
- **Stark Framework is architecturally better but functionally narrower.** We have a cleaner foundation (typed events, tracked injections, real diagnostics, settings engine), but we cover less surface area.
- **They coexist.** Use S4CL for its utilities. Use Stark Framework for its architecture. Adopt whichever pieces help.

---

## ⚖️ How It Compares

sims4-stark-framework replaces S4CL (Sims4CommunityLibrary) as the primary Python modding framework for Sims 4.

| Feature | S4CL (Community Library) | sims4-stark-framework |
|---------|--------------------------|----------------------|
| Type annotations | Partial — many `Any` types | Full — all public APIs typed |
| Decorator-driven hooks | No — manual injection pattern | Yes — `@on_event`, `@inject`, `@mod` |
| Dependency injection | No | Yes — `@inject` gives service access |
| Hot reload | No | Yes — live mod updates without restart |
| Event system | Limited custom events | Typed event bus with wildcard matching |
| Mod lifecycle | Manual `_reload_module` | `@mod` decorator handles init/teardown |
| Python version | 3.7 (EA's interpreter) | 3.7 — same EA interpreter, full compat |
| Game version compat | Lags behind EA patches | Pinned stubs, patch-tracked |
| Learning curve | High — requires understanding S4CL internals | Low — decorator syntax, standard Python patterns |
| Active maintenance | Community-maintained, slow patch response | Actively maintained by Stark Studio Labs |
| License | MIT | MIT |

> **Note:** S4CL is a genuine community achievement and many great mods depend on it. The Stark Framework is not a drop-in replacement — it's a different API designed for new mods from scratch.

---

## 🗺️ Roadmap

| Feature | Status | Notes |
|---------|--------|-------|
| `@mod` decorator — lifecycle management | ✅ Shipped | Init, teardown, reload hooks |
| `@on_event` — typed game event hooks | ✅ Shipped | 40+ event types |
| `@inject` — service injection | ✅ Shipped | Direct access to EA's service registry |
| Type stubs for EA's Python API | ✅ Shipped | Enables IDE autocomplete |
| Hot reload server | 🔨 In Progress | File watcher → live mod swap |
| Wildcard event matching | 🔨 In Progress | `sim.skill.*` pattern matching |
| Inter-mod messaging bus | 📋 Planned | Mods can publish/subscribe to each other |
| Sim state query API | 📋 Planned | Cleaner access to sim traits, skills, needs |
| Game version compatibility checker | 📋 Planned | Warn when stubs are out of date after EA patch |
| XML tuning integration | 📋 Planned | Python hooks that interact with tuning changes |
| S4CL compatibility shim | ❌ Out of Scope | Intentionally different API |
| CAS / Build-Buy assets | ❌ Out of Scope | Script mods only; use S4S for assets |

---

## The Problem

Sims 4 modding is stuck in 2015. The tools exist, but they fight you every step of the way.

### Monkey-patching everywhere

The dominant approach to hooking into game methods is monkey-patching -- replacing a game function with your own at runtime. [Sims4CommunityLib](https://github.com/ColonolNutty/Sims4CommunityLibrary) (S4CL) is the community standard at ~128K lines of code, and it relies heavily on this pattern. It works... until it doesn't:

- **Two mods patch the same function? One silently wins.** There's no conflict detection, no error, no warning. The second mod's patch just overwrites the first. Your mod is broken and you have no idea why.
- **Exceptions get swallowed.** The standard S4CL injection pattern wraps everything in a bare `except: pass`. Your error happened. You'll never know.
- **No dependency tracking.** Mods load in arbitrary order. If Mod A depends on Mod B, you find out it's missing when the game crashes -- not at startup.

### No standard event system

Every mod that needs to react to game events (a Sim dying, a household loading, a lot changing) has to invent its own approach. Some poll on a timer. Some monkey-patch deep into the engine. Some just hook into Zone.on_loading_screen_animation_finished and hope for the best. There's no shared vocabulary for "something happened in the game."

### Errors disappear into the void

When something goes wrong in a Sims 4 mod, you get... nothing. Maybe a freeze. Maybe a silent failure. Maybe the game's `lastException.txt` has a cryptic traceback that doesn't mention your mod by name. Debugging means adding `print()` statements and reloading the game (a 1-2 minute cycle) until you find the problem.

### No way to know what's installed

There's no registry of loaded mods. No way to ask "is Mod X installed?" at runtime. No way to declare "my mod conflicts with Mod Y" and have the system warn the player before things break.

**Stark Framework exists to fix all of this.**

---

## The Stark Way

Real code comparisons showing what changes.

### Injection: Hooking Into Game Methods

**Before -- the S4CL way:**

```python
from sims4communitylib.utils.common_injection_utils import CommonInjectionUtils
from sims4communitylib.mod_support.mod_identity import CommonModIdentity

class ModInfo(CommonModIdentity):
    _FILE_PATH = __file__

@CommonInjectionUtils.inject_safely_into(ModInfo.get_identity(),
    'sims.sim.Sim', 'on_add')
def _on_sim_added(original, self, *args, **kwargs):
    try:
        result = original(self, *args, **kwargs)
        return result
    except:
        pass  # Swallowed. Good luck debugging.
```

**After -- the Stark way:**

```python
from stark_framework.core.injection import inject_after

@inject_after("sims.sim.Sim", "on_add", mod_id="my_mod")
def on_sim_added(original, self, *args, **kwargs):
    result = original(self, *args, **kwargs)
    # If this throws, full stack trace in diagnostics.
    # If another mod hooks the same method, both run.
    # The injection is tracked and can be reverted cleanly.
    return result
```

### Or just use a pre-built hook:

```python
from stark_framework.core.events import EventBus
from stark_framework.game_hooks.sim_hooks import SimSpawnedEvent

@EventBus.on(SimSpawnedEvent)
def greet(event):
    print(f"Sim {event.sim_id} entered the world!")
# No injection code at all. The framework handles the hook.
```

---

### Event Handling: Reacting to Game Events

**Before -- poll on a timer:**

```python
_last_known_sims = set()

def _check_for_new_sims():
    global _last_known_sims
    current_sims = set()
    for sim_info in services.sim_info_manager().get_all():
        current_sims.add(sim_info.sim_id)
    new_sims = current_sims - _last_known_sims
    for sim_id in new_sims:
        print(f"New sim detected: {sim_id}")
    _last_known_sims = current_sims
```

**After -- typed events:**

```python
from stark_framework.core.events import EventBus, Event
from dataclasses import dataclass

@dataclass
class SimLoadedEvent(Event):
    sim_id: int
    first_name: str

    def __post_init__(self):
        super().__init__()

@EventBus.on(SimLoadedEvent)
def greet(event: SimLoadedEvent):
    log.info("Sim loaded", sim_id=event.sim_id, name=event.first_name)
```

No polling. No global state. Events are typed dataclasses -- your IDE autocompletes fields and catches typos.

---

## Quick Start

### Step 1: Install the framework

Download the latest release from [Releases](https://github.com/stark-studio-labs/sims4-stark-framework/releases) and place it in your Mods folder:

```
Documents/Electronic Arts/The Sims 4/Mods/
    stark_framework/       <-- drop the framework here
```

Or scaffold a project with [sims4-stark-devkit](https://github.com/stark-studio-labs/sims4-stark-devkit):

```bash
stark-devkit init-project ./MyFirstMod --name "My First Mod" --creator "YourName"
```

### Step 2: Create your mod

```python
# my_mod/__init__.py
from stark_framework.core.registry import ModRegistry
from stark_framework.utils.logging import get_logger

log = get_logger("my_mod")

ModRegistry.register(
    mod_id="my_mod",
    name="My First Mod",
    version="1.0.0",
    author="Your Name",
    dependencies=["stark_framework"],
)

log.info("My First Mod loaded!")
```

```python
# my_mod/hooks.py
from stark_framework.core.events import EventBus
from stark_framework.game_hooks.zone_hooks import ZoneLoadingFinishedEvent
from stark_framework.game_hooks.sim_hooks import SimAgeChangedEvent
from stark_framework.utils.logging import get_logger

log = get_logger("my_mod")

@EventBus.on(ZoneLoadingFinishedEvent)
def on_lot_ready(event):
    log.info("Lot loaded!", zone_id=event.zone_id)

@EventBus.on(SimAgeChangedEvent)
def on_age_up(event):
    log.info("Sim aged up!", sim_id=event.sim_id,
             old_age=event.old_age, new_age=event.new_age)
```

### Step 3: Test it

Launch The Sims 4 and load a save. For development outside the game:

```bash
cd sims4-stark-framework
pip install -e ".[dev]"
pytest
```

---

## Core Concepts

### Events

The event bus is the centerpiece. Instead of monkey-patching game methods, you subscribe to typed events.

```python
from stark_framework.core.events import EventBus, Event
from dataclasses import dataclass

@dataclass
class SimDiedEvent(Event):
    sim_id: int
    cause: str

    def __post_init__(self):
        super().__init__()

# Subscribe
@EventBus.on(SimDiedEvent)
def handle_death(event):
    print(f"Sim {event.sim_id} died from {event.cause}")

# Publish
result = EventBus.publish(SimDiedEvent(sim_id=42, cause="fire"))
if result.cancelled:
    print("A mod prevented the death!")
```

Features: priority ordering (lower runs first), cancellation, error isolation, source mod tracking.

---

### Injection

Hook into game methods with tracking, conflict detection, and clean revert.

```python
from stark_framework.core.injection import inject_before, inject_after, inject_replace

@inject_after("sims.sim.Sim", "on_add", mod_id="my_mod")
def after_add(original, self, *args, **kwargs):
    result = original(self, *args, **kwargs)
    print("Sim added!")
    return result

# Revert all your injections
from stark_framework.core.injection import InjectionManager
InjectionManager.revert_all(mod_id="my_mod")
```

Three types: `inject_before` (your code first), `inject_after` (original first), `inject_replace` (you decide).

---

### Registry

Track loaded mods, detect conflicts, validate dependencies.

```python
from stark_framework.core.registry import ModRegistry

ModRegistry.register(
    mod_id="alice_vampire_overhaul",
    name="Vampire Overhaul",
    version="2.1.0",
    author="Alice",
    dependencies=["stark_framework"],
    conflicts=["bobs_vampire_mod"],
)

if ModRegistry.is_loaded("werewolf_pack_extension"):
    enable_werewolf_compat()
```

---

### Diagnostics

Automatic error tracking and health reports.

```python
from stark_framework.core.diagnostics import Diagnostics

# Errors from event handlers are recorded automatically.
# Record your own:
Diagnostics.record_error(mod_id="my_mod", error=exc, context="Applying buff")

# Generate a health report:
print(Diagnostics.health_report())
```

---

### Services

Typed helpers that wrap game APIs with None-safety and graceful fallbacks.

```python
from stark_framework.services.sim_service import SimService
from stark_framework.services.household_service import HouseholdService
from stark_framework.services.world_service import WorldService

# All methods return sensible defaults outside the game.
active = SimService.get_active_sim_info()
household = HouseholdService.get_active_household()
zone = WorldService.get_current_zone()
```

---

### Settings

3-tier preset system with typed validation and persistence.

```python
from stark_framework.core.settings import Settings, Preset

settings = Settings(preset=Preset.STANDARD)

# Presets: CASUAL (relaxed), STANDARD (EA defaults), SIMULATION (hardcore)
settings.set_preset(Preset.CASUAL)  # 2x lifespan, no death, 1.5x career pay

# Read and write typed settings
lifespan = settings.get("core.lifespan_multiplier")  # 2.0
settings.set("core.household_size_cap", 12)

# Register mod-specific settings
settings.register_mod_settings("my_economy_mod", {
    "tax_rate": {"type": "float", "default": 0.10, "min": 0.0, "max": 1.0},
})
rate = settings.get("my_economy_mod.tax_rate")

# Listen for changes
settings.on_change("core.lifespan_multiplier", lambda k, old, new: print(f"{old} -> {new}"))

# Settings persist to JSON automatically. Migration support included.
settings.migrate(renames={"old.key": "new.key"}, removals=["deprecated.key"])
```

Built-in core settings: `lifespan_multiplier`, `aging_enabled`, `auto_bills`, `career_pay_multiplier`, `relationship_decay_rate`, `household_size_cap`, `npc_story_progression`, `autonomous_actions`, `death_enabled`, `motive_decay_multiplier`.

---

### Scheduler

Run tasks on game-time, not wall-clock time.

```python
from stark_framework.core.scheduler import GameScheduler

scheduler = GameScheduler()

# Run at midnight every game day
scheduler.daily(hour=0, callback=process_bills, label="midnight_bills")

# Run every 60 Sim-minutes
scheduler.interval(sim_minutes=60, callback=check_needs, label="need_check")

# Run once at the next 8:30 AM
scheduler.once(hour=8, minute=30, callback=morning_greeting, label="morning")

# Cancel a task
scheduler.cancel("midnight_bills")

# The scheduler is tick-driven -- call tick() from a zone hook or alarm:
scheduler.tick(current_hour=23, current_minute=59, current_day=7)
```

---

### Game Hooks

Pre-built injections targeting real Sims 4 class methods. Derived from MCCC bytecode analysis. Import a module and its hooks auto-register. Subscribe to the events they publish.

```python
from stark_framework.core.events import EventBus
from stark_framework.game_hooks.sim_hooks import SimAgeChangedEvent, SimDeathEvent
from stark_framework.game_hooks.zone_hooks import ZoneLoadingFinishedEvent
from stark_framework.game_hooks.instance_hooks import TuningLoadedEvent
from stark_framework.game_hooks.funds_hooks import FundsChangedEvent

# React to Sim aging
@EventBus.on(SimAgeChangedEvent)
def on_age_change(event):
    print(f"Sim {event.sim_id} aged from {event.old_age} to {event.new_age}")

# Prevent death (cancellable event)
@EventBus.on(SimDeathEvent, priority=1)
def save_sim(event):
    if has_death_flower(event.sim_id):
        event.cancel()

# Run init code when the lot is fully loaded
@EventBus.on(ZoneLoadingFinishedEvent)
def on_lot_ready(event):
    initialize_mod_state()

# Modify tuning as it loads (the MCCC pattern)
@EventBus.on(TuningLoadedEvent)
def patch_tuning(event):
    if str(event.manager_type) == "CAREER":
        for tuning_id, cls in event.tuning_classes.items():
            # Mutate career tuning at load time
            pass

# Double career pay (modifiable + cancellable funds event)
@EventBus.on(FundsChangedEvent)
def double_career_pay(event):
    if str(event.reason) == "CAREER":
        event.amount *= 2
```

**Hook targets (from bytecode analysis):**

| Module | Game Class | Method | Event |
|--------|-----------|--------|-------|
| `sim_hooks` | `SimInfo` | `advance_age` | `SimAgeChangedEvent` |
| `sim_hooks` | `Sim` | `on_add` | `SimSpawnedEvent` |
| `sim_hooks` | `Sim` | `on_remove` | `SimDespawnedEvent` |
| `sim_hooks` | `DeathTracker` | `run_death_behavior` | `SimDeathEvent` (cancellable) |
| `zone_hooks` | `Zone` | `do_zone_spin_up` | `ZoneSpinUpEvent` |
| `zone_hooks` | `Zone` | `on_loading_screen_animation_finished` | `ZoneLoadingFinishedEvent` |
| `zone_hooks` | `Zone` | `on_cleanup_zone_objects` | `ZoneCleanupEvent` |
| `instance_hooks` | `InstanceManager` | `load_data_into_class_instances` | `TuningLoadedEvent` |
| `funds_hooks` | `_Funds` | `add` | `FundsChangedEvent` (cancellable) |

---

### Type Stubs

The `stubs/` directory provides `.pyi` type stubs for Sims 4 game modules. Add them to your IDE for autocompletion and type checking when writing mods.

```toml
# pyproject.toml
[tool.mypy]
mypy_path = "stubs"
```

```json
// VS Code settings.json
{ "python.analysis.stubPath": "stubs" }
```

Included stubs: `sims4.resources` (Types, ResourceKey), `services` (manager accessors), `sims` (SimInfo, Sim, Household, _Funds, Age, Species, Gender), `zone` (Zone), `interactions` (DeathTracker, SuperInteraction), `instance_manager` (InstanceManager).

---

### Logging

Structured, mod-aware logging with an in-memory buffer.

```python
from stark_framework.utils.logging import get_logger

log = get_logger("my_mod")
log.info("Mod loaded", version="2.1.0")
log.error("Failed to apply buff", sim_id=42, reason="not_found")
# Output: [ERROR] [my_mod] Failed to apply buff | sim_id=42, reason='not_found'
```

---

## Architecture

```
stark_framework/
    core/
        events.py           -- Typed event bus (publish/subscribe, priority, cancellation)
        injection.py         -- Clean injection decorators (before/after/replace, tracked)
        registry.py          -- Mod registry (conflicts, dependencies)
        diagnostics.py       -- Error tracking, conflict detection, health reports
        settings.py          -- 3-tier preset system with typed validation + persistence
        scheduler.py         -- Game-time task scheduler (daily/interval/once)
    game_hooks/
        sim_hooks.py         -- SimInfo.advance_age, Sim.on_add/on_remove, DeathTracker
        zone_hooks.py        -- Zone.do_zone_spin_up, on_loading_screen_animation_finished
        instance_hooks.py    -- InstanceManager.load_data_into_class_instances
        funds_hooks.py       -- _Funds.add (Simoleon transaction interception)
    services/
        sim_service.py       -- Sim data access (names, ages, traits)
        household_service.py -- Household management (members, funds, lots)
        world_service.py     -- World/lot/zone helpers (objects, Sims on lot)
    utils/
        logging.py           -- Structured logging with mod context + buffer
        tuning.py            -- XML tuning helpers (FNV hashing, instance lookups)
stubs/
    sims4/
        resources.pyi        -- Types, ResourceKey
        services.pyi         -- Manager accessors
        sims.pyi             -- SimInfo, Sim, Household, _Funds, Age, Species
        zone.pyi             -- Zone
        interactions.pyi     -- DeathTracker, SuperInteraction
        instance_manager.pyi -- InstanceManager
```

**Design principles:**

- **Zero external dependencies** -- runs on Python 3.7 (The Sims 4's embedded interpreter) with only stdlib imports
- **No monkey-patching internally** -- uses `setattr` for injection but tracks every change for clean revert
- **Errors never swallowed** -- every caught exception is recorded with full context via diagnostics
- **Game-optional** -- services return sensible defaults outside the game, so you can develop and test without launching Sims 4
- **Hooks derived from real analysis** -- game_hooks targets are from MCCC bytecode reconstruction, not guesswork

---

## S4CL Compatibility

**Stark Framework and S4CL can coexist.** You do not need to remove S4CL to use Stark Framework.

- Mods built on S4CL will continue to work exactly as before
- Stark Framework does not modify or override any S4CL code
- You can use S4CL utilities alongside Stark Framework in the same mod
- Over time, Stark Framework provides a path to move off S4CL patterns at your own pace

**If you're starting a new mod,** we recommend building on Stark Framework from the start.

**If you have an existing S4CL mod,** adopt incrementally -- start with the event bus and registry, gradually replace injection patterns.

---

## For Framework Contributors

### Dev Setup

```bash
git clone https://github.com/stark-studio-labs/sims4-stark-framework.git
cd sims4-stark-framework
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest                    # Run all 80 tests
pytest -v                 # Verbose output
pytest --cov              # With coverage report
pytest tests/test_events.py      # Specific file
pytest tests/test_game_hooks.py  # Game hooks tests
pytest tests/test_settings.py    # Settings engine tests
pytest tests/test_scheduler.py   # Scheduler tests
```

### Project Structure

```
sims4-stark-framework/
    src/stark_framework/    -- Framework source code
    stubs/sims4/            -- Type stubs for Sims 4 game modules
    tests/                  -- Test suite (80 tests)
    pyproject.toml          -- Project config
    README.md               -- This file
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Write tests for new functionality
4. Run `pytest` and make sure everything passes
5. Submit a pull request

---

<div align="center">

**Built by [Stark Studio Labs](https://github.com/stark-studio-labs)**

MIT License. See [LICENSE](LICENSE) for details.

</div>
