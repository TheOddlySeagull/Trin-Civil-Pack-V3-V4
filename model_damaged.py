import json
import os
import random

def add_damaged_animation(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    for obj in data["rendering"]["animatedObjects"]:
        for anim in obj["animations"]:
            if anim["animationType"] == "rotation" and anim["variable"] == "damage_totaled":
                center_point = anim["centerPoint"]
                new_animation = {
                    "animationType": "rotation",
                    "variable": "damaged",
                    "centerPoint": center_point,
                    "axis": [random.uniform(2, 8), random.uniform(2, 8), random.uniform(2, 8)]
                }
                obj["animations"].append(new_animation)
                break
    
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=4)

# Path to the directory containing all the JSON files
directory = 'E:/Documents Global/Programmation/Trin/Trin Civil Pack V3/mccore/src/main/resources/assets/iv_tcp_v3_txs/jsondefs/vehicles'

# Iterate through all JSON files in the directory
for filename in os.listdir(directory):
    if filename.endswith('.json'):
        json_file = os.path.join(directory, filename)
        add_damaged_animation(json_file)
