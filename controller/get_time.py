from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.db_set import get_db
from model.get_time import getTime
from view.render_rsult import render

router = APIRouter(prefix="/api/mrt", tags=["MRT Services"])

@router.get("/time")
async def get_time(position: str, station_id: str, db: AsyncSession = Depends(get_db)):
    if position == "台北101-世貿":
        position = "台北101/世貿"
    
    status_code, data = await getTime(db, position, station_id)
    return render(status_code, data)
