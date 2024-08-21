import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from metro.model.models import StationTime
from metro.model.db import get_db
import json


async def insert_ticket_data(file_path: str, db: AsyncSession):
    async with db.begin(): 
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            for row in data:
                time = row["arriveTime"]
                startStation=row["startStation"]
                endStation=row["endStation"]
                if startStation == "Y板橋":
                    startStation = "板橋"
                if endStation == "Y板橋":
                    endStation = "板橋"
                
                station_time = StationTime(
                    startStationId=row["startStationId"],
                    startStation=startStation,
                    endStationId=row["endStationId"],
                    endStation=endStation,
                    arriveTime=time
                )
                db.add(station_time)  
        await db.commit()  

    print("Data inserted successfully")

async def main():
    async for db in get_db():  
        await insert_ticket_data("each_station_time.json", db)

if __name__ == "__main__":
    asyncio.run(main())
