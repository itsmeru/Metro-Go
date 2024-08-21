from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from db.db_set import get_db
from db.models import StationTime

router = APIRouter()

@router.get("/api/mrt/time/")
async def Time(position: str, station_id: str, db: AsyncSession = Depends(get_db)):
    if position == "台北101-世貿":
        position = "台北101/世貿"

    query = select(StationTime).where(
        (StationTime.startStation == position) & 
        (StationTime.startStationId == station_id)
    )
    result = await db.execute(query)
    results = result.scalars().all()
    entry = {}
    data = []
    for item in results:
        entry[item.endStationId] = item.arriveTime
        data.append(entry)
    
    if not results:
        raise HTTPException(status_code=404, detail="No data found for the given position and station_id")

    
    return data[0]
