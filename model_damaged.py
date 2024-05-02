import os
import json
import random
import argparse

# Parse the folder path from the command line
parser = argparse.ArgumentParser(description="Add 'damaged' animations to JSON files")
parser.add_argument("--folder_path", required=True, help="Path to the folder containing JSON files")
args = parser.parse_args()
folder_path = args.folder_path.replace("\\", "/")

# Function to add "damaged" animations to a JSON file
def add_damaged_animation(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)

    print(f"inside a json file: {json_file}")

    for obj in data["rendering"]["animatedObjects"]:
        print(f"inside an object: {obj['objectName']}")
        #print the number of animations in the object
        print(f"number of animations: {len(obj.get('animations', []))}")
        # if this animation has not already been added
        if not any(anim.get("variable", None) == "damage_totaled" for anim in obj.get("animations", []) ):
            print("damage_totaled animation does not exist")
            # Iterate through each animation in the object
            for anim in obj.get("animations", []):
                # If animation not of "variable" "damage_totaled"
                if anim.get("variable", None) != "damage_totaled":
                    print(f"inside an animation: type {anim['animationType']}, variable {anim['variable']}")
                    # inside the animation, get the "centerPoint" key
                    center_point = anim.get("centerPoint", None)
                    print(f"center point: {center_point}")

                    # Now, in animations, we need to add a new animation for the total damage
                    '''
                    expected:

                    {
                        "animationType": "rotation",
                        "variable": "damage_totaled",
                        "centerPoint": {centerPoint},
                        "axis": [x, y, z]
                    }
                    '''
                    # Create a new animation
                    new_anim = {
                        "animationType": "rotation",
                        "variable": "damage_totaled",
                        "centerPoint": center_point,
                        "axis": [random.uniform(-10, 10), random.uniform(-10, 10), random.uniform(-10, 10)]
                    }
                    print(f"new animation: {new_anim}")

                    # Add the new animation to the object
                    obj["animations"].append(new_anim)
        else:
            print("damage_totaled animation already exists")
            # for all the animation, if of type "damage_totaled", but "centerPoint": null, then delete the animation
            for anim in obj.get("animations", []):
                if anim.get("variable", None) == "damage_totaled" and anim.get("centerPoint", None) == None:
                    obj["animations"].remove(anim)
                    print("removed damage_totaled animation due to null centerPoint")
            
        

    # Save the modified JSON file
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=4)

# Iterate through each JSON file in the folder and subfolders
for root, _, files in os.walk(folder_path):
    for file_name in files:
        if file_name.endswith(".json"):
            file_path = os.path.join(root, file_name)
            # try to add a damaged animation to the file
            try:
                add_damaged_animation(file_path)
                print(f"Modified: {file_path}")
            except Exception as e:
                print(f"Error processing {file_path}: {e}")

print("Done!")
