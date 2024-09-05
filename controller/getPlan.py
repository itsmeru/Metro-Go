from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import MRTStation
from db.db_set import get_db
from model.travelPlan import get_travel_plan
router = APIRouter()

@router.get("/api/mrt/planning")
async def get_plan(
    db: AsyncSession = Depends(get_db), 
    start_station_id: str = Query(..., description="Start station ID"),
    end_station_id: str = Query(..., description="End station ID")
    
):
    result= await get_travel_plan(start_station_id,end_station_id )
    return {
        "result": result,
    }