


# import asyncio
# from sqlalchemy.ext.asyncio import AsyncSession
# import sys
# import os
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# from db.models import BusRoute
# from db.db_set import get_db, engine
# import json


# async def insert_bus_data(file_path: str, db: AsyncSession):
#     async with db.begin():
#         with open(file_path, "r", encoding="utf-8") as file:
#             data = json.load(file)
           
#             for routeId, routeName in data.items():
#                 bus_route = BusRoute(
#                     route_id = routeId,
#                     departure_stop_name_zh = routeName["DepartureStopNameZh"],
#                     destination_stop_name_zh = routeName["DestinationStopNameZh"],
#                     update_time = routeName["UpdateTime"],
#                 )
#                 db.add(bus_route)

        
#         await db.commit()
#         print("Data inserted successfully")
    

# async def main():
#     async for db in get_db():
#         try:
#             await insert_bus_data("bus_dest.json", db)
#         except Exception as e:
#             print(f"An error occurred: {e}")
#         finally:
#             await engine.dispose()

# if __name__ == "__main__":
#     asyncio.run(main())


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




import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.models import MRTStation
from db.db_set import get_db, engine
import json

async def insert_ticket_data(file_path: str, db: AsyncSession):
    try:
        async with db.begin():
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
            with open("name_dict.json", "r", encoding="utf-8") as file:
                name_data = json.load(file)
            
            with open("station-sid.json", "r", encoding="utf-8") as file:
                station_sid = json.load(file)

                for station in data:
                    id = station['StationID']
                    mrt_station = MRTStation(
                        station_id = id,
                        station_sid =  station_sid[id]['stationSid'],
                        station_name =station['stationName']['Zh_tw'],
                        stations_for_bus = name_data[station['stationName']['Zh_tw']],
                        station_name_en=station['stationName']['En'],
                        latitude=station['lat'],
                        longitude=station['lon']
                    )
                    db.add(mrt_station)
        
        await db.commit()
        print("Data inserted successfully")
    except Exception as e:
        await db.rollback()
        print(f"Error inserting data: {e}")
        raise

async def main():
    async for db in get_db():
        try:
            await insert_ticket_data("datas.json", db)
        except Exception as e:
            print(f"An error occurred: {e}")
    

if __name__ == "__main__":
    asyncio.run(main())

    
