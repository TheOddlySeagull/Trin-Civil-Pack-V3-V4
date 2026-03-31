import argparse
import json
import shutil
from pathlib import Path


def collect_item_pngs(assets_dir: Path) -> list[Path]:
    png_files: list[Path] = []
    for pack_dir in assets_dir.iterdir():
        if not pack_dir.is_dir():
            continue

        textures_dir = pack_dir / "textures"
        if not textures_dir.exists() or not textures_dir.is_dir():
            continue

        for texture_subdir in ("items", "item"):
            texture_root = textures_dir / texture_subdir
            if not texture_root.exists() or not texture_root.is_dir():
                continue

            png_files.extend(path for path in texture_root.rglob("*.png") if path.is_file())
            png_files.extend(path for path in texture_root.rglob("*.PNG") if path.is_file())

    return sorted(set(png_files))


def build_model_json(pack_id: str, texture_name: str) -> dict:
    return {
        "parent": "mts:item/basic",
        "textures": {
            "layer0": f"{pack_id}:item/{texture_name}",
        },
    }


def collect_pngs(directory: Path) -> list[Path]:
    if not directory.exists() or not directory.is_dir():
        return []
    return sorted(
        set(
            [path for path in directory.rglob("*.png") if path.is_file()]
            + [path for path in directory.rglob("*.PNG") if path.is_file()]
        )
    )


def get_revert_destination_root(pack_dir: Path, textures_dir: Path) -> Path:
    items_dir = textures_dir / "items"
    parts_dir = items_dir / "parts"
    vehicles_dir = items_dir / "vehicles"

    parts_exists = parts_dir.exists() and parts_dir.is_dir()
    vehicles_exists = vehicles_dir.exists() and vehicles_dir.is_dir()

    if parts_exists and not vehicles_exists:
        return parts_dir
    if vehicles_exists and not parts_exists:
        return vehicles_dir
    if pack_dir.name.endswith("_parts"):
        return parts_dir

    return vehicles_dir


def generate_models(base_path: Path) -> tuple[int, int]:
    assets_dir = base_path / "mccore" / "src" / "main" / "resources" / "assets"
    output_dir = assets_dir / "mts" / "models" / "item"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not assets_dir.exists():
        raise FileNotFoundError(f"Assets directory not found: {assets_dir}")

    png_files = collect_item_pngs(assets_dir)

    written_count = 0
    for png_path in png_files:
        try:
            pack_id = png_path.relative_to(assets_dir).parts[0]
        except (ValueError, IndexError):
            continue

        texture_name = png_path.stem
        model_name = f"{pack_id}.{texture_name}.json"
        model_path = output_dir / model_name

        model_data = build_model_json(pack_id, texture_name)
        model_path.write_text(json.dumps(model_data, separators=(",", ":")), encoding="utf-8")
        written_count += 1

    return len(png_files), written_count


def move_item_pngs(base_path: Path, revert: bool) -> tuple[int, int, int]:
    assets_dir = base_path / "mccore" / "src" / "main" / "resources" / "assets"
    if not assets_dir.exists():
        raise FileNotFoundError(f"Assets directory not found: {assets_dir}")

    scanned_count = 0
    moved_count = 0
    replaced_count = 0

    for pack_dir in assets_dir.iterdir():
        if not pack_dir.is_dir():
            continue

        textures_dir = pack_dir / "textures"
        if not textures_dir.exists() or not textures_dir.is_dir():
            continue

        if revert:
            source_root = textures_dir / "item"
            destination_root = get_revert_destination_root(pack_dir, textures_dir)

            source_files = collect_pngs(source_root)
            scanned_count += len(source_files)

            for source_file in source_files:
                relative_path = source_file.relative_to(source_root)
                destination_file = destination_root / relative_path
                destination_file.parent.mkdir(parents=True, exist_ok=True)

                if destination_file.exists():
                    destination_file.unlink()
                    replaced_count += 1

                shutil.move(str(source_file), str(destination_file))
                moved_count += 1
        else:
            destination_root = textures_dir / "item"
            source_roots = [
                textures_dir / "items" / "vehicles",
                textures_dir / "items" / "parts",
            ]

            for source_root in source_roots:
                source_files = collect_pngs(source_root)
                scanned_count += len(source_files)

                for source_file in source_files:
                    relative_path = source_file.relative_to(source_root)
                    destination_file = destination_root / relative_path
                    destination_file.parent.mkdir(parents=True, exist_ok=True)

                    if destination_file.exists():
                        destination_file.unlink()
                        replaced_count += 1

                    shutil.move(str(source_file), str(destination_file))
                    moved_count += 1

    return scanned_count, moved_count, replaced_count


def cleanup_models(base_path: Path) -> int:
    """Remove generated item model JSON files."""
    output_dir = base_path / "mccore" / "src" / "main" / "resources" / "assets" / "mts" / "models" / "item"

    if not output_dir.exists():
        return 0

    deleted_count = 0
    for model_file in output_dir.glob("*.json"):
        if model_file.is_file():
            model_file.unlink()
            deleted_count += 1

    return deleted_count


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Generate item model JSON files or move item PNGs between "
            "textures/items/vehicles and textures/item."
        )
    )
    parser.add_argument(
        "--base-path",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Project root path. Defaults to this script's directory.",
    )
    parser.add_argument(
        "--mode",
        choices=("generate-json", "move-png", "cleanup"),
        default="generate-json",
        help="Operation mode: generate JSON files, move PNG files, or cleanup generated JSON files.",
    )
    parser.add_argument(
        "--revert",
        action="store_true",
        help="With --mode move-png, move from textures/item back to textures/items/vehicles.",
    )
    args = parser.parse_args()

    if args.mode == "generate-json":
        if args.revert:
            parser.error("--revert can only be used with --mode move-png")

        scanned, written = generate_models(args.base_path.resolve())
        print(f"Scanned {scanned} PNG texture(s), wrote {written} model JSON file(s).")
        return

    if args.mode == "cleanup":
        if args.revert:
            parser.error("--revert can only be used with --mode move-png")

        deleted = cleanup_models(args.base_path.resolve())
        print(f"Deleted {deleted} model JSON file(s).")
        return

    scanned, moved, replaced = move_item_pngs(args.base_path.resolve(), args.revert)
    print(
        f"Scanned {scanned} PNG texture(s), moved {moved} file(s), "
        f"replaced {replaced} existing destination file(s)."
    )


if __name__ == "__main__":
    main()
