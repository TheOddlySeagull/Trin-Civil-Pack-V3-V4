import os
import json
import random

# Path to the folder containing the JSON files
folder_path = "E:/Documents Global/Programmation/Trin/Trin Civil Pack V3/mccore/src/main/resources/assets/iv_tcp_v3_txs/jsondefs/vehicles"

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
        else:
            print("damage_totaled animation already exists")
            continue
            
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

    # Save the modified JSON file
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=4)

# Iterate through each JSON file in the folder
for filename in os.listdir(folder_path):
    if filename.endswith(".json"):
        file_path = os.path.join(folder_path, filename)
        add_damaged_animation(file_path)

print("Done!")
