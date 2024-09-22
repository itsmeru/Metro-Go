export let position = "民權西路";
export let stationIds = "O11";
export let currentDisplay = "ticket";
export let currentTicket = "full_ticket_price";
export let userLat = 0;
export let userLon = 0;
export let tripPlannerActive = false;
export let svg = d3.select('#metro-map');
export const serverName = "https://api.ruru888.com";


export function encodeName(name) {
    return name.replace(/\//g, '-');
}

export function decodeName(name) {
    return name.replace(/-/g, '/');
}

export function updateVar(vars, change) {
    switch(vars) {
        case "currentDisplay":
            currentDisplay = change;
            break;
        case "position":
            position = change;
            break;
        case "stationIds":
            stationIds = change;
            break;
        case "currentTicket":
            currentTicket = change;
            break;
        case "gpsLat":
            userLat = change;
            break;
        case "gpsLon":
            userLon = change;
            break;
     
    }
}