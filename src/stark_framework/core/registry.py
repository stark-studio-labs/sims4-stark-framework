"""
Module Registry -- tracks loaded mods, detects conflicts, resolves dependencies.

Every mod should register itself on load so the framework can:
- Detect duplicate mod IDs
- Warn about version conflicts
- Verify dependencies are present before activation
- Provide a single source of truth for "what's installed"

Usage:
    from stark_framework.core.registry import ModRegistry

    # Register your mod (call once at mod startup)
    ModRegistry.register(
        mod_id="alice_vampire_overhaul",
        name="Vampire Overhaul",
        version="2.1.0",
        author="Alice",
        dependencies=["stark_framework"],
        conflicts=["bobs_vampire_mod"],
    )

    # Check if a mod is loaded
    if ModRegistry.is_loaded("some_other_mod"):
        enable_compat_patch()

    # Get mod info
    info = ModRegistry.get("alice_vampire_overhaul")
    print(info["version"])  # "2.1.0"

    # List all loaded mods
    for mod_id, info in ModRegistry.all_mods().items():
        print(f"{info['name']} v{info['version']} by {info['author']}")
"""


class ConflictError(Exception):
    """Raised when a mod conflicts with an already-loaded mod."""
    pass


class DependencyError(Exception):
    """Raised when a mod's dependencies are not satisfied."""
    pass


class ModRegistry:
    """Central registry for all loaded mods.

    Mods register themselves at startup. The registry tracks metadata,
    detects conflicts, and validates dependencies.
    """

    _mods = {}  # type: dict[str, dict]

    @classmethod
    def register(cls, mod_id, name, version, author="Unknown",
                 dependencies=None, conflicts=None, metadata=None):
        """Register a mod with the framework.

        Args:
            mod_id: Unique identifier (e.g. "alice_vampire_overhaul").
            name: Human-readable mod name.
            version: Semantic version string (e.g. "2.1.0").
            author: Mod author name.
            dependencies: List of mod_ids that must be loaded first.
            conflicts: List of mod_ids that cannot coexist.
            metadata: Optional dict of arbitrary extra data.

        Raises:
            ConflictError: If mod_id is already registered or conflicts
                with a loaded mod.
            DependencyError: If required dependencies are missing.
        """
        dependencies = dependencies or []
        conflicts = conflicts or []

        # Check for duplicate registration
        if mod_id in cls._mods:
            existing = cls._mods[mod_id]
            raise ConflictError(
                f"Mod '{mod_id}' is already registered "
                f"(v{existing['version']} by {existing['author']}). "
                f"Duplicate mod files?"
            )

        # Check for declared conflicts
        for conflict_id in conflicts:
            if conflict_id in cls._mods:
                raise ConflictError(
                    f"Mod '{mod_id}' conflicts with '{conflict_id}' "
                    f"(v{cls._mods[conflict_id]['version']}). "
                    f"Remove one of them."
                )

        # Check for reverse conflicts (another mod declared us as a conflict)
        for loaded_id, loaded_info in cls._mods.items():
            if mod_id in loaded_info.get("conflicts", []):
                raise ConflictError(
                    f"Mod '{loaded_id}' has declared a conflict with '{mod_id}'. "
                    f"Remove one of them."
                )

        # Check dependencies (stark_framework itself is always available)
        missing = []
        for dep_id in dependencies:
            if dep_id == "stark_framework":
                continue  # Always satisfied -- we are the framework
            if dep_id not in cls._mods:
                missing.append(dep_id)

        if missing:
            raise DependencyError(
                f"Mod '{mod_id}' requires mods that are not loaded: "
                f"{', '.join(missing)}. Install them or adjust load order."
            )

        cls._mods[mod_id] = {
            "mod_id": mod_id,
            "name": name,
            "version": version,
            "author": author,
            "dependencies": dependencies,
            "conflicts": conflicts,
            "metadata": metadata or {},
        }

    @classmethod
    def unregister(cls, mod_id):
        """Remove a mod from the registry.

        Args:
            mod_id: The mod to remove.

        Returns:
            True if found and removed, False otherwise.
        """
        return cls._mods.pop(mod_id, None) is not None

    @classmethod
    def is_loaded(cls, mod_id):
        """Check if a mod is registered.

        Args:
            mod_id: The mod identifier to check.

        Returns:
            True if the mod is currently registered.
        """
        return mod_id in cls._mods

    @classmethod
    def get(cls, mod_id):
        """Get metadata for a registered mod.

        Args:
            mod_id: The mod identifier.

        Returns:
            Dict with mod info, or None if not registered.
        """
        return cls._mods.get(mod_id)

    @classmethod
    def all_mods(cls):
        """Return a copy of all registered mods.

        Returns:
            Dict mapping mod_id to mod info dicts.
        """
        return dict(cls._mods)

    @classmethod
    def clear(cls):
        """Remove all registered mods. For testing only."""
        cls._mods.clear()
