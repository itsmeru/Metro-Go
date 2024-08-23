import json
import sys
import os
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
import logging

# 假設 db_set.py 在父目錄中
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.db_set import get_redis_connection

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Station:
    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name
        self.neighbors: Dict[str, int] = {}  # {鄰接站點id: 所需時間}
        self.lines: List[str] = []
        self.next_trains: Dict[str, str] = {}  # {方向: 下一班車時間}

class MetroSystem:
    def __init__(self):
        self.stations: Dict[str, Station] = {}
        self.lines: Dict[str, List[str]] = {}
        self.station_total: List[List[str]] = []

    def add_station(self, id: str, name: str):
        self.stations[id] = Station(id, name)

    def add_connection(self, station1: str, station2: str, time: int):
        self.stations[station1].neighbors[station2] = time
        self.stations[station2].neighbors[station1] = time
        logger.info(f"Added connection between {station1} and {station2} with time {time}")

    def add_line(self, line: str, stations: List[str]):
        self.lines[line] = stations
        self.station_total.append(stations)
        for station in stations:
            self.stations[station].lines.append(line)
        
        with open("each_station_time.json", "r", encoding="utf-8") as f:
            time_file = json.load(f)
        
        for i in range(len(stations) - 1):
            current_station = stations[i]
            next_station = stations[i + 1]
            for time in time_file:
                if (time["startStationId"] == current_station and time["endStationId"] == next_station) or \
                   (time["startStationId"] == next_station and time["endStationId"] == current_station):
                    self.add_connection(current_station, next_station, time["arriveTime"])
                    break
            else:
                logger.warning(f"未找到從 {current_station} 到 {next_station} 的連接時間")
        
        logger.info(f"Added line {line} with {len(stations)} stations")

    def update_next_train(self, station_id: str, direction_id: str, time: str):
        if ':' in time or time in ['資料擷取中', '列車進站']:
            self.stations[station_id].next_trains[direction_id] = time
        else:
            try:
                self.stations[station_id].next_trains[direction_id] = int(time)
            except ValueError:
                logger.warning(f"無效的時間格式 '{time}' 用於站點 {station_id} 和方向 {direction_id}")

    def get_wait_time(self, station: str, direction: str) -> int:
        next_train = self.stations[station].next_trains.get(direction)
        if next_train is not None:
            return self._process_wait_time(station, direction, next_train)
        logger.warning(f"站點 {station} 往 {direction} 方向沒有下一班車信息")
        return 0

    def _process_wait_time(self, station: str, direction: str, time_value: str) -> int:
        if time_value in ['資料擷取中', '列車進站']:
            logger.info(f"站點 {station} 往 {direction} 方向的下一班車信息為 '{time_value}'，嘗試獲取上一站信息")
            prev_station = self.get_previous_station(station, direction)
            if prev_station:
                prev_time = self.stations[prev_station].next_trains.get(direction)
                if prev_time:
                    return self._process_wait_time(prev_station, direction, prev_time)
            logger.warning(f"無法獲取站點 {station} 往 {direction} 方向的有效等待時間")
            return 0

        if ':' in time_value:
            now = datetime.now()
            train_time = datetime.strptime(time_value, "%H:%M").replace(year=now.year, month=now.month, day=now.day)
            if train_time < now:
                train_time += timedelta(days=1)
            wait_time = (train_time - now).total_seconds() / 60
            return int(wait_time)
        else:
            try:
                return int(time_value)
            except ValueError:
                logger.warning(f"無效的時間格式 '{time_value}' 用於站點 {station} 和方向 {direction}")
                return 0

    def get_direction(self, start_station: str, end_station: str) -> Optional[str]:
        for line, stations in self.lines.items():
            if start_station in stations and end_station in stations:
                start_index = stations.index(start_station)
                end_index = stations.index(end_station)
                if start_index < end_index:
                    return stations[-1]  # 終點站
                else:
                    return stations[0]  # 起始站
        return None

    def get_previous_station(self, station: str, direction: str) -> Optional[str]:
        for line in self.stations[station].lines:
            line_stations = self.lines[line]
            station_index = line_stations.index(station)
            if direction == line_stations[-1]:
                return line_stations[station_index - 1] if station_index > 0 else None
            else:
                return line_stations[station_index + 1] if station_index < len(line_stations) - 1 else None
        return None

    def find_route(self, route: List[str]):
        total_time = 0
        wait_time = 0
        path = []
        
        for i in range(len(route) - 1):
            current_station = route[i]
            next_station = route[i + 1]
            
            if not self.are_stations_on_same_line(current_station, next_station):
                transfer_path = self.find_transfer_station(current_station, next_station)
                if transfer_path:
                    logger.info(f"找到轉乘路線：{' -> '.join(transfer_path)}")
                    for j in range(len(transfer_path) - 1):
                        sub_path, sub_total_time, sub_wait_time = self.find_route([transfer_path[j], transfer_path[j+1]])
                        path.extend(sub_path[:-1])
                        total_time += sub_total_time
                        wait_time += sub_wait_time
                    current_station = transfer_path[-1]
                else:
                    raise ValueError(f"無法找到從 {current_station} 到 {next_station} 的路線")
            
            path.append(current_station)
            direction = self.get_direction(current_station, next_station)
            if direction is None:
                raise ValueError(f"無法確定從 {current_station} 到 {next_station} 的方向")
            
            station_wait_time = self.get_wait_time(current_station, direction)
            wait_time += station_wait_time

            travel_time = self.stations[current_station].neighbors.get(next_station, 0)
            if isinstance(travel_time, str):
                try:
                    travel_time = int(travel_time)
                except ValueError:
                    logger.warning(f"無效的旅行時間 '{travel_time}' 用於從 {current_station} 到 {next_station}")
                    travel_time = 0

            total_time += station_wait_time + travel_time
            logger.info(f"從 {current_station} 到 {next_station}: 等待時間 {station_wait_time}分鐘, 旅行時間 {travel_time}分鐘")
        
        path.append(route[-1])
        return path, total_time, wait_time

    def are_stations_on_same_line(self, station1: str, station2: str) -> bool:
        for line, stations in self.lines.items():
            if station1 in stations and station2 in stations:
                return True
        return False

    def find_transfer_station(self, station1: str, station2: str) -> List[str]:
        visited = set()
        queue = [(station1, [station1])]
        
        while queue:
            current_station, path = queue.pop(0)
            if current_station in visited:
                continue
            visited.add(current_station)
            
            if current_station == station2 or any(line in self.stations[station2].lines for line in self.stations[current_station].lines):
                return path
            
            for neighbor in self.stations[current_station].neighbors:
                if neighbor not in visited:
                    queue.append((neighbor, path + [neighbor]))
        
        logger.warning(f"無法找到從 {station1} 到 {station2} 的轉乘路線")
        return []

