export let position = "民權西路";
export let stationIds = "O11";
export let currentDisplay = "ticket";
export let currentTicket = "full_ticket_price";

export let svg = d3.select('#metro-map')

export function encodeName(name) {
    return name.replace(/\//g, '-');
}

export function decodeName(name) {
    return name.replace(/-/g, '/');
}

export function updateVar(vars,change) {
    if (vars === "currentDisplay"){
        currentDisplay = change;
    }
    if (vars === "position"){
        position = change;
    }
    if (vars === "stationIds"){
        stationIds = change;
    }
    if (vars === "currentTicket"){
        currentTicket = change;
    }
    

  }