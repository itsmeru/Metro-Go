import json

with open("station-time.json", "r", encoding="utf-8") as file:
    station_time = json.load(file)

with open("line-name.json", "r", encoding="utf-8") as file:
    line_name = json.load(file)

entry = []
for start, startValue in line_name.items():
    for end, endValue in line_name.items():
        matched = False
        for item in station_time:
            if isinstance(item, dict) and item != "Unknown":
                if startValue == item["start"] and endValue == item["end"]:
                    time = item["time"]
                    data = {
                        "startStationId": start,
                        "startStation": startValue,
                        "endStationId": end,
                        "endStation": endValue,
                        "arriveTime": time
                    }
                    entry.append(data)
                    matched = True
                    break
        if not matched:
            data = {
                "startStationId": start,
                "startStation": startValue,
                "endStationId": end,
                "endStation": endValue,
                "arriveTime": "0"
            }
            entry.append(data)


with open("each_station_time.json", "w", encoding="utf-8") as file:
    json.dump(entry, file, ensure_ascii=False, indent=4)
print("OK")
