from sqlalchemy.future import select
from db.models import TicketPrice 

async def getTicket(db, position):
    result = await db.execute(select(TicketPrice).where(TicketPrice.start_station == position))
    results = result.scalars().all()
    if not results:
        return 404, {"message": "Position not found"}

    entry = {item.end_station: {"full_ticket_price":item.full_ticket_price,"senior_card_price":item.senior_card_price,"taipei_child_discount":item.taipei_child_discount} for item in results}
    
    return 200, entry
