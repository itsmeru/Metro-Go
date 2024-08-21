import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()
app_id = os.getenv("TDX_ID")
app_key = os.getenv("TDX_KEY")


auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
urls = ["https://tdx.transportdata.tw/api/basic/v2/Rail/Metro/ODFare/TRTC?%24format=JSON","https://tdx.transportdata.tw/api/basic/v2/Rail/Metro/ODFare/NTMC?%24format=JSON"]

class Auth():

    def __init__(self, app_id, app_key):
        self.app_id = app_id
        self.app_key = app_key

    def get_auth_header(self):
        content_type = 'application/x-www-form-urlencoded'
        grant_type = 'client_credentials'

        return{
            'content-type' : content_type,
            'grant_type' : grant_type,
            'client_id' : self.app_id,
            'client_secret' : self.app_key
        }

class data():

    def __init__(self, app_id, app_key, auth_response):
        self.app_id = app_id
        self.app_key = app_key
        self.auth_response = auth_response

    def get_data_header(self):
        auth_JSON = json.loads(self.auth_response.text)
        access_token = auth_JSON.get('access_token')

        return{
            'authorization': 'Bearer ' + access_token,
            'Accept-Encoding': 'gzip'
        }

if __name__ == '__main__':
    mrt_line = []
    for idx,url in enumerate(urls):
        try:
            auth_response = None
            d = data(app_id, app_key, auth_response)
            data_response = requests.get(url, headers=d.get_data_header())        
        except:
            a = Auth(app_id, app_key)
            auth_response = requests.post(auth_url, a.get_auth_header())
            d = data(app_id, app_key, auth_response)
            data_response = requests.get(url, headers=d.get_data_header())
        datas = json.loads(data_response.text)
        for item in datas:
            info = {"originStationID":item["OriginStationID"],"startStation":item["OriginStationName"]["Zh_tw"],"destinationStationID":item["DestinationStationID"],"endStation":item["DestinationStationName"]["Zh_tw"],"Fares":{"normal":item["Fares"][0]["Price"],"nwtKid":item["Fares"][1]["Price"],"tpeKid":item["Fares"][2]["Price"],"loveOld":item["Fares"][3]["Price"]}}
            mrt_line.append(info)
    with open("tickets.json","w",encoding="utf-8") as file:
        json.dump(mrt_line,file,ensure_ascii=False,indent=4)