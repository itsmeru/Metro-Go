import aiohttp
import asyncio
import json
import re
from aiohttp.client_exceptions import ClientConnectorError, ServerDisconnectedError
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# SOAP 请求模板
SOAP_REQUEST_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xmlns:xsd="http://www.w3.org/2001/XMLSchema"
xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
<soap:Body>
<GetRecommandRoute xmlns="http://tempuri.org/">
<entrySid>{start}</entrySid>
<exitSid>{end}</exitSid>
<username>{email}</username>
<password>{password}</password>
</GetRecommandRoute>
</soap:Body>
</soap:Envelope>"""

URL = "https://ws.metro.taipei/trtcBeaconBE/RouteControl.asmx"
HEADERS = {"Content-Type": "text/xml; charset=utf-8"}
email = os.getenv("METRO_EMAIL")
password = os.getenv("METRO_PASSWORD")

async def getTime(session, start, end, startSid, endSid, semaphore):
    soap_request = SOAP_REQUEST_TEMPLATE.format(start=startSid, end=endSid, email=email, password=password)

    async with semaphore:
        for attempt in range(3):  # Retry up to 3 times
            try:
                async with session.post(URL, data=soap_request, headers=HEADERS, ssl=False) as response:
                    await asyncio.sleep(0.3)  # Delay between retries
                    if response.status == 200:
                        datas = await response.text()
                        match = re.search(r"\{.*?\}", datas)
                        if match:
                            try:
                                data = json.loads(match.group(0))
                                time = data.get("Time", "Unknown")
                                if time == "1":
                                    print(f"Received time is 1 minute, retrying: {attempt}")
                                    await asyncio.sleep(1)  # Wait before retry
                                    continue
                                print(f"Received time: {time}")
                                return {"time":time,"start":start,"end":end}
                            except json.JSONDecodeError:
                                print(f"JSONDecodeError: {datas}")
                                return "Unknown"
                    else:
                        print(f"Request failed with status: {response.status}")
            except (ClientConnectorError, ServerDisconnectedError) as e:
                print(f"Request error: {e}, retrying...")
            await asyncio.sleep(1)  # Wait before retry
        return "Unknown"

async def main():
    try:
        # Load station and line data
        with open("station-sid.json", "r", encoding="utf-8") as f1, \
             open("line-name.json", "r", encoding="utf-8") as f2:
            stationSid = json.load(f1)
            stationId = json.load(f2)
        
        seen_combinations = {}  # Store computed distances
        tasks = []
        semaphore = asyncio.Semaphore(10)

        async with aiohttp.ClientSession() as session:
            for start, startValue in stationId.items():
                for end, endValue in stationId.items():
                    combination_key = (startValue , endValue)

                    if combination_key in seen_combinations :
                        continue  # Skip already computed combinations

                    seen_combinations[combination_key] = True

                    if start == end:
                        # task_order.append((start, stationSid[start]["stationName"], end, stationSid[end]["stationName"]))
                        tasks.append(asyncio.sleep(0, result=0))  # Time is 0 for the same station
                    else:
                        # task_order.append((start, stationSid[start]["stationName"], end, stationSid[end]["stationName"]))
                        tasks.append(asyncio.create_task(getTime(session, startValue, endValue, stationSid[start]["stationSid"], stationSid[end]["stationSid"], semaphore)))

            # Gather results from all tasks
            results = await asyncio.gather(*tasks)

            # Process results
            # entry = []
            # for i in 
            # for i, (start, startValue, end, endValue) in enumerate(task_order):
            #     time = results[i]
            #     entry.append({
            #         "startStationId": start,
            #         "startStation": startValue,
            #         "endStationId": end,
            #         "endStation": endValue,
            #         "time": time
            #     })

        # Save results to file
        with open("station-time.json", "w", encoding="utf-8") as file:
            json.dump(results, file, ensure_ascii=False, indent=4)

    except json.JSONDecodeError as e:
        print("JSONDecodeError:", e)
    except FileNotFoundError as e:
        print("FileNotFoundError:", e)
    except Exception as e:
        print("Exception:", e)

if __name__ == "__main__":
    asyncio.run(main())
