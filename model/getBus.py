from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from db.models import BusRoute, MRTStation
import logging
from db.db_set import get_db, engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def bus_datas(db: AsyncSession,bus_data):
    bus_live_datas = defaultdict(list)

    try:
        query = select(MRTStation)
        mrt_name_result = await db.execute(query)
        mrt_name_results = mrt_name_result.scalars().all()

        query = select(BusRoute)
        bus_result = await db.execute(query)
        bus_results = bus_result.scalars().all()
        
        bus_destination = {route.route_id: {
            "DepartureStopNameZh": route.departure_stop_name_zh,
            "DestinationStopNameZh": route.destination_stop_name_zh
        } for route in bus_results}

        mrt_name = [station.stations_for_bus for station in mrt_name_results ]
        name_dic = {station.stations_for_bus :station.station_name for station in mrt_name_results }
      
        for mrt_station in mrt_name:
            for data in bus_data:
                for item in data:
                    bus_name = item["RouteName"]["Zh_tw"]
                    direction = item["Direction"]
                    stop_name = item["StopName"]["Zh_tw"]
                    destination = bus_destination.get(bus_name, {}).get("DestinationStopNameZh" if direction == 0 else "DepartureStopNameZh")
                    if not destination:
                        for key, value in bus_destination.items():
                            if bus_name in key:
                                destination = value["DestinationStopNameZh" if direction == 0 else "DepartureStopNameZh"]
                                break

                    if mrt_station == "板橋站":
                        mrt_station = "板橋車站(文化路)"
                    
                    if mrt_station in stop_name:
                        if mrt_station != "板橋車站(文化路)":
                            mrt_station = name_dic.get(mrt_station, mrt_station)
                        else:
                            mrt_station = "板橋"
                        
                        estimate_minutes = int(item["EstimateTime"]) // 60
                        if mrt_station not in bus_live_datas:
                            bus_live_datas[mrt_station] = []
                        bus_live_datas[mrt_station].append({
                            "bus_name": bus_name,
                            "Direction": direction,
                            "EstimateTime": f'{estimate_minutes} 分' if estimate_minutes > 0 else '即將進站',
                            "UpdateTime": item["UpdateTime"],
                            "destination": destination
                        })
        return  bus_live_datas

    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

async def get_bus(bus_data):
    async for db in get_db():
        try:
            return await bus_datas(db,bus_data)
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise
       