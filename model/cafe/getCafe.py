import json
from collections import defaultdict

with open("mrt_name.json", "r", encoding="utf-8") as f1, open("all_cafes.json", "r", encoding="utf-8") as f2:
    line_names = json.load(f1)
    cafes = json.load(f2)

    data = defaultdict(list)
    
    for name in line_names:
        for cafe in cafes:
            if name in cafe["mrt"]:
                data[name].append(cafe)
    
    with open("cafes-mrt.json", "w", encoding="utf-8") as f3:
        json.dump(data, f3, ensure_ascii=False, indent=4)
