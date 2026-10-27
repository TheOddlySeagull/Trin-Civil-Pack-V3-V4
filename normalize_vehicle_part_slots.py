#!/usr/bin/env python3
"""Normalize vehicle part-slot order without breaking numbered MTS variables.

MTS versions that resolve numbered variables by their physical part slot need the
engine slot to have a predictable index.  This tool puts all road-wheel slots
first, followed by all engine slots.  It then rewrites every numbered variable
reference in the vehicle JSON to point to the same slot after the move.

Spare wheels are deliberately not considered road wheels.  This is important
for the Trainingor: its replacement wheel remains with the other accessories,
after the licence-plate slots, rather than being moved to the front.

Run without --apply first.  It performs no writes and prints the planned moves.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator


DEFAULT_ASSETS_ROOT = Path("mccore/src/main/resources/assets")
INDEXED_VARIABLE = re.compile(r"^(.*_)(\d+)$")

# Scalar fields whose value is an MTS animation variable.  Lists below a key
# ending in "Variables" are handled too (interactableVariables, linkedVariables,
# visibilityVariables, etc.).
VARIABLE_FIELD_NAMES = {"variable", "litVariable"}
MODERN_ENGINE_VARIABLES = {
    "isAutomatic",
    "maxRPM",
    "maxSafeRPM",
    "revlimitRPM",
    "revlimitBounce",
    "revResistance",
    "idleRPM",
    "startRPM",
    "stallRPM",
    "starterPower",
    "fuelConsumption",
    "heatingCoefficient",
    "coolingCoefficient",
    "superchargerFuelConsumption",
    "superchargerEfficiency",
    "gearRatio",
    "forceShift",
    "engineWearFactor",
    "engineWinddownRate",
    "jetPowerFactor",
    "bypassRatio",
}


@dataclass(frozen=True)
class Migration:
    original_slots: int
    road_wheels: int
    engines: int
    old_to_new: dict[int, int]

    @property
    def engine_start(self) -> int:
        """One-based index of the first engine after normalization."""
        return self.road_wheels + 1


def is_road_wheel(slot: dict[str, Any]) -> bool:
    """Return true for a driving wheel, but never for a spare/replacement wheel."""
    return (
        not slot.get("isSpare", False)
        and any(str(part_type).startswith("ground_wheel") for part_type in slot.get("types", []))
    )


def is_engine(slot: dict[str, Any]) -> bool:
    return any(str(part_type).startswith("engine") for part_type in slot.get("types", []))


def plan_migration(parts: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], Migration] | None:
    """Return normalized parts and the one-based old-to-new slot mapping.

    A file with no engine is left untouched: it may be a trailer, an incomplete
    example, or a vehicle intentionally driven by a non-engine part.
    """
    road_wheel_indexes = [index for index, slot in enumerate(parts) if is_road_wheel(slot)]
    engine_indexes = [index for index, slot in enumerate(parts) if is_engine(slot)]
    if not engine_indexes:
        return None

    # Keep relative order inside each group.  The remaining slots (including
    # Trainingor's isSpare replacement wheel) retain their relative order too.
    front_indexes = road_wheel_indexes + engine_indexes
    front_set = set(front_indexes)
    ordered_indexes = front_indexes + [index for index in range(len(parts)) if index not in front_set]
    normalized_parts = [parts[index] for index in ordered_indexes]
    old_to_new = {old_index + 1: new_index + 1 for new_index, old_index in enumerate(ordered_indexes)}

    return normalized_parts, Migration(
        original_slots=len(parts),
        road_wheels=len(road_wheel_indexes),
        engines=len(engine_indexes),
        old_to_new=old_to_new,
    )


def remap_variable(
    value: str, old_to_new: dict[int, int], engine_slots: list[int]
) -> tuple[str, bool]:
    """Remap a numbered MTS variable while respecting engine ordinals.

    The legacy ``engine_*_N`` family uses N to refer to the Nth engine.  It is
    therefore mapped to the new physical slot of that engine, not by treating N
    as an old global slot.  Other numbered variables reference global slots and
    follow the complete old-to-new permutation.
    """
    match = INDEXED_VARIABLE.fullmatch(value)
    if not match:
        return value, False
    old_index = int(match.group(2))
    variable_stem = match.group(1)[:-1]  # Strip the separator before the suffix.
    is_engine_variable = variable_stem.startswith("engine_") or variable_stem in MODERN_ENGINE_VARIABLES
    if is_engine_variable and 1 <= old_index <= len(engine_slots):
        new_index = engine_slots[old_index - 1]
    else:
        new_index = old_to_new.get(old_index)
    if new_index is None or new_index == old_index:
        return value, False
    return f"{match.group(1)}{new_index}", True


def remap_variables(
    value: Any, old_to_new: dict[int, int], engine_slots: list[int], variable_context: bool = False
) -> tuple[Any, int]:
    """Recursively rewrite variable-valued fields, never IDs or object names."""
    if isinstance(value, str):
        if not variable_context:
            return value, 0
        updated, changed = remap_variable(value, old_to_new, engine_slots)
        return updated, int(changed)

    if isinstance(value, list):
        changes = 0
        updated_list = []
        for item in value:
            updated, item_changes = remap_variables(item, old_to_new, engine_slots, variable_context)
            updated_list.append(updated)
            changes += item_changes
        return updated_list, changes

    if isinstance(value, dict):
        changes = 0
        updated_dict: dict[str, Any] = {}
        for key, item in value.items():
            # Lists such as interactableVariables and linkedVariables contain
            # variable expressions.  Individual variable/litVariable fields do
            # too.  Deliberately do not treat names, objectName, or IDs as vars.
            is_variable_value = key in VARIABLE_FIELD_NAMES or key.endswith("Variables")
            updated, item_changes = remap_variables(item, old_to_new, engine_slots, is_variable_value)
            updated_dict[key] = updated
            changes += item_changes
        return updated_dict, changes

    return value, 0


def fix_clutch_visibility(data: dict[str, Any], first_engine_slot: int) -> int:
    """Make clutch objects visible exactly when the first engine is manual.

    This is deliberately limited to the named clutch object.  It does not alter
    unrelated visibility rules, even if they happen to use an engine variable.
    """
    rendering = data.get("rendering")
    if not isinstance(rendering, dict):
        return 0
    animated_objects = rendering.get("animatedObjects")
    if not isinstance(animated_objects, list):
        return 0

    changes = 0
    for animated_object in animated_objects:
        if not isinstance(animated_object, dict) or animated_object.get("objectName") != "clutch":
            continue
        animations = animated_object.get("animations")
        if not isinstance(animations, list):
            continue
        for animation in animations:
            if not isinstance(animation, dict) or animation.get("animationType") != "visibility":
                continue
            current_variable = str(animation.get("variable", "")).lstrip("!")
            if not (current_variable.startswith("engine_") or current_variable.startswith("isAutomatic")):
                continue
            replacement = {
                "variable": f"isAutomatic_{first_engine_slot}",
                "clampMin": 0.0,
                "clampMax": 0.0,
            }
            for key, replacement_value in replacement.items():
                if animation.get(key) != replacement_value:
                    animation[key] = replacement_value
                    changes += 1
    return changes


def vehicle_json_files(assets_root: Path) -> Iterator[Path]:
    yield from sorted(assets_root.glob("*/jsondefs/vehicles/**/*.json"))


def process_file(path: Path, apply: bool) -> tuple[Migration | None, int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    parts = data.get("parts")
    if not isinstance(parts, list) or not all(isinstance(slot, dict) for slot in parts):
        return None, 0

    planned = plan_migration(parts)
    if planned is None:
        return None, 0
    normalized_parts, migration = planned
    normalized_engine_slots = list(range(migration.engine_start, migration.engine_start + migration.engines))
    updated_data, variable_changes = remap_variables(data, migration.old_to_new, normalized_engine_slots)
    updated_data["parts"] = normalized_parts
    clutch_changes = fix_clutch_visibility(updated_data, migration.engine_start)

    if apply and updated_data != data:
        path.write_text(json.dumps(updated_data, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")
    return migration, variable_changes + clutch_changes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--assets-root",
        type=Path,
        default=DEFAULT_ASSETS_ROOT,
        help=f"assets directory to scan (default: {DEFAULT_ASSETS_ROOT})",
    )
    parser.add_argument("--apply", action="store_true", help="write the normalized JSON files (default: dry run)")
    args = parser.parse_args()

    files = list(vehicle_json_files(args.assets_root))
    if not files:
        print(f"No vehicle JSON files found below {args.assets_root}", file=sys.stderr)
        return 2

    changed_files = 0
    total_variable_changes = 0
    skipped = 0
    for path in files:
        migration, variable_changes = process_file(path, args.apply)
        if migration is None:
            skipped += 1
            continue
        changed_files += 1
        total_variable_changes += variable_changes
        relative_path = path.relative_to(args.assets_root)
        print(
            f"{relative_path}: {migration.road_wheels} road wheel(s), {migration.engines} engine(s), "
            f"first engine -> slot {migration.engine_start}; {variable_changes} variable reference(s) remapped"
        )

    mode = "Applied" if args.apply else "Dry run"
    print(
        f"{mode}: {changed_files} vehicle file(s) with engines, {skipped} without engines, "
        f"{total_variable_changes} numbered variable reference(s) remapped."
    )
    if not args.apply:
        print("Review the output, commit or stash your worktree, then repeat with --apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
