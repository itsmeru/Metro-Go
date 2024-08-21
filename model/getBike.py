import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from db.models import YoubikeStation
import logging
from db.db_set import get_db, engine


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def bike_datas(db: AsyncSession,bike_data_rel):
    bike_data={}
    try:
        query = select(YoubikeStation)
        result = await db.execute(query)
        bike_results = result.scalars().all()
        for bike in bike_results:
            real_item = bike_data_rel.get(bike.bike_uid,{})
            if bike.station_name not in bike_data:
                bike_data[bike.station_name] = []
            bike_data[bike.station_name].append( {
                    "StationUID": bike.bike_uid,
                    "StationName": bike.bike_name,
                    "PositionLat": float(bike.bike_latitude),
                    "PositionLon": float(bike.bike_longitude),
                    "StationAddress": bike.bike_address,
                    "AvailableRentBikes": real_item.get("available_rent_bikes", 0),
                    "AvailableReturnBikes": real_item.get("available_return_bikes", 0)
                })
        
        
        return bike_data

    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

async def get_bike(bike_data):
    async for db in get_db():
        try:
            return await bike_datas(db,bike_data)
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise
        finally:
            await engine.dispose()