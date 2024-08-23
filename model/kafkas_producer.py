import httpx
import json
import asyncio
import os
from dotenv import load_dotenv
from aiokafka import AIOKafkaProducer
from io import StringIO
import csv

load_dotenv()
app_id = os.getenv("TDX_ID")
app_key = os.getenv("TDX_KEY")
kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
BATCH_SIZE = 1000

auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
tpe_url = "https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json"
ntp_url = "https://data.ntpc.gov.tw/api/datasets/010e5b15-3823-4b20-b401-b1cf000550c5/csv/file"
# ntp_url = "https://data.ntpc.gov.tw/api/datasets/010e5b15-3823-4b20-b401-b1cf000550c5/csv?size=3000"
sid_url = "https://ws.metro.taipei/trtcBeaconBE/RouteControl.asmx"
metro_url = "https://api.metro.taipei/metroapi/TrackInfo.asmx"
bus_urls = ["https://tdx.transportdata.tw/api/basic/v2/Bus/EstimatedTimeOfArrival/City/Taipei?%24select=RouteName%2CStopName&%24filter=%28contains%28StopName%2FZh_tw%2C%20%27%E6%8D%B7%E9%81%8B%27%29%20or%20StopName%2FZh_tw%20eq%20%27%E6%9D%BF%E6%A9%8B%E8%BB%8A%E7%AB%99%28%E6%96%87%E5%8C%96%E8%B7%AF%29%27%29%20and%20EstimateTime%20lt%201200%20and%20StopStatus%20eq%200&%24format=JSON",
            "https://tdx.transportdata.tw/api/basic/v2/Bus/EstimatedTimeOfArrival/City/NewTaipei?%24select=RouteName%2CStopName&%24filter=%28contains%28StopName%2FZh_tw%2C%20%27%E6%8D%B7%E9%81%8B%27%29%20or%20StopName%2FZh_tw%20eq%20%27%E6%9D%BF%E6%A9%8B%E8%BB%8A%E7%AB%99%28%E6%96%87%E5%8C%96%E8%B7%AF%29%27%29%20and%20EstimateTime%20lt%201200%20and%20StopStatus%20eq%200&%24format=JSON"]

headers = {
    'Content-Type': 'text/xml; charset=utf-8',
}

metro_body = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xmlns:xsd="http://www.w3.org/2001/XMLSchema"
xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
<soap:Body>
<getTrackInfo xmlns="http://tempuri.org/">
<userName>{os.getenv("METRO_EMAIL")}</userName>
<passWord>{os.getenv("METRO_PASSWORD")}</passWord>
</getTrackInfo>
</soap:Body>
</soap:Envelope>"""


class DataPipeline:
    def __init__(self, app_id, app_key):
        self.app_id = app_id
        self.app_key = app_key
        self.producer = None
        self.access_token = None

    async def initialize(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8")
        )
        await self.producer.start()
        await self.get_access_token()

    async def close(self):
        if self.producer:
            await self.producer.stop()

    async def get_access_token(self):
        auth_data = {
            'grant_type': 'client_credentials',
            'client_id': self.app_id,
            'client_secret': self.app_key
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(auth_url, data=auth_data)
            response.raise_for_status()
            self.access_token = response.json().get('access_token')

    def get_headers(self):
        return {
            "authorization": f"Bearer {self.access_token}",
            "Accept-Encoding": "gzip"
        }

    async def fetch_data(self, url, headers=None, data=None, use_tdx_auth=False):
        try:
            async with httpx.AsyncClient() as client:
                if use_tdx_auth:
                    headers = self.get_headers()
                    response = await client.get(url, headers=headers)
                elif headers and data:
                    response = await client.post(url, headers=headers, data=data)
                else:
                    response = await client.get(url)
                response.raise_for_status()
                return response.text
        except httpx.RequestError as e:
            print(f"Failed to fetch data from {url}: {e}")
            raise

    async def process_bike_data(self):
        tpe_data, ntp_data = await asyncio.gather(
            self.fetch_data(tpe_url),
            self.fetch_data(ntp_url)
        )

        tpe_data = json.loads(tpe_data)

        f = StringIO(ntp_data)
        reader = csv.reader(f, delimiter=',')
        headers = next(reader)
        headers[0] = "sno"
        headers[3] = "available_rent_bikes"
        headers[6] = "latitude"
        headers[7] = "longitude"
        headers[12] = "available_return_bikes"
        
        bike_info = {}
     
        for row in reader:
            row_data = dict(zip(headers, row))
            bike_info[row_data["sno"]] = row_data

        for item in tpe_data:
            bike_info[item["sno"]] = item

        return list(bike_info.values())

    async def process_metro_data(self):
        response = await self.fetch_data(metro_url, headers=headers, data=metro_body)
        datas = response.split(']')[0].lstrip('[')
        return json.loads(f"[{datas}]")

    async def process_bus_data(self):
        all_bus_data = []
        for bus_url in bus_urls:
            response = await self.fetch_data(bus_url, use_tdx_auth=True)
            bus_data = json.loads(response)
            all_bus_data.extend(bus_data)
        return all_bus_data

    async def send_batch_to_kafka(self, topic, batch):
        await self.producer.send_and_wait(topic, batch)

    async def send_end(self, topic):
        await self.producer.send_and_wait(topic, "end_marker")

    async def bike_data_task(self, interval):
        while True:
            try:
                bike_data = await self.process_bike_data()
                for i in range(0, len(bike_data), BATCH_SIZE):
                    batch = bike_data[i:i+BATCH_SIZE]
                    await self.send_batch_to_kafka("bike_data", batch)
                await self.send_end("bike_data")
                print("Bike data processing and sending completed.")
            except Exception as e:
                print(f"An error occurred during bike data processing: {e}")
            await asyncio.sleep(interval)

    async def metro_data_task(self, interval):
        while True:
            try:
                metro_data = await self.process_metro_data()
                for i in range(0, len(metro_data), BATCH_SIZE):
                    batch = metro_data[i:i+BATCH_SIZE]
                    await self.send_batch_to_kafka("metro_data", batch)
                await self.send_end("metro_data")
                print("Metro data processing and sending completed.")
            except Exception as e:
                print(f"An error occurred during metro data processing: {e}")
            await asyncio.sleep(interval)

    async def bus_data_task(self, interval):
        while True:
            try:
                bus_data = await self.process_bus_data()
                for i in range(0, len(bus_data), BATCH_SIZE):
                    batch = bus_data[i:i+BATCH_SIZE]
                    await self.send_batch_to_kafka("bus_data", batch)
                await self.send_end("bus_data")
                print("Bus data processing and sending completed.")
            except Exception as e:
                print(f"An error occurred during bus data processing: {e}")
            await asyncio.sleep(interval)
    async def wait_for_consumer(self, timeout=300):  
        start_time = asyncio.get_event_loop().time()
        while True:
            if os.path.exists("/tmp/kafka_consumer_ready"):
                print("Consumer is ready. Starting producer tasks.")
                return
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError("Consumer did not become ready in time")
            await asyncio.sleep(1)

    async def start_tasks(self, bike_interval, metro_interval, bus_interval):
        await self.wait_for_consumer()
        await asyncio.gather(
            self.bike_data_task(bike_interval),
            self.metro_data_task(metro_interval),
            self.bus_data_task(bus_interval)
        )

async def main():
    pipeline = DataPipeline(app_id, app_key)
    await pipeline.initialize()
    try:
        await pipeline.start_tasks(bike_interval=60, metro_interval=11, bus_interval=31)
    finally:
        await pipeline.close()

if __name__ == "__main__":
    asyncio.run(main())