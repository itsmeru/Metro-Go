from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from db.db_set import get_db
from model.get_plan import get_travel_plan
from view.render_rsult import render

router = APIRouter(prefix="/api/mrt", tags=["MRT Services"])

@router.get("/planning")
async def get_plan(
    db: AsyncSession = Depends(get_db), 
    start_station_id: str = Query(..., description="Start station ID"),
    end_station_id: str = Query(..., description="End station ID")
    
):
    status_code, data= await get_travel_plan(db,start_station_id,end_station_id)
    return render(status_code, data)
