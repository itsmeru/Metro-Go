import asyncio
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select
from sqlalchemy.exc import SQLAlchemyError
from db.models import  StationTime
import logging
from db.db_set import get_db, engine


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

            
async def station_data(db: AsyncSession,startId, endId):
    try:
        query = select( StationTime.arriveTime).filter(and_( StationTime.startStationId == startId , StationTime.endStationId == endId))
        result = await db.execute(query)
        time_results = result.scalar_one_or_none()
    
        return time_results
     

    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

async def get_station_time(startId, endId):
    async for db in get_db():
        try:
            return await station_data(db,startId, endId)
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise
      