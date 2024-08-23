from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import MRTStation
from db.db_set import get_db
from model.getPlan import getTripPlan
router = APIRouter()

@router.get("/api/mrt/planning")
async def get_plan(
    db: AsyncSession = Depends(get_db), 
    start_station_id: str = Query(..., description="Start station ID"),
    end_station_id: str = Query(..., description="End station ID")
    
):
    async def get_station(station_id):
        query = select(MRTStation).filter(MRTStation.station_id == station_id)
        result = await db.execute(query)
        station = result.scalar_one_or_none()
        if station is None:
            raise HTTPException(status_code=404, detail=f"Station with ID {station_id} not found")
        return station.station_sid

    start_station_sid = await get_station(start_station_id)
    end_station_sid = await get_station(end_station_id)
    result = await getTripPlan(start_station_sid,  end_station_sid )
    return {
        "start_station_sid": start_station_sid,
        "end_station_sid": end_station_sid,
        "result": result
    }