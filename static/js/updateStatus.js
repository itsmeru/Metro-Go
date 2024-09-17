import { getTicket,getStationTimes} from "./getFunction.js"
import { lines } from "./coord.js"
import { encodeName} from "./globalVar.js"

export async function updateTickets(position, category){
    if(position==="Y板橋"){
        position = "板橋"
    }
    
    let newTicket = await getTicket(position);
    let updatedStations = new Set(); 

    Object.values(lines).forEach(line => {
        line.stations.forEach(station => {
            if (!updatedStations.has(station.name)) {
                station.full_ticket_price = newTicket[station.name][category];
                if (station.stationId === "Y16"){
                    d3.select(`.info-${encodeName("Y板橋")}`)
                    .text(station.full_ticket_price);
                }
                else{
                    d3.selectAll(`.info-${encodeName(station.name)}`)
                    .text(station.full_ticket_price);
                    if (station.name !== "板橋"){
                        updatedStations.add(station.name);
                    }
                }
               
            }
        });
    });
}

export  async function updateTimes(position, station_Id){
    if(position==="Y板橋"){
        position = "板橋"
    }
    
    let newTime = await getStationTimes(position, station_Id);
    let updatedStations = new Set(); 

    Object.values(lines).forEach(line => {
        line.stations.forEach(station => {
            if (!updatedStations.has(station.name)) {
                let arrive_times = newTime[station.stationId];
                station.arrive_times = arrive_times;
                if (station.name !== "板橋"){
                    d3.selectAll(`.info-${encodeName(station.name)}`)
                    .text(station.arrive_times);
                    updatedStations.add(station.name);
                }
                if (station.stationId !== "Y16"){
                    d3.select(`.info-${encodeName(station.name)}`)
                    .text(station.arrive_times);
                }
                else{
                    d3.select(`.info-${encodeName("Y板橋")}`)
                    .text(station.arrive_times);

                }
            
            }
        });
    });
}