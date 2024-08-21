import json
import httpx
import asyncio

url = "https://cafenomad.tw/api/v1.2/cafes"

async def fetch_cafes():
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"Request failed with status code: {response.status_code}")
            return None

async def main():
    cafes = await fetch_cafes()
    if cafes:
        with open("./data_json/cafes.json", "w", encoding="utf-8") as file: # 咖啡廳資訊
            json.dump(cafes, file, ensure_ascii=False, indent=4)


try:
    loop = asyncio.get_event_loop()
    if loop.is_running():
        print("Event loop is running, scheduling with ensure_future")
        loop.create_task(main())
    else:
        asyncio.run(main())
except RuntimeError as e:
    print(f"RuntimeError: {e}")
    asyncio.run(main())
