import requests
import gzip
import json
import io


# route_url = "https://tcgbusfs.blob.core.windows.net/blobbus/GetRoute.gz"
# estimate_url = "https://tcgbusfs.blob.core.windows.net/blobbus/GetEstimateTime.gz"
# stop_url = "https://tcgbusfs.blob.core.windows.net/blobbus/GetStopLocation.gz"

# response = requests.get(route_url)
# with gzip.GzipFile(fileobj=io.BytesIO(response.content)) as gzipped_file:
#         decompressed_content = gzipped_file.read()

#         # 解析 JSON
#         json_data = json.loads(decompressed_content.decode('utf-8'))
# with open("try.json","w",encoding="utf-8")as f:
#         json.dump(json_data,f,ensure_ascii=False,indent=4)

# import time
# import requests
# import json
# from dotenv import load_dotenv
# import os
# from collections import defaultdict
# load_dotenv()
# app_id = os.getenv("TDX_ID")
# app_key = os.getenv("TDX_KEY")


# auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
# urls = ["https://tdx.transportdata.tw/api/basic/v2/Bus/EstimatedTimeOfArrival/City/Taipei?%24select=RouteName%2CStopName&%24filter=%28contains%28StopName%2FZh_tw%2C%20%27%E6%8D%B7%E9%81%8B%27%29%20or%20StopName%2FZh_tw%20eq%20%27%E6%9D%BF%E6%A9%8B%E8%BB%8A%E7%AB%99%28%E6%96%87%E5%8C%96%E8%B7%AF%29%27%29%20and%20EstimateTime%20lt%201200%20and%20StopStatus%20eq%200&%24format=JSON",
#             "https://tdx.transportdata.tw/api/basic/v2/Bus/EstimatedTimeOfArrival/City/NewTaipei?%24select=RouteName%2CStopName&%24filter=%28contains%28StopName%2FZh_tw%2C%20%27%E6%8D%B7%E9%81%8B%27%29%20or%20StopName%2FZh_tw%20eq%20%27%E6%9D%BF%E6%A9%8B%E8%BB%8A%E7%AB%99%28%E6%96%87%E5%8C%96%E8%B7%AF%29%27%29%20and%20EstimateTime%20lt%201200%20and%20StopStatus%20eq%200&%24format=JSON"]
# class Auth():

#     def __init__(self, app_id, app_key):
#         self.app_id = app_id
#         self.app_key = app_key

#     def get_auth_header(self):
#         content_type = 'application/x-www-form-urlencoded'
#         grant_type = 'client_credentials'

#         return{
#             'content-type' : content_type,
#             'grant_type' : grant_type,
#             'client_id' : self.app_id,
#             'client_secret' : self.app_key
#         }

# class data():

#     def __init__(self, app_id, app_key, auth_response):
#         self.app_id = app_id
#         self.app_key = app_key
#         self.auth_response = auth_response

#     def get_data_header(self):
#         auth_JSON = json.loads(self.auth_response.text)
#         access_token = auth_JSON.get('access_token')

#         return{
#             'authorization': 'Bearer ' + access_token,
#             'Accept-Encoding': 'gzip'
#         }

# if __name__ == '__main__':
#     bus_live_datas= {}
#     with open("bus_dest.json","r",encoding="utf-8") as file:
#         bus_destination = json.load(file)
    
#     with open("mrt_name_v2.json","r",encoding="utf-8") as file:
#         mrt_name= json.load(file)

#     with open("name_dict.json","r",encoding="utf-8") as file:
#         name_dic= json.load(file)

#     das = []
#     for idx,url in enumerate(urls):
#         try:
#             auth_response = None
#             d = data(app_id, app_key, auth_response)
#             data_response = requests.get(url, headers=d.get_data_header())        
#         except:
#             a = Auth(app_id, app_key)
#             auth_response = requests.post(auth_url, a.get_auth_header())
#             d = data(app_id, app_key, auth_response)
#             data_response = requests.get(url, headers=d.get_data_header())
#         response_text = json.loads(data_response.text)
#         das.append(response_text)

#     with open("bus_.json","w",encoding="utf-8") as file:
#         json.dump(das,file,ensure_ascii=False,indent=4)
        
