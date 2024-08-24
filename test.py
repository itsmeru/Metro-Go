from collections import defaultdict
from model.station_time import get_station_time
import heapq
import json
class MetroSystem:
    def __init__(self, lines, station_names, transfer_stations):
        self.lines = lines
        self.station_names = station_names
        self.transfer_stations = transfer_stations
        self.graph = self._build_graph()

    def _build_graph(self):
        graph = defaultdict(list)
        
        for line, stations in self.lines:
            for i in range(len(stations) - 1):
                graph[stations[i]].append((stations[i+1], line, 1))
                graph[stations[i+1]].append((stations[i], line, 1))
        
        for station, lines in self.transfer_stations.items():
            codes = [code for code, name in self.station_names.items() if name == station]
            for i in range(len(codes)):
                for j in range(i+1, len(codes)):
                    graph[codes[i]].append((codes[j], "轉乘", 5))
                    graph[codes[j]].append((codes[i], "轉乘", 5))
        
        return graph

    def find_path(self, start, end):
        queue = [(0, start, [])]
        visited = set()

        while queue:
            (cost, station, path) = heapq.heappop(queue)
            
            if station not in visited:
                visited.add(station)
                path = path + [station]

                if station == end:
                    return self._process_path(path)

                for next_station, line, edge_cost in self.graph[station]:
                    if next_station not in visited:
                        heapq.heappush(queue, (cost + edge_cost, next_station, path))
        
        return None

    def _process_path(self, path):
        result = []
        current_line = None
        
        for i in range(len(path)):
            station = path[i]
            station_name = self.station_names[station]
            
            if i == 0:
                result.append(f"從 {station_name} 站出發")
            elif i == len(path) - 1:
                result.append(f"到達 {station_name} 站")
            else:
                next_station = path[i+1]
                for next_station_info in self.graph[station]:
                    if next_station_info[0] == next_station:
                        line = next_station_info[1]
                        if line != current_line:
                            if line == "轉乘":
                                result.append(f"在 {station_name} 站轉乘")
                            else:
                                result.append(f"在 {station_name} 站乘坐 {line} 線")
                            current_line = line
                        break

        return result

# 捷運路線數據
lines = [
    ("BL", ["BL01", "BL02", "BL03", "BL04", "BL05", "BL06", "BL07", "BL08", "BL09", "BL10", "BL11", "BL12", "BL13", "BL14", "BL15", "BL16", "BL17", "BL18", "BL19", "BL20", "BL21", "BL22", "BL23"]),
    ("BR", ["BR01", "BR02", "BR03", "BR04", "BR05", "BR06", "BR07", "BR08", "BR09", "BR10", "BR11", "BR12", "BR13", "BR14", "BR15", "BR16", "BR17", "BR18", "BR19", "BR20", "BR21", "BR22", "BR23", "BR24"]),
    ("G", ["G01", "G02", "G03", "G03A", "G04", "G05", "G06", "G07", "G08", "G09", "G10", "G11", "G12", "G13", "G14", "G15", "G16", "G17", "G18", "G19"]),
    ("O", ["O01", "O02", "O03", "O04", "O05", "O06", "O07", "O08", "O09", "O10", "O11", "O12", "O13", "O14", "O15", "O16", "O17", "O18", "O19", "O20", "O21", "O50", "O51", "O52", "O53", "O54"]),
    ("R", ["R02", "R03", "R04", "R05", "R06", "R07", "R08", "R09", "R10", "R11", "R12", "R13", "R14", "R15", "R16", "R17", "R18", "R19", "R20", "R21", "R22", "R22A", "R23", "R24", "R25", "R26", "R27", "R28"]),
    ("Y", ["Y07", "Y08", "Y09", "Y10", "Y11", "Y12", "Y13", "Y14", "Y15", "Y16", "Y17", "Y18", "Y19", "Y20"])
]

# 站點名稱數據
with open("line-name.json","r",encoding="utf-8")as f:
    station_names = json.load(f)
