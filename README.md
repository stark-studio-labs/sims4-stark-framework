<div align="center">

# 🧱 Stark Framework

**A modern, typed modding framework for The Sims 4.**

*Clean architecture. Zero monkey-patching. First-class developer experience.*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)]()
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)]()
[![Made by Stark Studio Labs](https://img.shields.io/badge/made%20by-Stark%20Studio%20Labs-blueviolet)](https://github.com/stark-studio-labs)

*Built by [Stark Studio Labs](https://github.com/stark-studio-labs)*

</div>

---

## 🌐 Stark Labs Ecosystem

> Everything we build for The Sims 4 modding community — open source, interconnected, and community-driven.

| Repo | What It Does | Status |
|------|-------------|--------|
| 📚 **[awesome-sims4-mods](https://github.com/stark-studio-labs/awesome-sims4-mods)** | Curated mod directory with compatibility tracking | ![Active](https://img.shields.io/badge/-active-brightgreen) |
| 🧱 **[sims4-stark-framework](https://github.com/stark-studio-labs/sims4-stark-framework)** | Modern typed modding framework (replaces S4CL patterns) | ![Active](https://img.shields.io/badge/-active-brightgreen) |
| 🔧 **[sims4-stark-devkit](https://github.com/stark-studio-labs/sims4-stark-devkit)** | CLI toolkit — decompile, package, scaffold, test | ![Active](https://img.shields.io/badge/-active-brightgreen) |
| 📦 **[sims4-mod-manager](https://github.com/stark-studio-labs/sims4-mod-manager)** | Scan, organize, and detect conflicts in your mod collection | ![Alpha](https://img.shields.io/badge/-alpha-orange) |
| 🎨 **[sims4-mod-builder](https://github.com/stark-studio-labs/sims4-mod-builder)** | Visual mod creation tool — no XML knowledge needed | ![In Dev](https://img.shields.io/badge/-in%20dev-yellow) |
| 🔬 **[sims4-mod-revival](https://github.com/stark-studio-labs/sims4-mod-revival)** | Decompile and revive abandoned community mods | ![Active](https://img.shields.io/badge/-active-brightgreen) |
| 💰 **[sims4-economy-sim](https://github.com/stark-studio-labs/sims4-economy-sim)** | Banking, bills, jobs, and stock market overhaul mod | ![Pre-Alpha](https://img.shields.io/badge/-pre--alpha-red) |

---

## 📖 Table of Contents

- [😤 The Problem](#-the-problem)
- [✨ The Stark Way](#-the-stark-way)
- [🚀 Quick Start](#-quick-start)
- [📚 Core Concepts](#-core-concepts)
  - [Events](#-events)
  - [Injection](#-injection)
  - [Registry](#-registry)
  - [Diagnostics](#-diagnostics)
  - [Services](#-services)
  - [Logging](#-logging)
- [🏗️ Architecture](#%EF%B8%8F-architecture)
- [🤝 S4CL Compatibility](#-s4cl-compatibility)
- [🔧 For Framework Contributors](#-for-framework-contributors)

---

## 😤 The Problem

Sims 4 modding is stuck in 2015. The tools exist, but they fight you every step of the way.

### Monkey-patching everywhere

The dominant approach to hooking into game methods is monkey-patching — replacing a game function with your own at runtime. [Sims4CommunityLib](https://github.com/ColonolNutty/Sims4CommunityLibrary) (S4CL) is the community standard at ~128K lines of code, and it relies heavily on this pattern. It works... until it doesn't:

- **Two mods patch the same function? One silently wins.** There's no conflict detection, no error, no warning. The second mod's patch just overwrites the first. Your mod is broken and you have no idea why.
- **Exceptions get swallowed.** The standard S4CL injection pattern wraps everything in a bare `except: pass`. Your error happened. You'll never know.
- **No dependency tracking.** Mods load in arbitrary order. If Mod A depends on Mod B, you find out it's missing when the game crashes — not at startup.

### No standard event system

Every mod that needs to react to game events (a Sim dying, a household loading, a lot changing) has to invent its own approach. Some poll on a timer. Some monkey-patch deep into the engine. Some just hook into Zone.on_loading_screen_animation_finished and hope for the best. There's no shared vocabulary for "something happened in the game."

### Errors disappear into the void

When something goes wrong in a Sims 4 mod, you get... nothing. Maybe a freeze. Maybe a silent failure. Maybe the game's `lastException.txt` has a cryptic traceback that doesn't mention your mod by name. Debugging means adding `print()` statements and reloading the game (a 1-2 minute cycle) until you find the problem.

### No way to know what's installed

There's no registry of loaded mods. No way to ask "is Mod X installed?" at runtime. No way to declare "my mod conflicts with Mod Y" and have the system warn the player before things break.

**Stark Framework exists to fix all of this.**

---

## ✨ The Stark Way

Real code comparisons showing what changes.

### Injection: Hooking Into Game Methods

**Before — the S4CL way:**

```python
# The old way: manual injection boilerplate
from sims4communitylib.utils.common_injection_utils import CommonInjectionUtils
from sims4communitylib.mod_support.mod_identity import CommonModIdentity

class ModInfo(CommonModIdentity):
    _FILE_PATH = __file__

@CommonInjectionUtils.inject_safely_into(ModInfo.get_identity(),
    'sims.sim.Sim', 'on_add')
def _on_sim_added(original, self, *args, **kwargs):
    # Hope this doesn't conflict with other mods doing the same thing
    try:
        result = original(self, *args, **kwargs)
        # Your code here...
        return result
    except:
        pass  # Swallowed. Good luck debugging.
```

**After — the Stark way:**

```python
# The Stark way: typed events, clean decorators, real error tracking
from stark_framework.core.events import EventBus
from stark_framework.core.injection import inject_after
from dataclasses import dataclass

@dataclass
class SimAddedEvent(EventBus.Event):
    sim_id: int

@inject_after("sims.sim.Sim", "on_add", mod_id="my_mod")
def on_sim_added(original, self, *args, **kwargs):
    result = original(self, *args, **kwargs)
    EventBus.publish(SimAddedEvent(sim_id=self.sim_id))
    return result
    # If this throws, you'll see the full stack trace in diagnostics.
    # If another mod hooks the same method, both run — no silent override.
    # The injection is tracked and can be reverted cleanly.
```

**What changed:**
- No boilerplate `ModIdentity` class required
- No bare `except: pass` — errors are caught and recorded by the framework with full tracebacks
- The injection is registered and visible to the diagnostics system
- Other mods hooking the same method don't silently overwrite yours — they chain

---

### Event Handling: Reacting to Game Events

**Before — the poll-based way:**

```python
# The old way: poll on a timer and check for state changes
import services
import sims4.commands

_last_known_sims = set()

# Called every few sim-minutes via an alarm or zone spin-up
def _check_for_new_sims():
    global _last_known_sims
    current_sims = set()
    sim_info_manager = services.sim_info_manager()
    if sim_info_manager:
        for sim_info in sim_info_manager.get_all():
            current_sims.add(sim_info.sim_id)

    new_sims = current_sims - _last_known_sims
    for sim_id in new_sims:
        print(f"New sim detected: {sim_id}")  # print is your only friend
        # Hope nobody else is also polling...

    _last_known_sims = current_sims
```

**After — typed event bus:**

```python
# The Stark way: subscribe to typed events, react instantly
from stark_framework.core.events import EventBus, Event
from dataclasses import dataclass

@dataclass
class SimLoadedEvent(Event):
    sim_id: int
    first_name: str
    last_name: str

    def __post_init__(self):
        super().__init__()

# Subscribe with a decorator — handler fires when the event is published
@EventBus.on(SimLoadedEvent)
def greet_new_sim(event: SimLoadedEvent):
    log.info("New sim loaded", sim_id=event.sim_id, name=f"{event.first_name} {event.last_name}")

# Priority ordering — lower values run first (default is 100)
@EventBus.on(SimLoadedEvent, priority=10)
def log_early(event: SimLoadedEvent):
    log.debug("Early handler", sim_id=event.sim_id)

# Cancellation — stop other handlers from running
@EventBus.on(SimLoadedEvent, priority=5)
def maybe_block(event: SimLoadedEvent):
    if event.first_name == "Vladislaus":
        event.cancel()  # Remaining handlers won't fire
```

**What changed:**
- No polling. No global state. No timers.
- Events are typed dataclasses — your IDE autocompletes fields, catches typos
- Priority ordering means multiple mods can subscribe and run in a defined order
- Cancellation lets any handler stop the chain (and you can check `event.cancelled` afterward)
- The source mod is tracked: `EventBus.publish(event, source_mod="my_mod")`

---

### Logging: Seeing What Happened

**Before — print and pray:**

```python
# The old way: print statements, hope they show up somewhere
print("My mod loaded!")
print(f"Applying buff to sim {sim_id}")
print(f"ERROR: something went wrong")  # Where does this go? Who knows.

# If you're lucky, it shows up in the game console.
# If you're not, it vanishes completely.
# There's no way to filter by mod, no timestamps, no structured data.
```

**After — structured logging with context:**

```python
# The Stark way: structured, filterable, buffered logging
from stark_framework.utils.logging import get_logger

log = get_logger("my_vampire_mod")

log.info("Mod initialized", version="2.1.0")
log.info("Buff applied", sim_id=42, buff="vampire_thirst", duration=120.0)
log.warn("Tuning override detected", tuning_id="0x1A2B3C4D")
log.error("Failed to apply trait", sim_id=42, trait="vampire_master", reason="already_has_trait")

# Debug messages only show when debug mode is enabled
log.debug("Cache lookup", key="trait_42", hit=False)

# Output format: [LEVEL] [mod_name] message | key=value, key=value
# [INFO] [my_vampire_mod] Buff applied | sim_id=42, buff='vampire_thirst', duration=120.0

# Every log entry is buffered in memory — pull recent entries for health reports:
from stark_framework.utils.logging import LogBuffer
recent_errors = LogBuffer.get_entries(limit=10, level="ERROR", mod_name="my_vampire_mod")
```

**What changed:**
- Every message is tagged with your mod name — no more guessing who logged what
- Structured key-value fields instead of f-string spaghetti
- In-memory buffer lets you pull recent logs without parsing files
- Debug mode toggle — ship debug logging in production, disable it by default
- Output goes to stderr (game console + exception log) AND the in-memory buffer

---

### Mod Registration: Knowing What's Installed

**Before — nothing:**

```python
# The old way: there is no old way. Mods just... exist.
# No registration. No conflict detection. No dependency checking.
# Two mods with the same name? Both load. Good luck.
# Missing a dependency? Find out when the game crashes.
```

**After — explicit registration with conflict detection:**

```python
from stark_framework.core.registry import ModRegistry

# Register your mod at startup
ModRegistry.register(
    mod_id="alice_vampire_overhaul",
    name="Vampire Overhaul",
    version="2.1.0",
    author="Alice",
    dependencies=["stark_framework"],
    conflicts=["bobs_vampire_mod"],  # Can't coexist — framework will raise ConflictError
)

# Check if another mod is loaded (for compatibility patches)
if ModRegistry.is_loaded("werewolf_pack_extension"):
    enable_werewolf_compat()

# List everything that's installed
for mod_id, info in ModRegistry.all_mods().items():
    print(f"{info['name']} v{info['version']} by {info['author']}")

# What happens at registration time:
# - Duplicate mod_id? → ConflictError with a clear message
# - Conflicts with a loaded mod? → ConflictError
# - Missing dependency? → DependencyError listing what's missing
```

**What changed:**
- Mods have identities — you can query what's installed at runtime
- Conflicts are declared upfront and caught at load time, not at crash time
- Dependencies are validated before your mod's code runs
- The diagnostics system uses mod IDs to attribute errors to the right mod

---

## 🚀 Quick Start

Get your first Stark Framework mod running in 5 minutes.

### Step 1: Install the framework

Download the latest release from [Releases](https://github.com/stark-studio-labs/sims4-stark-framework/releases) and place it in your Mods folder:

```
Documents/
  Electronic Arts/
    The Sims 4/
      Mods/
        stark_framework/       ← Drop the framework here
          core/
          services/
          utils/
          __init__.py
```

Or, if you're using [sims4-stark-devkit](https://github.com/stark-studio-labs/sims4-stark-devkit), scaffold a new project and the framework is included automatically:

```bash
stark-devkit init-project ./MyFirstMod --name "My First Mod" --creator "YourName"
```

### Step 2: Create your first mod

Create a new folder in your Mods directory for your mod, then add a Python file:

```
Documents/
  Electronic Arts/
    The Sims 4/
      Mods/
        stark_framework/       ← The framework (already installed)
        my_first_mod/          ← Your mod
          __init__.py
          my_first_mod.py
```

**`my_first_mod/__init__.py`** — register your mod when it loads:

```python
from stark_framework.core.registry import ModRegistry
from stark_framework.utils.logging import get_logger

log = get_logger("my_first_mod")

# Register with the framework
ModRegistry.register(
    mod_id="my_first_mod",
    name="My First Mod",
    version="1.0.0",
    author="Your Name",
    dependencies=["stark_framework"],
)

log.info("My First Mod loaded!")
```

**`my_first_mod/my_first_mod.py`** — hook into the game:

```python
from stark_framework.core.events import EventBus, Event
from stark_framework.core.injection import inject_after
from stark_framework.services.household_service import HouseholdService
from stark_framework.utils.logging import get_logger
from dataclasses import dataclass

log = get_logger("my_first_mod")

# Define a custom event
@dataclass
class HouseholdLoadedEvent(Event):
    household_name: str
    member_count: int
    funds: int

    def __post_init__(self):
        super().__init__()

# Fire the event when a household becomes active
@inject_after("sims.household.Household", "on_all_households_and_sim_infos_loaded",
              mod_id="my_first_mod")
def on_household_loaded(original, self, *args, **kwargs):
    result = original(self, *args, **kwargs)

    household = HouseholdService.get_active_household()
    if household:
        name = HouseholdService.get_name(household)
        count = HouseholdService.member_count(household)
        funds = HouseholdService.get_funds(household)

        EventBus.publish(
            HouseholdLoadedEvent(household_name=name, member_count=count, funds=funds),
            source_mod="my_first_mod",
        )

    return result

# React to the event
@EventBus.on(HouseholdLoadedEvent)
def greet_household(event: HouseholdLoadedEvent):
    log.info(
        "Household loaded!",
        name=event.household_name,
        members=event.member_count,
        funds=event.funds,
    )
```

### Step 3: Test it

Launch The Sims 4 and load a save. Check the game console or `lastException.txt` for:

```
[INFO] [my_first_mod] My First Mod loaded!
[INFO] [my_first_mod] Household loaded! | name='Goth', members=5, funds=50000
```

If you're developing outside the game, run the framework's test suite:

```bash
cd sims4-stark-framework
pip install -e ".[dev]"
pytest
```

---

## 📚 Core Concepts

### 🎯 Events

The event bus is the centerpiece of Stark Framework. Instead of monkey-patching game methods to detect when things happen, you publish and subscribe to typed events.

**What is an event?** A plain Python dataclass that extends `Event`. It carries data about something that happened.

```python
from stark_framework.core.events import EventBus, Event
from dataclasses import dataclass

@dataclass
class SimDiedEvent(Event):
    sim_id: int
    cause: str       # "fire", "old_age", "drowning", etc.

    def __post_init__(self):
        super().__init__()  # Required for cancellation support
```

**Subscribe to events** with the `@EventBus.on()` decorator or the `EventBus.subscribe()` method:

```python
# Decorator style (most common)
@EventBus.on(SimDiedEvent)
def handle_death(event: SimDiedEvent):
    print(f"Sim {event.sim_id} died from {event.cause}")

# Programmatic style (useful for dynamic subscriptions)
EventBus.subscribe(SimDiedEvent, handle_death, priority=50, mod_id="my_mod")
```

**Publish events** to notify all subscribers:

```python
result = EventBus.publish(SimDiedEvent(sim_id=42, cause="fire"))
if result.cancelled:
    print("A mod prevented the death!")
```

**Priority ordering** controls execution order. Lower numbers run first (default is 100):

```python
@EventBus.on(SimDiedEvent, priority=10)   # Runs first
def log_early(event): ...

@EventBus.on(SimDiedEvent, priority=100)  # Runs second (default)
def handle_normal(event): ...

@EventBus.on(SimDiedEvent, priority=200)  # Runs last
def cleanup_late(event): ...
```

**Cancellation** lets any handler stop the remaining handlers from running:

```python
@EventBus.on(SimDiedEvent, priority=1)
def maybe_save_sim(event: SimDiedEvent):
    if player_has_death_flower():
        event.cancel()  # No more handlers fire
```

**Error isolation** — if a handler throws an exception, it's caught and recorded by the diagnostics system. Other handlers still run:

```python
@EventBus.on(SimDiedEvent, priority=10, mod_id="buggy_mod")
def buggy_handler(event):
    raise RuntimeError("Oops!")  # Caught, recorded, doesn't crash anything

@EventBus.on(SimDiedEvent, priority=20)
def still_runs(event):
    print("I still run!")  # Yes, this fires
```

---

### 💉 Injection

Injection is how you hook into the game's existing methods. Instead of replacing a function entirely (monkey-patching), Stark Framework wraps it — the original still runs, your code runs before or after, and the whole thing is tracked.

**Three injection types:**

| Decorator | When Your Code Runs | Use Case |
|-----------|-------------------|----------|
| `@inject_before` | Before the original method | Validate inputs, log calls, modify args |
| `@inject_after` | After the original method | React to results, fire events, clean up |
| `@inject_replace` | Instead of the original (you decide if it runs) | Full control — use sparingly |

**`inject_before`** — your code runs first, then you call the original:

```python
from stark_framework.core.injection import inject_before

@inject_before("sims.sim.Sim", "on_add", mod_id="my_mod")
def before_sim_add(original, self, *args, **kwargs):
    print(f"A Sim is about to be added!")
    return original(self, *args, **kwargs)  # MUST call original
```

**`inject_after`** — the original runs first, then your code:

```python
from stark_framework.core.injection import inject_after

@inject_after("sims.sim.Sim", "on_remove", mod_id="my_mod")
def after_sim_remove(original, self, *args, **kwargs):
    result = original(self, *args, **kwargs)
    print(f"A Sim was removed. Cleaning up...")
    return result
```

**`inject_replace`** — you control everything:

```python
from stark_framework.core.injection import inject_replace

@inject_replace("sims.sim_info.SimInfo", "get_name", mod_id="my_mod")
def custom_name(original, self, *args, **kwargs):
    real_name = original(self, *args, **kwargs)
    return f"[Modded] {real_name}"
```

**Reverting injections** — undo your hooks cleanly:

```python
from stark_framework.core.injection import InjectionManager

# Revert all injections from your mod
InjectionManager.revert_all(mod_id="my_mod")

# List what's currently injected
for inj in InjectionManager.list_injections():
    print(f"{inj['target']}.{inj['method']} — {inj['kind']} by {inj['mod_id']}")
```

The first argument to your wrapper is always `original` — the game's real method. **You must call it** (except in `inject_replace` where it's your choice). The second argument is `self` — the game object instance.

---

### 📋 Registry

The registry tracks every loaded mod. It's how the framework knows what's installed, detects conflicts, and validates dependencies.

**Register your mod** at startup (typically in `__init__.py`):

```python
from stark_framework.core.registry import ModRegistry

ModRegistry.register(
    mod_id="alice_vampire_overhaul",    # Unique ID — use snake_case
    name="Vampire Overhaul",            # Human-readable name
    version="2.1.0",                    # Semantic version
    author="Alice",                     # Author name
    dependencies=["stark_framework"],   # Required mods (checked at registration)
    conflicts=["bobs_vampire_mod"],     # Incompatible mods (raises ConflictError)
)
```

**What happens at registration:**

1. **Duplicate check** — if `mod_id` is already registered, `ConflictError` is raised with a message telling you which version is already loaded
2. **Conflict check** — if any mod in your `conflicts` list is loaded (or any loaded mod lists YOU as a conflict), `ConflictError` is raised
3. **Dependency check** — if any mod in your `dependencies` list is not loaded, `DependencyError` is raised listing the missing mods

**Query the registry** at runtime:

```python
# Is a mod loaded?
if ModRegistry.is_loaded("werewolf_pack_extension"):
    enable_werewolf_compat()

# Get mod info
info = ModRegistry.get("alice_vampire_overhaul")
print(info["version"])  # "2.1.0"
print(info["author"])   # "Alice"

# List everything
for mod_id, info in ModRegistry.all_mods().items():
    print(f"{info['name']} v{info['version']} by {info['author']}")
```

---

### 🔍 Diagnostics

The diagnostics system automatically catches and records errors from event handlers and injections. You can also record your own errors, detect conflicts, and generate health reports.

**Errors are recorded automatically** when an event handler throws:

```python
@EventBus.on(SimDiedEvent, mod_id="my_mod")
def handler(event):
    raise ValueError("Something broke")
    # → Automatically recorded: mod_id="my_mod", full traceback, context
```

**Record your own errors** for tracking:

```python
from stark_framework.core.diagnostics import Diagnostics

try:
    risky_operation()
except Exception as e:
    Diagnostics.record_error(
        mod_id="my_mod",
        error=e,
        context="Applying custom trait to Sim 42",
    )
```

**Detect conflicts** between mods:

```python
conflicts = Diagnostics.detect_conflicts()
for c in conflicts:
    print(f"[{c['severity'].upper()}] {c['description']}")

# Detects:
# - Multiple mods injecting the same game method
# - Mods with high error rates (10+ errors)
```

**Generate a health report** — a single snapshot of everything:

```python
report = Diagnostics.health_report()
print(report)
```

```
=== Stark Framework Health Report ===

Loaded mods: 3
  Vampire Overhaul v2.1.0 [OK]
  Werewolf Extension v1.0.0 [OK]
  Buggy Mod v0.1.0 [12 errors]

Active injections: 4
  sims.sim.Sim.on_add (after) by alice_vampire_overhaul
  sims.sim.Sim.on_remove (after) by alice_vampire_overhaul
  sims.sim_info.SimInfo.get_name (replace) by werewolf_extension
  sims.household.Household.on_all_households_and_sim_infos_loaded (after) by buggy_mod

Detected conflicts: 2
  [WARNING] Multiple mods inject sims.sim.Sim.on_add: alice_vampire_overhaul, buggy_mod
  [ERROR] Mod 'buggy_mod' has 12 recorded errors

Total errors: 12 (showing last 5)
  [ValueError] Applying buff: invalid buff ID
  [AttributeError] Sim lookup: 'NoneType' has no attribute 'sim_id'
  ...

=== End Report ===
```

---

### 🛠️ Services

Services are typed helper classes that wrap the game's internal APIs. They handle `None` checks, missing attributes, and `ImportError` gracefully — so your code doesn't have to.

**SimService** — work with Sim data:

```python
from stark_framework.services.sim_service import SimService

# Get all Sims in the save
for sim_info in SimService.get_all_sim_infos():
    name = SimService.get_full_name(sim_info)
    print(f"Sim: {name}")

# Get the active (player-controlled) Sim
active = SimService.get_active_sim_info()
if active:
    print(f"Playing as {SimService.get_full_name(active)}")

# Check age, get traits, get household ID
if SimService.is_teen_or_older(sim_info):
    traits = SimService.get_traits(sim_info)
    household_id = SimService.get_household_id(sim_info)
```

**HouseholdService** — work with households:

```python
from stark_framework.services.household_service import HouseholdService

# Get the active household
household = HouseholdService.get_active_household()
if household:
    name = HouseholdService.get_name(household)
    funds = HouseholdService.get_funds(household)
    members = HouseholdService.get_members(household)
    print(f"The {name} family has {funds} Simoleons and {len(members)} members")

# List all households
for hh in HouseholdService.get_all_households():
    print(f"{HouseholdService.get_name(hh)}: {HouseholdService.member_count(hh)} sims")
```

**WorldService** — work with zones, lots, and the world:

```python
from stark_framework.services.world_service import WorldService

# Current zone and lot
zone = WorldService.get_current_zone()
lot = WorldService.get_current_lot()

# Check lot type
if WorldService.is_residential_lot():
    print("We're on a residential lot")

# Get objects and Sims on the current lot
objects = WorldService.get_lot_objects()
sims_here = WorldService.get_sims_on_lot()
print(f"{len(objects)} objects, {len(sims_here)} sims on this lot")
```

All service methods return sensible defaults (`None`, `[]`, `0`, `"Unknown Sim"`) when called outside the game environment. This means your code doesn't crash during development or testing — it just gets empty data.

---

### 📝 Logging

Stark Framework provides structured, mod-aware logging that replaces `print()` statements.

**Create a logger** for your mod:

```python
from stark_framework.utils.logging import get_logger

log = get_logger("my_mod")  # Name should match your mod_id
```

**Log at different levels:**

```python
log.info("Mod loaded", version="2.1.0")
log.warn("Unexpected state", sim_id=42, expected="alive", actual="ghost")
log.error("Failed to apply buff", sim_id=42, buff="happy_buff", reason="buff_not_found")
log.debug("Cache miss", key="trait_lookup")  # Only shows when debug mode is enabled
```

**Output format:**

```
[INFO] [my_mod] Mod loaded | version='2.1.0'
[WARN] [my_mod] Unexpected state | sim_id=42, expected='alive', actual='ghost'
[ERROR] [my_mod] Failed to apply buff | sim_id=42, buff='happy_buff', reason='buff_not_found'
```

**In-memory log buffer** — pull recent entries for diagnostics or health reports:

```python
from stark_framework.utils.logging import LogBuffer

# Get the last 20 entries
recent = LogBuffer.get_entries(limit=20)

# Filter by level or mod
errors = LogBuffer.get_entries(level="ERROR", mod_name="my_mod")
```

**Enable debug mode** globally:

```python
from stark_framework.utils.logging import Logger
Logger.set_debug(True)   # Debug messages now visible
Logger.set_debug(False)  # Back to normal
```

---

### 🔧 Tuning Helpers

The Sims 4 defines game data (traits, buffs, interactions, careers, etc.) through XML tuning files. These are identified at runtime by numeric IDs (FNV hashes). The `TuningHelper` class makes it easy to look up and work with tuning data.

```python
from stark_framework.utils.tuning import TuningHelper, fnv32

# Look up a tuning instance by numeric ID
trait = TuningHelper.get_tuning("TRAIT", 0x1A2B3C4D)
if trait:
    print(f"Found trait: {trait.__name__}")

# Search by name (slower — iterates all instances)
buff = TuningHelper.find_tuning_by_name("BUFF", "Buff_Happy")

# List all tuning of a type
all_traits = TuningHelper.get_all_tuning("TRAIT")
print(f"Game has {len(all_traits)} traits loaded")

# Convert a tuning name to its FNV32 hash
hash_val = fnv32("my_custom_trait")
print(f"Hash: 0x{hash_val:08X}")
```

Supported tuning types: `TRAIT`, `BUFF`, `INTERACTION`, `OBJECT`, `SIM_INFO`, `SITUATION`, `ASPIRATION`, `CAREER`, `SKILL`, `LOT_TUNING`, `RECIPE`.

---

## 🏗️ Architecture

```
stark_framework/
├── 🎯 core/                          # The engine
│   ├── events.py                     # Typed event bus — publish/subscribe with priority & cancellation
│   ├── registry.py                   # Mod registry — tracks loaded mods, conflicts, dependencies
│   ├── injection.py                  # Clean injection decorators — inject_before, inject_after, inject_replace
│   ├── diagnostics.py                # Error tracking, conflict detection, health reports
│   └── __init__.py
├── 🛠️ services/                      # Game API wrappers
│   ├── sim_service.py                # Sim data access — names, ages, traits, household IDs
│   ├── household_service.py          # Household management — members, funds, home lots
│   ├── world_service.py              # World/lot/zone helpers — objects, Sims on lot, lot type
│   └── __init__.py
├── 🔧 utils/                         # Utilities
│   ├── logging.py                    # Structured logging with mod context + in-memory buffer
│   ├── tuning.py                     # XML tuning helpers — FNV hashing, instance manager lookups
│   └── __init__.py
└── __init__.py                       # Package root — exports version and author
```

**Design principles:**

- **Zero external dependencies** — the framework runs on Python 3.7 (The Sims 4's embedded interpreter) with only stdlib imports
- **No monkey-patching internally** — the framework uses `setattr` for injection but tracks every change for clean revert
- **Errors never swallowed** — every caught exception is recorded with full context via the diagnostics system
- **Game-optional** — services return sensible defaults outside the game, so you can develop and test without launching Sims 4

---

## 🤝 S4CL Compatibility

**Stark Framework and S4CL can coexist.** You do not need to remove S4CL to use Stark Framework.

- Mods built on S4CL will continue to work exactly as before
- Stark Framework does not modify or override any S4CL code
- You can use S4CL utilities alongside Stark Framework in the same mod
- Over time, Stark Framework provides a path to move off S4CL patterns at your own pace

**If you're starting a new mod,** we recommend building on Stark Framework from the start. You get typed events, real error tracking, conflict detection, and a cleaner API.

**If you have an existing S4CL mod,** you can adopt Stark Framework incrementally:
1. Add `stark_framework` as a dependency
2. Start using the event bus for new features
3. Gradually replace S4CL injection patterns with Stark decorators
4. Register your mod with the registry for conflict detection

The two frameworks use different mechanisms internally, so there's no risk of one interfering with the other.

---

## 🔧 For Framework Contributors

### Dev Setup

```bash
git clone https://github.com/stark-studio-labs/sims4-stark-framework.git
cd sims4-stark-framework
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest                    # Run all tests
pytest -v                 # Verbose output
pytest --cov              # With coverage report
pytest tests/test_events.py  # Specific test file
```

### Project Structure

```
sims4-stark-framework/
├── src/
│   └── stark_framework/    # Framework source code
├── tests/
│   └── test_events.py      # Test suite
├── pyproject.toml           # Project config (setuptools + pytest)
├── README.md                # You are here
└── LICENSE                  # MIT
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Write tests for new functionality
4. Run `pytest` and make sure everything passes
5. Submit a pull request

---

<div align="center">

**Built with 💚 by [Stark Studio Labs](https://github.com/stark-studio-labs)**

MIT License. See [LICENSE](LICENSE) for details.

</div>
