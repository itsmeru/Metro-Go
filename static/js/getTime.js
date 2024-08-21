async function getStationTimes(position, stationId) {
    let url = `/api/mrt/time?position=${encodeURIComponent(position)}&station_id=${stationId}`;
    
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        // console.log(data);
        return data;
    } catch (error) {
        console.error('Error fetching station times:', error);
    }
}

export  {getStationTimes};