export function haversineDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // 地球半徑，單位為公里
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = 
        Math.sin(dLat/2) * Math.sin(dLat/2) +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
        Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    
    return R * c; // 返回距離，單位為公里
}

export async function getStation(){
    let res = await fetch("/api/mrt/name",{
        "Content-type":"application/json"
    });
    let result = await res.json();
    // console.log(result);
    return result;
}

export async function getTicket(position){
    let res = await fetch(`/api/mrt/ticket/${position}`,{
        "Content-type":"application/json"
    });
    let result = await res.json();
    return result;
}


export async function getStationTimes(position, stationId) {
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