# station_names = {
#     "BL01": "頂埔", "BL02": "永寧", "BL03": "土城", "BL04": "海山", "BL05": "亞東醫院", "BL06": "府中", "BL07": "板橋", "BL08": "新埔", "BL09": "江子翠", "BL10": "龍山寺", "BL11": "西門", "BL12": "台北車站", "BL13": "善導寺", "BL14": "忠孝新生", "BL15": "忠孝復興", "BL16": "忠孝敦化", "BL17": "國父紀念館", "BL18": "市政府", "BL19": "永春", "BL20": "後山埤", "BL21": "昆陽", "BL22": "南港", "BL23": "南港展覽館",
#     "BR01": "動物園", "BR02": "木柵", "BR03": "萬芳社區", "BR04": "萬芳醫院", "BR05": "辛亥", "BR06": "麟光", "BR07": "六張犁", "BR08": "科技大樓", "BR09": "大安", "BR10": "忠孝復興", "BR11": "南京復興", "BR12": "中山國中", "BR13": "松山機場", "BR14": "大直", "BR15": "劍南路", "BR16": "西湖", "BR17": "港墘", "BR18": "文德", "BR19": "內湖", "BR20": "大湖公園", "BR21": "葫洲", "BR22": "東湖", "BR23": "南港軟體園區", "BR24": "南港展覽館",
#     "G01": "新店", "G02": "新店區公所", "G03": "七張", "G04": "大坪林", "G05": "景美", "G06": "萬隆", "G07": "公館", "G08": "台電大樓", "G09": "古亭", "G10": "中正紀念堂", "G11": "小南門", "G12": "西門", "G13": "北門", "G14": "中山", "G15": "松江南京", "G16": "南京復興", "G17": "台北小巨蛋", "G18": "南京三民", "G19": "松山", "G03A": "小碧潭",
#     "O01": "南勢角", "O02": "景安", "O03": "永安市場", "O04": "頂溪", "O05": "古亭", "O06": "東門", "O07": "忠孝新生", "O08": "松江南京", "O09": "行天宮", "O10": "中山國小", "O11": "民權西路", "O12": "大橋頭", "O13": "台北橋", "O14": "菜寮", "O15": "三重", "O16": "先嗇宮", "O17": "頭前庄", "O18": "新莊", "O19": "輔大", "O20": "丹鳳", "O21": "迴龍", "O50": "三重國小", "O51": "三和國中", "O52": "徐匯中學", "O53": "三民高中", "O54": "蘆洲",
#     "R02": "象山", "R03": "台北101/世貿", "R04": "信義安和", "R05": "大安", "R06": "大安森林公園", "R07": "東門", "R08": "中正紀念堂", "R09": "台大醫院", "R10": "台北車站", "R11": "中山", "R12": "雙連", "R13": "民權西路", "R14": "圓山", "R15": "劍潭", "R16": "士林", "R17": "芝山", "R18": "明德", "R19": "石牌", "R20": "唭哩岸", "R21": "奇岩", "R22": "北投", "R22A": "新北投", "R23": "復興崗", "R24": "忠義", "R25": "關渡", "R26": "竹圍", "R27": "紅樹林", "R28": "淡水",
#     "Y07": "大坪林", "Y08": "十四張", "Y09": "秀朗橋", "Y10": "景平", "Y11": "景安", "Y12": "中和", "Y13": "橋和", "Y14": "中原", "Y15": "板新", "Y16": "板橋", "Y17": "新埔民生", "Y18": "頭前庄", "Y19": "幸福", "Y20": "新北產業園區"
# }


# 轉乘站數據
transfer_stations = {
    "南港展覽館": ["BL", "BR"],
    "大安": ["BR", "R"],
    "忠孝復興": ["BL", "BR"],
    "南京復興": ["BR", "G"],
    "中山": ["G", "R"],
    "松江南京": ["G", "O"],
    "西門": ["BL", "G"],
    "古亭": ["G", "O"],
    "東門": ["O", "R"],
    "忠孝新生": ["BL", "O"],
    "民權西路": ["O", "R"],
    "台北車站": ["BL", "R"],
    "中正紀念堂": ["G", "R"],
    "大坪林": ["G", "Y"],
    "景安": ["O", "Y"],
    "頭前庄": ["O", "Y"]
}

# 站點時間


# 創建 MetroSystem 對象
metro = MetroSystem(lines, station_names, transfer_stations)

# 使用示例
start = "BL07"  
end = "O13"     

path = metro.find_path(start, end)

if path:
    print(f"從 {station_names[start]} 到 {station_names[end]} 的路線:")
    for step in path:
        print(step)
else:
    print(f"無法找到從 {station_names[start]} 到 {station_names[end]} 的路線")