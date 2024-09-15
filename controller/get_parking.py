from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from model.get_parking import getParking
from view.render_rsult import render
from db.db_set import get_db

router = APIRouter(prefix="/api/mrt", tags=["MRT Services"])

@router.get("/parking/{station}")
async def get_parking(station: str, db: AsyncSession = Depends(get_db)):
    status_code, data = await getParking(db,station)
    return render(status_code, data)
  