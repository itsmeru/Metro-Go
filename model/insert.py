import asyncio
import json
import os
import sys
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.models import BusRoute, Station, YoubikeStation, MRTStation
from db.db_set import get_db, engine

async def insert_bus_data(file_path: str, db: AsyncSession):
    try:
        async with db.begin():
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
            
            for station_name, routes in data.items():
                stmt = select(Station).where(Station.name == station_name)
                result = await db.execute(stmt)
                station = result.scalar_one_or_none()
                
                if not station:
                    station = Station(name=station_name)
                    db.add(station)
                    await db.flush()
                
                for route in routes:
                    new_route = BusRoute(
                        station_id=station.id,
                        stop_name=route['StopName'],
                        route_name=route['RouteName'],
                        departure=route['departure'],
                        destination=route['destination']
                    )
                    db.add(new_route)
            
            await db.commit()
        print("公車數據插入成功")
    except Exception as e:
        await db.rollback()
        print(f"插入公車數據時發生錯誤: {e}")
        raise

async def insert_youbike_data(file_path: str, db: AsyncSession):
    try:
        async with db.begin():
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                for area, stations in data.items():
                    for station in stations:
                        bike_uid = station["StationUID"].replace("NWT", "").replace("TPE", "")
                        bike_station = YoubikeStation(
                            station_name=area,
                            bike_name=station["StationName"],
                            bike_uid=bike_uid,
                            bike_latitude=station["PositionLat"],
                            bike_longitude=station["PositionLon"],
                            bike_address=station["StationAddress"]
                        )
                        db.add(bike_station)
            
            await db.commit()
        print("YouBike數據插入成功")
    except Exception as e:
        await db.rollback()
        print(f"插入YouBike數據時發生錯誤: {e}")
        raise

async def insert_mrt_data(file_path: str, name_dict_path: str, station_sid_path: str, db: AsyncSession):
    try:
        async with db.begin():
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
            with open(name_dict_path, "r", encoding="utf-8") as file:
                name_data = json.load(file)
            with open(station_sid_path, "r", encoding="utf-8") as file:
                station_sid = json.load(file)

            for station in data:
                id = station['StationID']
                mrt_station = MRTStation(
                    station_id = id,
                    station_sid = station_sid[id]['stationSid'],
                    station_name = station['stationName']['Zh_tw'],
                    stations_for_bus = name_data[station['stationName']['Zh_tw']],
                    station_name_en = station['stationName']['En'],
                    latitude = station['lat'],
                    longitude = station['lon']
                )
                db.add(mrt_station)
        
            await db.commit()
        print("捷運站數據插入成功")
    except Exception as e:
        await db.rollback()
        print(f"插入捷運站數據時發生錯誤: {e}")
        raise

async def main():
    try:
        async for db in get_db():
            # 插入公車數據
            await insert_bus_data("./data_json/processed_bus_data.json", db)
            
            # 插入YouBike數據
            await insert_youbike_data("./data_json/bike_results.json", db)
            
            # 插入捷運站數據
            await insert_mrt_data("./data_json/datas.json", "name_dict.json", "station-sid.json", db)
            
            break  
    except Exception as e:
        print(f"發生錯誤: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())