def load_metro_data(metro: MetroSystem):
    with open("line-name.json", "r", encoding="utf-8") as f:
        stations_data = json.load(f)
    with open("name_dict.json", "r", encoding="utf-8") as f:
        name_dict = json.load(f)

    for station_id, name in stations_data.items():
        metro.add_station(station_id, name)

    metro.add_line("BL", ["BL01", "BL02", "BL03", "BL04", "BL05", "BL06", "BL07", "BL08", "BL09", "BL10", "BL11", "BL12", "BL13", "BL14", "BL15", "BL16", "BL17", "BL18", "BL19", "BL20", "BL21", "BL22", "BL23"])
    metro.add_line("BR", ["BR01", "BR02", "BR03", "BR04", "BR05", "BR06", "BR07", "BR08", "BR09", "BR10", "BR11", "BR12", "BR13", "BR14", "BR15", "BR16", "BR17", "BR18", "BR19", "BR20", "BR21", "BR22", "BR23", "BR24"])
    metro.add_line("G", ["G01", "G02", "G03", "G03A", "G04", "G05", "G06", "G07", "G08", "G09", "G10", "G11", "G12", "G13", "G14", "G15", "G16", "G17", "G18", "G19"])
    metro.add_line("O", ["O01", "O02", "O03", "O04", "O05", "O06", "O07", "O08", "O09", "O10", "O11", "O12", "O13", "O14", "O15", "O16", "O17", "O18", "O19", "O20", "O21", "O50", "O51", "O52", "O53", "O54"])
    metro.add_line("R", ["R02", "R03", "R04", "R05", "R06", "R07", "R08", "R09", "R10", "R11", "R12", "R13", "R14", "R15", "R16", "R17", "R18", "R19", "R20", "R21", "R22", "R22A", "R23", "R24", "R25", "R26", "R27", "R28"])
    metro.add_line("Y", ["Y07", "Y08", "Y09", "Y10", "Y11", "Y12", "Y13", "Y14", "Y15", "Y16", "Y17", "Y18", "Y19", "Y20"])

    redis = get_redis_connection()
    metro_data = redis.get("station_data")
    metro_data_str = metro_data.decode('utf-8')
    metro_data_json = json.loads(metro_data_str)

    inverted_station = {value: key for key, value in stations_data.items()}
    name_dic = {value: key for key, value in name_dict.items()}

    for station_name, station_data in metro_data_json.items():
        for item in station_data:
            destinationName = item["DestinationName"]
            if station_name == "板橋" and destinationName in ["大坪林站", "新北產業園區站"]:
                station_id = "Y16"
            else:
                station_id = inverted_station[station_name]
            end_id = inverted_station[name_dic[destinationName]]
            count_down = item["CountDown"]
            metro.update_next_train(station_id, end_id, count_down)

def main():
    metro = MetroSystem()
    load_metro_data(metro)

    route = ["R14", "R13", "O09"]  # 圓山-民權西路-行天宮

    try:
        path, total_time, wait_time = metro.find_route(route)
        print(f"路線：{' -> '.join([metro.stations[s].name for s in path])}")
        print(f"總旅行時間：{total_time} 分鐘")
        print(f"其中等待時間：{wait_time} 分鐘")
        print(f"實際乘車時間：{total_time - wait_time} 分鐘")
    except ValueError as e:
        print(f"錯誤：{e}")

if __name__ == "__main__":
    main()