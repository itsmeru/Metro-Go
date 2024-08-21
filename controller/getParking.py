from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import Station, ParkingLot
from db.db_set import get_db

router = APIRouter()

@router.get("/api/mrt/parking/{station}")
async def parking(station: str, db: AsyncSession = Depends(get_db)):
    try:
        query = select(Station, ParkingLot).join(ParkingLot, Station.id == ParkingLot.station_id).where(Station.name == station)
        result = await db.execute(query)
        parking_data = result.scalars().all()
        
        if not parking_data:
            return {"message": "No parking data found for this station"}
        
        station_info = {
            "station_latitude": parking_data[0].Station.latitude,
            "station_longitude": parking_data[0].Station.longitude,
        }
        
        # 提取所有停車場信息
        parking_lots = [
            {
                "parking_lot_name": row.ParkingLot.name,
                "parking_lot_latitude": row.ParkingLot.latitude,
                "parking_lot_longitude": row.ParkingLot.longitude
            }
            for row in parking_data
        ]
        
        # 組合最終結果
        return {
            parking_data[0].Station.name: {
                **station_info,
                "parking_lots": parking_lots
            }
        }
    
    except Exception as e:
        print(f"Error retrieving data: {e}")
        raise