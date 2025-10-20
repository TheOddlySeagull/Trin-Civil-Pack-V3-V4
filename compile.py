import subprocess
import os
import sys
import argparse
from pathlib import Path

# Parse arguments
parser = argparse.ArgumentParser(description="Compile Trin Civil Pack")
parser.add_argument("--skip-1165", action="store_true", help="Skip compiling for 1.16.5")
args = parser.parse_args()

ROOT = Path(__file__).resolve().parent

def py_exec(*script_and_args: str):
    """Run a Python script with the current interpreter, raise on failure."""
    script_path = ROOT / script_and_args[0]
    args = [str(script_path)] + list(script_and_args[1:])
    subprocess.run([sys.executable] + args, check=True)

def gradle_exec(*gradle_args: str):
    """Run the Gradle wrapper in a cross-platform way, raise on failure."""
    gradle_cmd = "gradlew.bat" if os.name == "nt" else "./gradlew"
    subprocess.run([gradle_cmd] + list(gradle_args), check=True)

# 1) Generate specular maps
py_exec("generate_specular_maps.py")

# 2) Transform IDs for 1.12.2 build (reverse)
py_exec("1-12-2_1-16-5_ID_transformer.py", "--reverse")

# 3) Build Forge 1.12.2
gradle_exec("buildForge1122")

# 4) Transform IDs forward for 1.16.5
py_exec("1-12-2_1-16-5_ID_transformer.py")

# 5) Build Forge 1.16.5 (unless skipped)
if not args.skip_1165:
    gradle_exec("buildForge1165")

# 6) Restore IDs back to 1.12.2 state for a clean repo
py_exec("1-12-2_1-16-5_ID_transformer.py", "--reverse")
