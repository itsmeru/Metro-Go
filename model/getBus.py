from collections import defaultdict
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.exc import SQLAlchemyError
from db.models import BusRoute, Station
import logging
from db.db_set import async_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def bus_datas(db: AsyncSession, realtime_data):
    try:
        query = (
            select(Station)
            .options(selectinload(Station.bus_routes))
        )
        result = await db.execute(query)
        stations = result.scalars().unique().all()

        realtime_dict = {}
        for realtime_group in realtime_data:
            for rt in realtime_group:
                key = (rt["RouteName"]["Zh_tw"], rt["StopName"]["Zh_tw"])
                realtime_dict[key] = rt

        integrated_data = defaultdict(list)

        for station in stations:
            for route in station.bus_routes:
                key = (route.route_name, route.stop_name)
                matching_realtime = realtime_dict.get(key)

                if matching_realtime:
                    direction = route.destination if matching_realtime["Direction"] == 0 else route.departure
                    path = "去程" if matching_realtime["Direction"] == 0 else "回程"

                    estimate_minutes = int(matching_realtime["EstimateTime"]) // 60
                    estimate_time = f'{estimate_minutes} 分' if estimate_minutes > 0 else '即將進站'

                    integrated_stop = {
                        "RouteName": matching_realtime["RouteName"]["Zh_tw"],
                        "Direction": f"{direction} ({path})",
                        "EstimateTime": estimate_time,
                        "UpdateTime": matching_realtime["UpdateTime"]
                    }
                    integrated_data[station.name].append(integrated_stop)

        return dict(integrated_data)

    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

async def get_bus(realtime_data):
    async with async_session() as db:
        try:
            return await bus_datas(db, realtime_data)
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise