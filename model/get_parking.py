from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from db.models import Station, ParkingLot
import logging

async def getParking(db, station: str) :
    try:
        query = select(Station, ParkingLot).join(ParkingLot, Station.id == ParkingLot.station_id).where(Station.name == station)
        result = await db.execute(query)
        parking_data = result.fetchall()
        
        if not parking_data:
            return 404, {"message": "No parking data found for this station"}
      
        station_info = {
            "station_latitude": parking_data[0].Station.latitude,
            "station_longitude": parking_data[0].Station.longitude,
        }
        
        parking_lots = [
            {
                "parking_lot_name": row.ParkingLot.name,
                "parking_lot_latitude": row.ParkingLot.latitude,
                "parking_lot_longitude": row.ParkingLot.longitude
            }
            for row in parking_data
        ]
        
        response_data = {
            parking_data[0].Station.name: {
                **station_info,
                "parking_lots": parking_lots
            }
        }
        
        return 200, response_data
    
    except SQLAlchemyError as e:
        logging.error(f"Database error: {str(e)}")
        return 500, {"error": "Database error occurred"}
    
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return 500, {"error": "Internal server error"}