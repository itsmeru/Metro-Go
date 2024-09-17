import { serverName } from "./globalVar.js";

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

async function fetchWithErrorHandling(url, options = {}) {
    try {
        const response = await fetch(url, options);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Error fetching data from ${url}:`, error);
        throw error; // 重新拋出錯誤，讓調用者可以處理
    }
}

export async function getStation() {
    return fetchWithErrorHandling(`${serverName}/api/mrt/name`, {
        headers: { "Content-Type": "application/json" }
    });
}

export async function getTicket(position) {
    return fetchWithErrorHandling(`${serverName}/api/mrt/ticket/${position}`, {
        headers: { "Content-Type": "application/json" }
    });
}

export async function getStationTimes(position, stationId) {
    const url = `${serverName}/api/mrt/time?position=${position}&station_id=${stationId}`;
    return fetchWithErrorHandling(url);
}