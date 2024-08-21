from fastapi import *
import json
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import MRTStation
from db.db_set import get_db



router = APIRouter()
@router.get("/api/mrt/name")
async def station_info(db: AsyncSession = Depends(get_db)):
    station_data = []
    query = select(MRTStation)
    result = await db.execute(query)
    results = result.scalars().all()
    for item in results:
        station_data.append({
            "StationID": item.station_id,
            "stationName": {
                "Zh_tw": item.station_name,
                "En": item.station_name_en
            },
            "lon": item.longitude,
            "lat": item.latitude
        })
    return station_data