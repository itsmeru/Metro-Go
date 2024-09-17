from fastapi import *
from sqlalchemy.ext.asyncio import AsyncSession
from db.db_set import get_db
from model.get_mrt_name import getMrtName
from view.render_rsult import render


router = APIRouter(prefix="/api/mrt", tags=["MRT Services"])
@router.get("/name")
async def get_station_info(db: AsyncSession = Depends(get_db)):
    
    status_code, data= await getMrtName(db)
    return render(status_code, data)