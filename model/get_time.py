from db.models import StationTime
from sqlalchemy.future import select

async def getTime(db, position, station_id):
    query = select(StationTime).where(
    (StationTime.startStation == position) & 
    (StationTime.startStationId == station_id)
)
    result = await db.execute(query)
    results = result.scalars().all()
    entry = {}
    data = []
    for item in results:
        entry[item.endStationId] = item.arriveTime
        data.append(entry)
    
    if not results:
        return 404, {"message":"No data found for the given position and station_id"}

    
    return 200, data[0]
