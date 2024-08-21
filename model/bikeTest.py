from collections import defaultdict
import math
import httpx
import json
import csv
from io import StringIO
import asyncio

tpe_url = "https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json"
# ntp_url = "https://data.ntpc.gov.tw/api/datasets/010e5b15-3823-4b20-b401-b1cf000550c5/csv?size=3000"
ntp_url = "https://data.ntpc.gov.tw/api/datasets/010e5b15-3823-4b20-b401-b1cf000550c5/csv/file"


async def fetch_data(url):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.text

async def process_data():
    tep_data, ntp_data = await asyncio.gather(
        fetch_data(tpe_url),
        fetch_data(ntp_url)
    )

    tep_data = json.loads(tep_data)

    f = StringIO(ntp_data)
    reader = csv.reader(f, delimiter=',')
    headers = next(reader)
    print(headers)
    headers[0] = "sno"
    headers[3] = "available_rent_bikes"
    headers[6] = "latitude"
    headers[7] = "longitude"
    headers[12] = "available_return_bikes"
   
    
    bike_info = {}

    for row in reader:
        row_data = dict(zip(headers,row))
        bike_info[row_data["sno"]] = row_data

    for item in tep_data:
        bike_info[item["sno"]] = item

 
    write_data_to_file(bike_info)
    # 寫入文件
    with open("NbikeTest.json", "w", encoding="utf-8") as file:
        json.dump(bike_info, file, ensure_ascii=False, indent=4)

def write_data_to_file(bike_info):
    with open("bike_results.json","r",encoding="utf-8")as files:
            bike_results = json.load(files)
            for key, values in bike_results.items():
                for value in values:
                    uid = value["StationUID"].replace("NWT","").replace("TPE","")
                    real_item = bike_info[uid]
                    value["AvailableRentBikes"] = real_item["available_rent_bikes"]
                    value["AvailableReturnBikes"] = real_item["available_return_bikes"]
                   
            
            with open("bike_.json","w",encoding="utf-8")as file2:
                json.dump(bike_results,file2,ensure_ascii=False,indent=4)


# 找出捷運站附近的 youbike 站

# def write_data_to_file(bike_info):
#     with open("station_position.json","r",encoding="utf-8")as files:
#         station_position = json.load(files)
#         station_bike_data = defaultdict(list)
#         for station in  station_position :
#             for key , bike in  bike_info.items():
#                 lat = station["PositionLat"]
#                 lon = station["PositionLon"]
#                 low_lat,high_lat,low_lon,high_lon = calculate(lat,lon)
               
#                 bike_lon = float(bike["longitude"])
#                 bike_lat = float(bike["latitude"])
#                 if (bike_lon > low_lon) and (bike_lon < high_lon) and (bike_lat > low_lat) and (bike_lat < high_lat):
#                     data = {"StationUID":bike["sno"],"StationName":bike["sna"], "PositionLon":bike_lon,"PositionLat":bike_lat,"StationAddress":bike["ar"]}

#                     station_bike_data[station["StationName"]].append(data)

#         with open("bike_results2.json","w",encoding="utf-8")as file2:
#             json.dump(station_bike_data,file2,ensure_ascii=False,indent=4)

# def calculate(lat,lon):
#     delta_lat = 300 / 111320  
#     delta_lon = 300 / (111320 * math.cos(math.radians(lat)))
#     low_lat = lat - delta_lat
#     high_lat = lat + delta_lat
#     low_lon = lon - delta_lon
#     high_lon = lon + delta_lon
#     return low_lat,high_lat,low_lon,high_lon

# 運行非同步函數
asyncio.run(process_data())
