import asyncio
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from db.models import MRTStation
import logging
from db.db_set import get_db, engine


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

            
async def metro_data(db: AsyncSession,real_time_datas):
    station_position_data = defaultdict(list)
    station_name_mapping = {}
    try:
        query = select(MRTStation.station_name,MRTStation.stations_for_bus)
        result = await db.execute(query)
        metro_results = result.fetchall()

        for metro in metro_results:
            station_name_mapping[metro.stations_for_bus] = metro.station_name

        for data in real_time_datas[0]:
            station_name = data["StationName"]
            destination = data["DestinationName"]
            if station_name in station_name_mapping:
                if destination in ["大坪林", "新北產業園區"]:
                    station_name = "Y板橋"
                else:
                    station_name = station_name_mapping.get(station_name, station_name)
                
                station_position_data[station_name].append(data)

        return station_position_data
     

    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

async def get_metro(real_time_datas):
    async for db in get_db():
        try:
            return await metro_data(db,real_time_datas)
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise
      