import asyncio
import os
import sys
from typing import List, Tuple, Dict, Optional
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from collections import defaultdict
import heapq
import json
from model.station_time import get_station_time
from db.db_set import engine, get_redis_connection

class MetroSystem:
    def __init__(self, lines: List[Tuple[str, List[str]]], station_names: Dict[str, str], transfer_stations: Dict[str, List[str]], transfer_times: Dict[str, int]):
        self.lines = lines
        self.station_names = station_names
        self.transfer_stations = transfer_stations
        self.transfer_times = transfer_times
        self.graph = self._build_graph()
        self.station_code_to_name = {v: k for k, v in station_names.items()}

    def _build_graph(self):
        graph = defaultdict(list)

        for line, stations in self.lines:
            for i in range(len(stations) - 1):
                graph[stations[i]].append((stations[i+1], line, 1))
                graph[stations[i+1]].append((stations[i], line, 1))

        for station, codes in self.transfer_stations.items():
            for i in range(len(codes)):
                for j in range(i+1, len(codes)):
                    graph[codes[i]].append((codes[j], "轉乘", 5))
                    graph[codes[j]].append((codes[i], "轉乘", 5))

      

        return graph
    
    

    def get_line_stations(self, line: str) -> List[str]:
        return next(stations for l, stations in self.lines if l == line)

    def get_previous_station(self, station: str, line: str, direction_code: str):
        line_stations = self.get_line_stations(line)
        station_index = line_stations.index(station)
        if station == line_stations[0] or station == line_stations[-1]:
            return [station]
        
        metro_on_path = line_stations[:station_index] if direction_code > station else line_stations[station_index:]

        return metro_on_path

    def get_direction(self, current_station: str, next_station: str, line: str) :
        line_stations = self.get_line_stations(line)
        current_index = line_stations.index(current_station)
        next_index = line_stations.index(next_station)
        if next_index > current_index:
            return line_stations[-1], self.station_names[line_stations[-1]] + "站"
        else:
            return line_stations[0], self.station_names[line_stations[0]] + "站"

    def parse_destination(self, destination: str) -> str:
        if destination == "台北車站":
            return destination
        return destination[:-1]  # 移除 "站" 字

    async def get_next_trains(self, station: str, line: str, direction: str, direction_code: str, current_time: datetime, redis):
        station_data = json.loads(redis.get("station_data"))
        station_name = self.station_names[station]
        print(f"當前站點: {station_name}", station, direction, direction_code)
        if station_name not in station_data:
            print(f"警告：找不到站點 {station_name} 的數據")
            return []

        direction = self.parse_destination(direction)
        # 篩選出所有前往指定方向的列車
        relevant_trains = {
            self.parse_destination(train['StationName']): train 
            for station_trains in station_data.values()
            for train in station_trains
            if self.parse_destination(train['DestinationName']) == direction
        }

        if not relevant_trains:
            print(f"警告：在站點 {station_name} 找不到前往 {direction} 的列車")
            return []

        next_trains = []
        first_station_code = station
        current_station_code = station
        # 直到找到指定數量的列車或沒有更多站點可查找
        metro_on_path = self.get_previous_station(station, line, direction_code)
        for path in metro_on_path:
            current_station = self.station_names[path]
            if current_station in relevant_trains:
                train = relevant_trains[current_station]
        
                countdown = train['CountDown']
                if countdown in ['列車進站', '資料擷取中'] and (line == "R1" or line == "G1"):
                    waiting_time = 580
                elif countdown in ['列車進站', '資料擷取中'] or countdown == '月台暫停服務':
                    continue  # 跳過此站點，繼續查找下一個站點
                else:
                    # 計算等待時間
                    minutes, seconds = map(int, countdown.split(':'))
                    waiting_time = minutes * 60 + seconds

                # 計算行駛時間和總時間
                travel_time = await self.get_travel_time(current_station_code, first_station_code) * 60
                total_time = waiting_time + travel_time
                next_trains.append({
                    'station': current_station,
                    'station_id': current_station_code,
                    'waiting_time': waiting_time,
                    'travel_time': travel_time,
                    'total_time': total_time,
                    'arrival_time': current_time + timedelta(seconds=total_time)
                })

        if not next_trains:
            print(f"警告：無法在 {station_name} 及其前站找到合適的列車")
            next_trains.append({
                'station': station_name,
                'station_id': station,
                'waiting_time': 480,  # 8分鐘默認等待時間
                'travel_time': 0,
                'total_time': 480,
                'arrival_time': current_time + timedelta(seconds=480)
            })
        
        return next_trains

    async def process_paths_with_waiting_times(self, path: List[List[str]], redis, start_time: datetime):
            processed_paths = []
            # 列表來存儲路徑的選項
            path_options = []
            # 初始化總行程時間
            total_time = 0
            # 初始化一個列表來存儲行程細節
            journey_details = []
            # 設置選項的當前時間為開始時間
            current_time = start_time
            i = 0
            flag = False
            while i < len(path)-1:
                current_station = path[i]
                next_station = path[i + 1]
                # 找出從當前站點到下一站點的線路
                line = next((info[1] for info in self.graph[current_station] if info[0] == next_station), None)
                if current_station == "O12" and (next_station == "O50" or next_station == "O13"):
                    flag = True
                # 如果是轉乘，獲取轉乘時間
                if i == 0 or line == "轉乘" or flag:
                    if line == "轉乘":
                        transfer_time = self.transfer_times.get(self.station_names[next_station], 5)*60 
                        if i ==0:
                            direction = self.station_names[current_station]
                        # 設置轉乘時間
                        transfer_time = transfer_time 
                        total_time += transfer_time
                        current_time += timedelta(seconds=transfer_time)
                        journey_details.append({
                            'action': '轉乘',
                            'station': self.station_names[current_station],
                            'station_id' : current_station,
                            "direction" : direction,
                            'time': transfer_time,
                            'arrival_time': current_time
                        })
                        i += 1
                        # 如果還有下一站，更新當前站和下一站，否則結束循環
                        if i < len(path) - 1:
                            current_station = path[i]
                            next_station = path[i + 1]
                            line = next((info[1] for info in self.graph[current_station] if info[0] == next_station), None)
                        else:
                            break
                    # 獲取行進方向
                    direction_code, direction = self.get_direction(current_station, next_station, line)

                    # 獲取下一班車信息
                    next_trains = await self.get_next_trains(current_station, line, direction, direction_code, current_time, redis)
                    print(next_trains)
                    # 找到第一班適合的列車  
                    suitable_train = next((train for train in next_trains if train['arrival_time'] > current_time), None)
            
                    if suitable_train is None:
                        print(f"無法在 {current_station} 找到合適的列車")
                        break
                    # 計算等待時間並更新總時間
                    waiting_time = (suitable_train['arrival_time'] - current_time).total_seconds()
                    total_time += waiting_time

                    journey_details.append({
                        'action': '等待',
                        'station': self.station_names[current_station],
                        'station_id' : current_station,
                        "direction" : direction,
                        'time': waiting_time,
                        'train_time': suitable_train['arrival_time']
                    })

                    current_time = suitable_train['arrival_time']

                travel_time = await self.get_travel_time(current_station, next_station) * 60
                total_time += travel_time
                current_time += timedelta(seconds=travel_time)

                journey_details.append({
                    'action': '乘車',
                    'from_station': self.station_names[current_station],
                    'to_station': self.station_names[next_station],
                    'station_id' : next_station,
                    "direction" : direction,
                    'time': travel_time,
                    'arrival_time': current_time,
                    'line': line
                })

                # 移動到下一個站點

                i += 1
                if ((path[-1]== "R22A" or path[-1]== "G03A") and (current_station== "R22" or current_station== "G03")) or current_station== "R22A"or current_station== "G03A" :
                    flag = True
                else:
                    flag = False

            path_options.append({
                'option': 1,
                'total_time': total_time,
                'journey_details': journey_details,
                'arrival_time': current_time
            })

            path_names = [self.station_names[station] for station in path]

            processed_paths.append({
                'path':  [path_names,path],
                'options': path_options
            })
            

            return processed_paths

    async def get_travel_time(self, start_station: str, end_station: str) -> int:
        try:
            time = await get_station_time(start_station, end_station)
            return time if time is not None else 3
        except Exception as e:
            print(f"Error getting travel time from {start_station} to {end_station}: {e}")
            return 3
        
    async def find_paths(self, start: str, end: str) -> List[str]:
        queue = [(0, start, [])]
        visited = set()
        def is_same_station(station, end):
            s1 = self.station_names[station]
            if s1 in self.transfer_stations:
                same_vale = self.transfer_stations.get(s1,[])
                return (station in same_vale and end in same_vale) 
            return False

        while queue:
            (cost, station, path) = heapq.heappop(queue)
            if station == end or is_same_station(station, end):
                return path + [station]  # 找到最佳路徑，直接返回

            if station not in visited:
                visited.add(station)
                new_path = path + [station]

                for next_station, line, edge_cost in self.graph[station]:
                    if next_station not in new_path:
                        total_cost = cost + edge_cost 
                        heapq.heappush(queue, (total_cost, next_station, new_path))

        return []  

# 捷運路線數據
lines = [
    ("BL", ["BL01", "BL02", "BL03", "BL04", "BL05", "BL06", "BL07", "BL08", "BL09", "BL10", "BL11", "BL12", "BL13", "BL14", "BL15", "BL16", "BL17", "BL18", "BL19", "BL20", "BL21", "BL22", "BL23"]),
    ("BR", ["BR01", "BR02", "BR03", "BR04", "BR05", "BR06", "BR07", "BR08", "BR09", "BR10", "BR11", "BR12", "BR13", "BR14", "BR15", "BR16", "BR17", "BR18", "BR19", "BR20", "BR21", "BR22", "BR23", "BR24"]),
    ("G", ["G01", "G02", "G03", "G04", "G05", "G06", "G07", "G08", "G09", "G10", "G11", "G12", "G13", "G14", "G15", "G16", "G17", "G18", "G19"]),
    ("G1", ["G03", "G03A"]),
    ("O", ["O01", "O02", "O03", "O04", "O05", "O06", "O07", "O08", "O09", "O10", "O11", "O12", "O13", "O14", "O15", "O16", "O17", "O18", "O19", "O20", "O21"]),
    ("O1", ["O01", "O02", "O03", "O04", "O05", "O06", "O07", "O08", "O09", "O10", "O11","O12", "O50", "O51", "O52", "O53", "O54"]),
    ("R", ["R02", "R03", "R04", "R05", "R06", "R07", "R08", "R09", "R10", "R11", "R12", "R13", "R14", "R15", "R16", "R17", "R18", "R19", "R20", "R21","R22","R23", "R24", "R25", "R26", "R27", "R28"]),
    ("R1", ["R22","R22A"]),
    ("Y", ["Y07", "Y08", "Y09", "Y10", "Y11", "Y12", "Y13", "Y14", "Y15", "Y16", "Y17", "Y18", "Y19", "Y20"])
]

