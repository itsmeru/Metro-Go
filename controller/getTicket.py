from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from db.db_set import get_db
from db.models import TicketPrice  

router = APIRouter()

@router.get("/api/mrt/ticket/{position}")
async def ticket(position: str, db: AsyncSession = Depends(get_db)):
    if position == "台北101-世貿":
        position = "台北101/世貿"
    
    result = await db.execute(select(TicketPrice).where(TicketPrice.start_station == position))
    results = result.scalars().all()
    if not results:
        raise HTTPException(status_code=404, detail="Position not found")

    entry = {item.end_station: {"full_ticket_price":item.full_ticket_price,"senior_card_price":item.senior_card_price,"taipei_child_discount":item.taipei_child_discount} for item in results}
    
    return JSONResponse(content=entry)
