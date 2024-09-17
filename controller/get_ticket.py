from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.db_set import get_db
from model.get_ticket import getTicket
from view.render_rsult import render

router = APIRouter(prefix="/api/mrt", tags=["MRT Services"])

@router.get("/ticket/{position}")
async def get_ticket(position: str, db: AsyncSession = Depends(get_db)):
    if position == "台北101-世貿":
        position = "台北101/世貿"
    
    status_code, data = await getTicket(db, position)
    return render(status_code, data)