# Stark Framework

A modern, typed modding framework for The Sims 4 -- built to replace Sims4CommunityLibrary (S4CL) with clean architecture, zero monkey-patching, and first-class developer experience.

## Why Stark Framework?

| Feature | S4CL | Stark Framework |
|---------|------|-----------------|
| Event system | Monkey-patches game methods | Typed event bus with publish/subscribe |
| Mod conflicts | Silent failures | Built-in conflict detection and diagnostics |
| Injection | Manual wrapping boilerplate | Clean `@inject_into` decorators |
| Logging | Basic print statements | Structured logging with mod context |
| Module registration | None | Central registry with dependency tracking |
| Python version | 3.7 | 3.7 (game-compatible) |
| Error handling | Swallowed exceptions | Full error tracking with stack context |

## Installation

### For Mod Developers

1. Download the latest release from [Releases](https://github.com/stark-studio-labs/sims4-stark-framework/releases)
2. Place the `stark_framework` folder in your Sims 4 Mods directory:
   ```
   Documents/Electronic Arts/The Sims 4/Mods/stark_framework/
   ```
3. Import in your mod:
   ```python
   from stark_framework.core.events import EventBus, Event
   ```

### For Framework Contributors

```bash
git clone https://github.com/stark-studio-labs/sims4-stark-framework.git
cd sims4-stark-framework
pip install -e ".[dev]"
pytest
```

## Quick Start

### Subscribe to Game Events

```python
from stark_framework.core.events import EventBus, Event
from dataclasses import dataclass

@dataclass
class SimDiedEvent(Event):
    sim_id: int
    cause: str

# Subscribe a handler
@EventBus.on(SimDiedEvent)
def handle_death(event: SimDiedEvent):
    print(f"Sim {event.sim_id} died from {event.cause}")

# Publish from your mod (or from an injection hook)
EventBus.publish(SimDiedEvent(sim_id=12345, cause="fire"))
```

### Inject Into Game Methods

```python
from stark_framework.core.injection import inject_before, inject_after

@inject_before("sims.sim.Sim", "on_add")
def on_sim_added(original, self, *args, **kwargs):
    print(f"A new Sim is being added to the world!")
    return original(self, *args, **kwargs)
```

### Register Your Mod

```python
from stark_framework.core.registry import ModRegistry

ModRegistry.register(
    mod_id="my_awesome_mod",
    name="My Awesome Mod",
    version="1.0.0",
    author="Your Name",
    dependencies=["stark_framework"],
)
```

### Structured Logging

```python
from stark_framework.utils.logging import get_logger

log = get_logger("my_awesome_mod")
log.info("Mod loaded successfully")
log.warn("Tuning override detected", tuning_id="0x1A2B3C4D")
log.error("Failed to apply buff", sim_id=12345, buff="happy_buff")
```

## Architecture

```
stark_framework/
  core/
    events.py       -- Typed event bus (the centerpiece)
    registry.py     -- Module registry with conflict detection
    injection.py    -- Clean injection decorators
    diagnostics.py  -- Error tracking and mod conflict detection
  services/
    sim_service.py        -- Sim data access helpers
    household_service.py  -- Household management
    world_service.py      -- World/lot/zone helpers
  utils/
    tuning.py    -- XML tuning helpers
    logging.py   -- Structured logging for mod developers
```

## License

MIT License. See [LICENSE](LICENSE) for details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Write tests for new functionality
4. Submit a pull request

Built by [Stark Labs](https://github.com/stark-studio-labs).