#         for mrt_station in mrt_name:
#             for item in response_text:
#                 bus_name = item["RouteName"]["Zh_tw"]
#                 direction = item["Direction"]
#                 stop_name = item["StopName"]["Zh_tw"]
#                 destination = bus_destination.get(bus_name, {}).get("DestinationStopNameZh" if direction == 0 else "DepartureStopNameZh")
#                 if not destination:
#                     for key, value in bus_destination.items():
#                         if bus_name in key:
#                             destination = value["DestinationStopNameZh" if direction == 0 else "DepartureStopNameZh"]
#                             break

               
#                 if mrt_station == "板橋站":
#                     mrt_station = "板橋車站(文化路)"
                 
#                 if mrt_station in stop_name:
#                     if mrt_station != "板橋車站(文化路)":
#                         mrt_station = name_dic.get(mrt_station, mrt_station)
#                     else:
#                         mrt_station = "板橋"
                    
#                     estimate_minutes = int(item["EstimateTime"]) // 60
#                     if mrt_station not in bus_live_datas:
#                         bus_live_datas[mrt_station] = []
#                     bus_live_datas[mrt_station].append({
#                         "bus_name": bus_name,
#                         "Direction": direction,
#                         "EstimateTime": f'{estimate_minutes} 分' if estimate_minutes > 0 else '即將進站',
#                         "UpdateTime": item["UpdateTime"],
#                         "destination": destination
#                     })
#                 # if mrt_station in stop_name:
#                 #     if mrt_station not in bus_live_datas:
#                 #         bus_live_datas[mrt_station] = []
#                 #     bus_live_datas[mrt_station].append({"bus_name":bus_name,"Direction":item["Direction"],"EstimateTime":item["EstimateTime"],"UpdateTime":item["UpdateTime"],"destination": destination})
#         with open("bus_livess.json","w",encoding="utf-8") as file:
#             json.dump(bus_live_datas,file,ensure_ascii=False,indent=4)



       

#     ## bus_dest.json

# ## 抓公車站 去回程資料
# # urls = ["https://tdx.transportdata.tw/api/basic/v2/Bus/Route/City/Taipei?%24select=DepartureStopNameZh%2CDestinationStopNameZh%2CSubRoutes&%24format=JSON","https://tdx.transportdata.tw/api/basic/v2/Bus/Route/City/NewTaipei?%24select=DepartureStopNameZh%2CDestinationStopNameZh%2CSubRoutes&%24format=JSON"]

#     # with open("all_bus_data.json", "r", encoding="utf-8") as file:
#     #     result = json.load(file)

#     # route_info = defaultdict(dict)

#     # for outer_item in result:
#     #     for item in outer_item:
#     #         departure = item.get("DepartureStopNameZh")
#     #         destination = item.get("DestinationStopNameZh")
#     #         update_time = item.get("UpdateTime")

#     #         for subroute in item.get("SubRoutes", []):
#     #             subroute_name = subroute.get("SubRouteName", {}).get("Zh_tw")
#     #             if subroute_name:
#     #                 route_info[subroute_name] = {
#     #                     "DepartureStopNameZh": departure,
#     #                     "DestinationStopNameZh": destination,
#     #                     "UpdateTime": update_time
#     #                 }
#     # with open("bus_dest.json","w",encoding="utf-8") as file:
#     #     json.dump(route_info,file,ensure_ascii=False,indent=4)



# # import csv 
# # import json
# # with open("bus.csv",newline="",encoding="utf-8")as f:
# #     reader = csv.reader(f, delimiter=',')
# #     results = {}
# #     seen = set()
# #     for data in reader:
# #         id,name = data[1].split("_")
# #         bus_no = data[3].split("-")[0]
# #         key = (name, bus_no, data[3],data[2])
# #         if key not in seen:
# #             seen.add(key)
# #             if id not in results:
# #                 results[id] = []
# #             results[id].append({"stationName":name,"busNo":bus_no,"busName":data[3],"exit":data[2]})

# #     with open ("bus.json","w",encoding="utf-8")as file:
# #         json.dump(results,file,ensure_ascii=False,indent=4)
