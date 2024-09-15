from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from db.models import MRTStation
import logging

async def getMrtName(db) :
    try:
        station_data = []
        query = select(MRTStation)
        result = await db.execute(query)
        stations = result.scalars().all()
        
        if not stations:
            return 404, {"error": "No MRT stations found"}
        
        for station in stations:
            station_data.append({
                "StationID": station.station_id,
                "stationName": {
                    "Zh_tw": station.station_name,
                    "En": station.station_name_en
                },
                "lon": station.longitude,
                "lat": station.latitude
            })
        
        return 200, station_data

    except SQLAlchemyError as e:
        # 資料庫錯誤，記錄錯誤並返回500錯誤
        logging.error(f"Database error: {str(e)}")
        return 500, {"error": "Database error occurred"}

    except Exception as e:
        # 其他未預期的錯誤，記錄錯誤並返回500錯誤
        logging.error(f"Unexpected error: {str(e)}")
        return 500, {"error": "Internal server error"}