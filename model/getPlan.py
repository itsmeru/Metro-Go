import json
import os
import httpx
import xml.etree.ElementTree as ET
from fastapi import HTTPException

METRO_API_URL = "https://ws.metro.taipei/trtcBeaconBE/RouteControl.asmx"

async def getTripPlan(entry_sid: str, exit_sid: str):
    soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
    <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
    xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
    <GetRecommandRoute xmlns="http://tempuri.org/">
    <entrySid>{entry_sid}</entrySid>
    <exitSid>{exit_sid}</exitSid>
    <username>{os.getenv("METRO_EMAIL")}</username>
    <password>{os.getenv("METRO_PASSWORD")}</password>
    </GetRecommandRoute>
    </soap:Body>
    </soap:Envelope>"""

    headers = {
        'Content-Type': 'text/xml; charset=utf-8',
    }


    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(METRO_API_URL, headers=headers, content=soap_body)
            response.raise_for_status()
            
            print(f"Status Code: {response.status_code}")
           

            result =  json.loads(response.text.split("<")[0])
            print(result)
            transferStations = result["TransferStations"]
            time = result["Time"]
            if result is not None:
                return {"transferStations":transferStations,"time":time}
            else:
                raise ValueError("Could not find GetRecommandRouteResult in the response")

        except httpx.HTTPStatusError as e:
            print(f"HTTP Error: {e}")
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except ET.ParseError as e:
            print(f"XML Parse Error: {e}")
            raise HTTPException(status_code=500, detail="Failed to parse XML response")
        except ValueError as e:
            print(f"Value Error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            print(f"Unexpected Error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

# # Usage example
# async def main():
#     entry_sid = "055"  # Replace with actual station ID
#     exit_sid = "132"   # Replace with actual station ID
#     result = await get_recommended_route(entry_sid, exit_sid)
#     print(result)

# import asyncio
# asyncio.run(main())