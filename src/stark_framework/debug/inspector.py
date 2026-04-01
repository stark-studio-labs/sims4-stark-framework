"""
Sim Inspector -- extract and format sim stats for debugging.

Pulls traits, buffs, skills, career, household, relationships, and funds from
a sim_info object. Every attribute access is wrapped in try/except because the
game API surface varies across patches and DLC installs.

Usage:
    from stark_framework.debug.inspector import SimInspector

    inspector = SimInspector()

    # Get raw data dict
    data = inspector.inspect_sim(sim_info)
    # {"name": "Bella Goth", "traits": [...], "buffs": [...], ...}

    # Get a formatted report string
    report = inspector.format_report(data)
    print(report)
"""


class SimInspector:
    """Extracts and formats debug data from sim_info objects.

    Designed to be resilient -- every attribute read is wrapped in try/except
    so a missing DLC or changed API doesn't crash the inspector.
    """

    def inspect_sim(self, sim_info):
        """Extract all available stats from a sim_info object.

        Args:
            sim_info: A Sims 4 sim_info instance (or mock with similar attrs).

        Returns:
            Dict with keys: name, sim_id, traits, buffs, skills, career,
            household, relationships, funds. Missing data returns empty
            lists/strings/0 rather than raising.
        """
        data = {}

        # Basic identity
        data["name"] = self._safe_get_name(sim_info)
        data["sim_id"] = self._safe_attr(sim_info, "sim_id", 0)

        # Traits
        data["traits"] = self._safe_get_traits(sim_info)

        # Buffs
        data["buffs"] = self._safe_get_buffs(sim_info)

        # Skills
        data["skills"] = self._safe_get_skills(sim_info)

        # Career
        data["career"] = self._safe_get_career(sim_info)

        # Household
        data["household"] = self._safe_get_household(sim_info)

        # Relationships
        data["relationships"] = self._safe_get_relationships(sim_info)

        # Funds
        data["funds"] = self._safe_get_funds(sim_info)

        return data

    def format_report(self, sim_data):
        """Format an inspect_sim result as a human-readable string.

        Args:
            sim_data: Dict returned by inspect_sim().

        Returns:
            Multi-line formatted report string.
        """
        lines = []
        lines.append(f"=== Sim Inspector: {sim_data.get('name', 'Unknown')} ===")
        lines.append(f"Sim ID: {sim_data.get('sim_id', 'N/A')}")
        lines.append("")

        # Traits
        traits = sim_data.get("traits", [])
        lines.append(f"Traits ({len(traits)}):")
        for t in traits:
            lines.append(f"  - {t}")
        if not traits:
            lines.append("  (none)")

        lines.append("")

        # Buffs
        buffs = sim_data.get("buffs", [])
        lines.append(f"Buffs ({len(buffs)}):")
        for b in buffs:
            lines.append(f"  - {b}")
        if not buffs:
            lines.append("  (none)")

        lines.append("")

        # Skills
        skills = sim_data.get("skills", [])
        lines.append(f"Skills ({len(skills)}):")
        for s in skills:
            lines.append(f"  - {s}")
        if not skills:
            lines.append("  (none)")

        lines.append("")

        # Career
        career = sim_data.get("career", "")
        lines.append(f"Career: {career or '(none)'}")

        # Household
        household = sim_data.get("household", "")
        lines.append(f"Household: {household or '(none)'}")

        # Funds
        funds = sim_data.get("funds", 0)
        lines.append(f"Funds: {funds:,}")

        lines.append("")

        # Relationships
        relationships = sim_data.get("relationships", [])
        lines.append(f"Relationships ({len(relationships)}):")
        for r in relationships:
            lines.append(f"  - {r}")
        if not relationships:
            lines.append("  (none)")

        lines.append("")
        lines.append("=== End Report ===")
        return "\n".join(lines)

    # ── Safe attribute access ───────────────────────────────────────

    @staticmethod
    def _safe_attr(obj, attr, default=None):
        """Get an attribute safely, returning default on any error."""
        try:
            return getattr(obj, attr, default)
        except Exception:
            return default

    def _safe_get_name(self, sim_info):
        """Extract sim name, handling various API shapes."""
        try:
            first = getattr(sim_info, "first_name", "")
            last = getattr(sim_info, "last_name", "")
            if first or last:
                return f"{first} {last}".strip()
        except Exception:
            pass
        return "Unknown"

    def _safe_get_traits(self, sim_info):
        """Extract trait names from sim_info."""
        try:
            trait_tracker = getattr(sim_info, "trait_tracker", None)
            if trait_tracker is None:
                # Fallback: traits might be a direct attribute
                traits = getattr(sim_info, "traits", [])
                return [str(t) for t in traits]

            equipped = getattr(trait_tracker, "equipped_traits", [])
            return [str(t) for t in equipped]
        except Exception:
            return []

    def _safe_get_buffs(self, sim_info):
        """Extract active buff names from sim_info."""
        try:
            buff_component = getattr(sim_info, "Buffs", None)
            if buff_component is None:
                buff_component = getattr(sim_info, "buffs", None)
            if buff_component is None:
                return []

            # Try iterable of active buffs
            active = getattr(buff_component, "active_buffs", [])
            return [str(b) for b in active]
        except Exception:
            return []

    def _safe_get_skills(self, sim_info):
        """Extract skill names and levels from sim_info."""
        try:
            tracker = getattr(sim_info, "skill_tracker", None)
            if tracker is None:
                skills = getattr(sim_info, "skills", [])
                return [str(s) for s in skills]

            all_skills = getattr(tracker, "all_skills", [])
            result = []
            for skill in all_skills:
                name = getattr(skill, "name", str(skill))
                level = getattr(skill, "level", "?")
                result.append(f"{name} (Lv {level})")
            return result
        except Exception:
            return []

    def _safe_get_career(self, sim_info):
        """Extract career info from sim_info."""
        try:
            career_tracker = getattr(sim_info, "career_tracker", None)
            if career_tracker is None:
                return getattr(sim_info, "career", "")

            careers = getattr(career_tracker, "careers", {})
            if not careers:
                return ""

            # Return first career found
            for career in careers.values():
                name = getattr(career, "name", str(career))
                level = getattr(career, "level", "?")
                return f"{name} (Lv {level})"
            return ""
        except Exception:
            return ""

    def _safe_get_household(self, sim_info):
        """Extract household name from sim_info."""
        try:
            household = getattr(sim_info, "household", None)
            if household is None:
                return ""
            return getattr(household, "name", str(household))
        except Exception:
            return ""

    def _safe_get_relationships(self, sim_info):
        """Extract relationship summaries from sim_info."""
        try:
            tracker = getattr(sim_info, "relationship_tracker", None)
            if tracker is None:
                rels = getattr(sim_info, "relationships", [])
                return [str(r) for r in rels]

            relationships = getattr(tracker, "relationships", [])
            result = []
            for rel in relationships:
                target = getattr(rel, "target_name", str(rel))
                rel_type = getattr(rel, "type", "")
                if rel_type:
                    result.append(f"{target} ({rel_type})")
                else:
                    result.append(str(target))
            return result
        except Exception:
            return []

    def _safe_get_funds(self, sim_info):
        """Extract household funds from sim_info."""
        try:
            household = getattr(sim_info, "household", None)
            if household is None:
                return 0
            funds_obj = getattr(household, "funds", None)
            if funds_obj is None:
                return 0
            # funds might be an int or an object with a .money attribute
            if isinstance(funds_obj, (int, float)):
                return int(funds_obj)
            return int(getattr(funds_obj, "money", 0))
        except Exception:
            return 0
