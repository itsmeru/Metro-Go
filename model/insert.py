import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.models import BusRoute, Station
from db.db_set import get_db, engine
import json

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
        print("Data inserted successfully")
    except Exception as e:
        await db.rollback()
        print(f"An error occurred during insertion: {e}")
        raise

async def main():
    try:
        async for db in get_db():
            await insert_bus_data("processed_bus_data.json", db)
            break  # 如果你只需要执行一次，可以在这里退出循环
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())

# import asyncio
# from sqlalchemy.ext.asyncio import AsyncSession
# from db.models import YoubikeStation
# from db.db import get_db, engine
# import json


# async def insert_youbike_data(file_path: str, db: AsyncSession):
#     async with db.begin():
#         with open(file_path, "r", encoding="utf-8") as file:
#             data = json.load(file)
#             for area, stations in data.items():
#                 for station in stations:
#                     bike_uid = station["StationUID"].replace("NWT", "").replace("TPE", "")
#                     bike_station = YoubikeStation(
#                         station_name=area,
#                         bike_name=station["StationName"],
#                         bike_uid=bike_uid,
#                         bike_latitude=station["PositionLat"],
#                         bike_longitude=station["PositionLon"],
#                         bike_address=station["StationAddress"]
#                     )
#                     db.add(bike_station)
        
#         await db.commit()
#         print("Data inserted successfully")
    

# async def main():
#     async for db in get_db():
#         try:
#             await insert_youbike_data("bike_results.json", db)
#         except Exception as e:
#             print(f"An error occurred: {e}")
#         finally:
#             await engine.dispose()

# if __name__ == "__main__":
#     asyncio.run(main())




# import asyncio
# from sqlalchemy.ext.asyncio import AsyncSession
# import sys
# import os
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# from db.models import MRTStation
# from db.db_set import get_db, engine
# import json

# async def insert_ticket_data(file_path: str, db: AsyncSession):
#     try:
#         async with db.begin():
#             with open(file_path, "r", encoding="utf-8") as file:
#                 data = json.load(file)
#             with open("name_dict.json", "r", encoding="utf-8") as file:
#                 name_data = json.load(file)
            
#             with open("station-sid.json", "r", encoding="utf-8") as file:
#                 station_sid = json.load(file)

#                 for station in data:
#                     id = station['StationID']
#                     mrt_station = MRTStation(
#                         station_id = id,
#                         station_sid =  station_sid[id]['stationSid'],
#                         station_name =station['stationName']['Zh_tw'],
#                         stations_for_bus = name_data[station['stationName']['Zh_tw']],
#                         station_name_en=station['stationName']['En'],
#                         latitude=station['lat'],
#                         longitude=station['lon']
#                     )
#                     db.add(mrt_station)
        
#         await db.commit()
#         print("Data inserted successfully")
#     except Exception as e:
#         await db.rollback()
#         print(f"Error inserting data: {e}")
#         raise

# async def main():
#     async for db in get_db():
#         try:
#             await insert_ticket_data("datas.json", db)
#         except Exception as e:
#             print(f"An error occurred: {e}")
     

# if __name__ == "__main__":
#     asyncio.run(main())

    