# 站點名稱數據
with open("./model/line-name.json", "r", encoding="utf-8") as f:
    station_names = json.load(f)

# 轉乘站數據
transfer_stations = {
    "南港展覽館": ["BL23", "BR24"],
    "大安": ["BR09", "R05"],
    "忠孝復興": ["BL15", "BR10"],
    "南京復興": ["BR11", "G16"],
    "中山": ["G14", "R11"],
    "松江南京": ["G15", "O08"],
    "西門": ["BL11", "G12"],
    "古亭": ["G09", "O05"],
    "東門": ["O06", "R07"],
    "忠孝新生": ["BL14", "O07"],
    "民權西路": ["O11", "R13"],
    "台北車站": ["BL12", "R10"],
    "中正紀念堂": ["G10", "R08"],
    "大坪林": ["G04", "Y07"],
    "景安": ["O02", "Y11"],
    "頭前庄": ["O17", "Y18"],
    "板橋": ["BL07", "Y16"],
    "新埔": ["BL08", "Y17"],
    "新埔民生": ["BL08", "Y17"]
}


# 轉乘步行時間數據
transfer_times = {
    "北投": 3,
    "民權西路": 3,
    "忠孝新生": 2,
    "忠孝復興": 5,
    "台北車站": 4,
    "中正紀念堂": 2,
    "古亭": 2,
    "七張": 3,
    "南港展覽館": 5,
    "西門": 2,
    "大橋頭": 1,
    "東門": 2,
    "大安": 5,
    "南京復興": 5,
    "松江南京": 2,
    "中山": 3,
    "景安": 6,
    "板橋": 11,
    "新埔": 9,
    "新埔民生": 9,
    "頭前庄": 6
}

async def get_travel_plan(start,end):
    metro = MetroSystem(lines, station_names, transfer_stations, transfer_times)
    redis = get_redis_connection()
    
    start = start # 例如: "O54" 圓山站
    end = end # 例如: "G13" 龍山寺站
    start_time = datetime.now()
    try:
        paths = await metro.find_paths(start, end)
        
        if paths:
            print(paths)
            processed_paths = await metro.process_paths_with_waiting_times(paths, redis, start_time)

            print(f"從 {station_names[start]} 到 {station_names[end]} 的可行路線：")
            for path_index, path_info in enumerate(processed_paths, 1):
                print(f"\n路線 {path_index}：")
                for option in path_info['options']:
                    print(f"  選項 {option['option']}:")
                    total_minutes, total_seconds = divmod(int(option['total_time']), 60)
                    print(f"    總行程時間: {total_minutes} 分 {total_seconds} 秒")
                    print(f"    預計到達時間: {option['arrival_time'].strftime('%H:%M:%S')}")
                    for detail in option['journey_details']:
                        if detail['action'] == '等待':
                            wait_minutes, wait_seconds = divmod(int(detail['time']), 60)
                            print(f"    在 {detail['station']} 站等待 {wait_minutes} 分 {wait_seconds} 秒")
                            print(f"    搭乘 {detail['train_time'].strftime('%H:%M:%S')} 的列車")
                        elif detail['action'] == '乘車':
                            travel_minutes, travel_seconds = divmod(int(detail['time']), 60)
                            print(f"    搭乘 {detail['line']} 線從 {detail['from_station']} 站到 {detail['to_station']} 站，耗時 {travel_minutes} 分 {travel_seconds} 秒")
                            print(f"    到達時間: {detail['arrival_time'].strftime('%H:%M:%S')}")
                        elif detail['action'] == '轉乘':
                            transfer_minutes, transfer_seconds = divmod(int(detail['time']), 60)
                            print(f"    在 {detail['station']} 站轉乘，耗時 {transfer_minutes} 分 {transfer_seconds} 秒")
                            print(f"    轉乘完成時間: {detail['arrival_time'].strftime('%H:%M:%S')}")
                    print()
            return processed_paths
                

        else:
            print(f"無法找到從 {station_names[start]} 到 {station_names[end]} 的路線")
    except Exception as e:
        print(f"發生錯誤：{e}")
    finally:
        await engine.dispose()
    

# if __name__ == "__main__":
#     asyncio.run(get_travel_plan())

