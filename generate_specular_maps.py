import os
import pathlib
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed

# === Configuration ===
COLOR_MAP = {
    "#99CCCC": "#FFFFFF",
    "#B8B7B5": "#999999",
    "#989794": "#999999",
    "#444444": "#808080",
    "#686868": "#808080",
    "#E6E6E6": "#808080",
    "#99FFFF": "#808080",
    "#FF0000": "#808080",
    "#B70000": "#808080",
    "#874920": "#808080",
    "#CC3300": "#0C0C0C",
    "#FFCC00": "#0C0C0C",
    "#FFFFCC": "#0C0C0C",
    "#990000": "#0C0C0C",
    "#191919": "#0C0C0C",
    "#111111": "#0C0C0C",
    "#050505": "#0C0C0C",
    "#070707": "#0C0C0C",
    "#0F0F0F": "#0C0C0C",
    "#142168": "#0C0C0C",
    "#191819": "#0C0C0C",
    "#1A1A1A": "#0C0C0C",
    "#271101": "#0C0C0C",
    "#361701": "#0C0C0C",
    "#3A3A3A": "#0C0C0C",
    "#424242": "#0C0C0C",
    "#472916": "#0C0C0C",
    "#515151": "#0C0C0C",
    "#521A1C": "#0C0C0C",
    "#666666": "#0C0C0C",
    "#802625": "#0C0C0C",
    "#828282": "#0C0C0C",
    "#BFBFBF": "#0C0C0C",
    "#CCCCCC": "#0C0C0C",
    "#CEBC68": "#0C0C0C",
    "#E5E5E5": "#0C0C0C",
    "#EEE8C9": "#0C0C0C",
    "#FEF6D6": "#0C0C0C",
}
DEFAULT_COLOR = "#666666"
NOISE_TOLERANCE = 0
OVERRIDE_EXISTING = False
USE_MULTITHREADING = False  # Set to True to enable multithreading
BLACKLIST = {"vignette.png"}  # Add filenames to blacklist

# === Paths ===
# Allow overriding via BASE_PATH env var, default to current working directory (CI-friendly)
BASE_PATH = os.path.abspath(os.getenv("BASE_PATH", os.getcwd()))
EXCLUDE_PATH = os.path.join(BASE_PATH, "mccore", "build")

# === Helper Functions ===
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    return "#{:02X}{:02X}{:02X}".format(*rgb)

def is_valid_image_path(path):
    parts = pathlib.Path(path).parts
    if "assets" in parts:
        idx = parts.index("assets")
        if "items" in parts[idx:]:
            return False
    if pathlib.Path(path).name in BLACKLIST:  # Check if file is in blacklist
        return False
    return True

def color_within_tolerance(pixel_rgb, target_rgb, tolerance):
    return all(abs(p - t) <= tolerance for p, t in zip(pixel_rgb, target_rgb))

def map_pixel_color(pixel_rgb):
    matched_colors = []
    for k_hex, v_hex in COLOR_MAP.items():
        target_rgb = hex_to_rgb(k_hex)
        if color_within_tolerance(pixel_rgb, target_rgb, NOISE_TOLERANCE):
            matched_colors.append(hex_to_rgb(v_hex))
    if matched_colors:
        # Choose the darkest color (lowest sum of RGB values)
        return min(matched_colors, key=lambda rgb: sum(rgb))
    return hex_to_rgb(DEFAULT_COLOR)

def process_image(image_path):
    specular_name = os.path.splitext(image_path)[0] + "_s.png"
    if not OVERRIDE_EXISTING and os.path.exists(specular_name):
        return
    try:
        with Image.open(image_path).convert("RGBA") as img:
            pixels = img.load()
            for y in range(img.height):
                for x in range(img.width):
                    r, g, b, a = pixels[x, y]
                    if a == 0:
                        continue
                    mapped_rgb = map_pixel_color((r, g, b))
                    pixels[x, y] = (*mapped_rgb, a)
            img.save(specular_name)
            print(f"Generated specular map for: {os.path.relpath(image_path, BASE_PATH)}")
    except Exception as e:
        print(f"Error processing {image_path}: {e}")

def cleanup_orphans(valid_sources):
    for dirpath, _, filenames in os.walk(BASE_PATH):
        for file in filenames:
            if file.endswith("_s.png"):
                specular_path = os.path.join(dirpath, file)
                source_path = specular_path[:-6] + ".png"
                if os.path.normpath(source_path) not in valid_sources:
                    os.remove(specular_path)
                    print(f"Removed orphaned specular map: {os.path.relpath(specular_path, BASE_PATH)}")

# === Main ===
def main():
    found_sources = set()
    images_to_process = []

    for dirpath, _, filenames in os.walk(BASE_PATH):
        if os.path.commonpath([EXCLUDE_PATH, dirpath]) == EXCLUDE_PATH:
            continue

        for file in filenames:
            if file.lower().endswith(".png") and not file.lower().endswith("_s.png"):
                full_path = os.path.join(dirpath, file)
                if not is_valid_image_path(full_path):
                    continue
                found_sources.add(os.path.normpath(full_path))
                images_to_process.append(full_path)

    if USE_MULTITHREADING:
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(process_image, img_path) for img_path in images_to_process]
            for _ in as_completed(futures):
                pass
    else:
        for img_path in images_to_process:
            process_image(img_path)

    cleanup_orphans(found_sources)

if __name__ == "__main__":
    main()
