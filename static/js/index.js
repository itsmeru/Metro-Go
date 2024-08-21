import { getStation } from "./getStations.js";
import { getTicket } from "./getTickets.js";
import { getStationTimes } from "./getTime.js";
import { subscribeToStation, unsubscribeFromStation, subscribeToBike, unsubscribeFromBike,subscribeToBus,unsubscribeFromBus} from "./websockets.js";
import { lines, lineCoordinates } from "./coord.js"
import { currentDisplay, currentTicket, encodeName, decodeName, updateVar, svg } from "./globalVar.js"
import { updateTickets, updateTimes } from "./updateStatus.js"
import { createCountdownCircle, updateCountdownCircle } from "./circle.js"
import { getCurrentPosition} from "./gps.js";
import {  haversineDistance } from "./distance.js"
import { getParking }from "./getParking.js"

document.addEventListener('DOMContentLoaded', async () => {
    let position = "民權西路";
    let stationIds = "O11";
    
    const result = await getStation();
    console.log(result);
    
    const ticket = await getTicket(position);
    const times = await getStationTimes(position, stationIds);

    // 初始化地圖
    initializeMap();

    

    async function updatePosition(stations) {        
        return new Promise((resolve, reject) => {
            const user_position = getCurrentPosition();
            if (user_position === "PERMISSION_DENIED") {
                reject(new Error("PERMISSION_DENIED"));
            }
            let minDistance = Infinity;
            if (user_position) {
                const userLat = user_position.latitude;
                const userLon = user_position.longitude;
                for (let i = 0; i < stations.length; i++) {
                    const targetLat = stations[i]["lat"];
                    const targetLon = stations[i]["lon"];
                    const distance = haversineDistance(userLat, userLon, targetLat , targetLon);
                    if (distance < minDistance) {
                        minDistance = distance;
                        position = stations[i]["stationName"]["Zh_tw"];
                        stationIds = stations[i]["StationID"]
                    }
                }
                resolve({ position: position, stationIds: stationIds });
               
            } else {
                reject(new Error("位置信息暫時不可用"));
            }
        });
    }

    function initializeMap() {
        assignStationsToLine("BL Line", result.slice(0, 23));
        assignStationsToLine("BR Line", result.slice(23, 47));
        assignStationsToLine("GREEN Line", result.slice(47, 67));
        assignStationsToLine("O Line", result.slice(67, 93));
        assignStationsToLine("Red Line", result.slice(93, 121));
        assignStationsToLine("Y Line", result.slice(121));

        Object.entries(lines).forEach(([lineName, line]) => {
            drawStations(lineName, line);
        });
    }

    function assignStationsToLine(lineName, stations) {
        lineCoordinates[lineName].forEach((coords, idx) => {
            if (stations[idx]) {
                StationToLine(stations[idx], lines[lineName], coords[0], coords[1]);
            }
        });
    }

    function StationToLine(station, line, x, y) {
        const name = station["stationName"]["Zh_tw"];
        const full_ticket_price = ticket[name]?.["full_ticket_price"] || "N/A";
        const senior_card_price = ticket[name]?.["senior_card_price"] || "N/A";
        const taipei_child_discount = ticket[name]?.["taipei_child_discount"] || "N/A";
        const stationId = station["StationID"];
        const arrive_times = times[stationId] || "N/A";
        const data = { name, x, y, full_ticket_price, senior_card_price, taipei_child_discount, arrive_times, stationId };
        line.stations.push(data);
    }

    function updateStationDisplay(info, stationName) {
        const dynamicInfo = document.querySelector(".dynamic-info");
        if (!dynamicInfo) {
            console.error("No element with class 'dynamic-info' found");
            return;
        }

        try {
            dynamicInfo.innerHTML = `
                <h2>列車進站動態</h2>
                <div class="update-info">
                    <div class="update-countdown">下次更新: </div>
                    <div class="current-location">現在位置: ${stationName}</div>
                </div>
            `;
            const countdownCircle = createCountdownCircle();
            dynamicInfo.appendChild(countdownCircle);

            const countDown = 10;
            let timeLeft = countDown;
            const countdownInterval = setInterval(() => {
                if (timeLeft <= 0) {
                    clearInterval(countdownInterval);
                } else {
                    updateCountdownCircle(countdownCircle, timeLeft, countDown);
                    timeLeft--;
                }
            }, 1000);
            const div = document.createElement("div");
            div.innerHTML = `
            <div class='coming-title'>時間</div>
            <div class='coming-title'>倒數進站</div>
            <div class='coming-title'>方向</div>
            `
            div.className = "metro-coming";
            dynamicInfo.appendChild(div);
            for (const key in info) {
                const div = document.createElement("div");
                div.className = "metro-coming";

                const nowTimeDiv = document.createElement("div");
                nowTimeDiv.className = "coming-info";
                nowTimeDiv.textContent = info[key]["NowDateTime"] || "N/A";

                const countDiv = document.createElement("div");
                countDiv.className = "coming-info";
                countDiv.textContent = info[key].CountDown || "N/A";

                const destinationDiv = document.createElement("div");
                destinationDiv.className = "coming-info";
                destinationDiv.textContent = info[key].DestinationName ? `往 ${info[key].DestinationName}` : "N/A";

                div.append(nowTimeDiv, countDiv, destinationDiv);
                dynamicInfo.appendChild(div);
            }
        } catch (error) {
            console.error("Error fetching station info:", error);
            dynamicInfo.textContent = "Error loading station information.";
        }
    }

    function updateBikeDisplay(info, stationName) {
        if (info === null){
                dynamicInfo.textContent = "資料更新中";
            const countdownCircle = createCountdownCircle();
            dynamicInfo.appendChild(countdownCircle);
            return ;
        }
        const dynamicInfo = document.querySelector(".dynamic-bike");
        if (!dynamicInfo) {
            console.error("No element with class 'dynamic-bike' found");
            return;
        }

        try {
            dynamicInfo.innerHTML = `
                <h2>YouBike 動態</h2>
                <div class="update-info">
                    <div class="update-countdown">下次更新: </div>
                    <div class="current-location">現在位置: ${stationName}</div>
                </div>
            `;
            const countdownCircle = createCountdownCircle();
            dynamicInfo.appendChild(countdownCircle);

            const countDown = 60;
            let timeLeft = countDown;
            const countdownInterval = setInterval(() => {
                if (timeLeft <= 0) {
                    clearInterval(countdownInterval);
                } else {
                    updateCountdownCircle(countdownCircle, timeLeft, countDown);
                    timeLeft--;
                }
            }, 1000);
            const div = document.createElement("div");
            div.innerHTML = `
                <div class='coming-title'>地點</div>
                <div class='coming-title'>可還車數量</div>
                <div class='coming-title'>可租車數量</div>
                `
            div.className = "metro-coming";
            dynamicInfo.appendChild(div);
            for (const key in info) {
                const div = document.createElement("div");
                div.className = "metro-coming";

                const bikeNameDiv = document.createElement("div");
                bikeNameDiv.className = "coming-info";
                bikeNameDiv.textContent = info[key]["StationName"] || "N/A";

                const returnDiv = document.createElement("div");
                returnDiv.className = "coming-info";
                returnDiv.textContent = info[key]["AvailableReturnBikes"] ? `${info[key]["AvailableReturnBikes"]}` : "0";

                const rentDiv = document.createElement("div");
                rentDiv.className = "coming-info";
                rentDiv.textContent = info[key]["AvailableRentBikes"] ? ` ${info[key]["AvailableRentBikes"]}` : "0";

                div.append(bikeNameDiv, returnDiv, rentDiv);
                dynamicInfo.appendChild(div);
            }
        } catch (error) {
            console.error("Error fetching bike info:", error);
            dynamicInfo.textContent = "Error loading bike information.";
        }
    }
    function updateBusDisplay(info, stationName) {
        if (info === null){
                dynamicInfo.textContent = "資料更新中";
            const countdownCircle = createCountdownCircle();
            dynamicInfo.appendChild(countdownCircle);
            return ;
        }
        const dynamicInfo = document.querySelector(".dynamic-bus");
        if (!dynamicInfo) {
            console.error("No element with class 'dynamic-bus' found");
            return;
        }

        try {
            dynamicInfo.innerHTML = `
                <h2>Bus 動態</h2>
                <div class="update-info">
                    <div class="update-countdown">下次更新: </div>
                    <div class="current-location">現在位置: ${stationName}</div>
                </div>
            `;
            const countdownCircle = createCountdownCircle();
            dynamicInfo.appendChild(countdownCircle);

            const countDown = 30;
            let timeLeft = countDown;
            const countdownInterval = setInterval(() => {
                if (timeLeft <= 0) {
                    clearInterval(countdownInterval);
                } else {
                    updateCountdownCircle(countdownCircle, timeLeft, countDown);
                    timeLeft--;
                }
            }, 1000);
            const div = document.createElement("div");
            div.innerHTML = `
                <div class='coming-title'>公車號碼</div>
                <div class='coming-title'>倒數進站時間</div>
                <div class='coming-title'>方向</div>
                `
            div.className = "metro-coming";
            dynamicInfo.appendChild(div);
            for (const key in info) {
                const div = document.createElement("div");
                div.className = "metro-coming";

                const busNameDiv = document.createElement("div");
                busNameDiv.className = "coming-info";
                busNameDiv.textContent = info[key]["bus_name"] || "N/A";

                const nowTimeDiv = document.createElement("div");
                nowTimeDiv.className = "coming-info";
                nowTimeDiv.textContent = info[key]["EstimateTime"];

                const destinationDiv = document.createElement("div");
                destinationDiv.className = "coming-info";
                destinationDiv.textContent = `${info[key]["destination"]} ${info[key]["Direction"] == 0 ? "(去程)" : "(回程)"}`;

                div.append(busNameDiv, nowTimeDiv, destinationDiv);
                dynamicInfo.appendChild(div);
            }
        } catch (error) {
            console.error("Error fetching bike info:", error);
            dynamicInfo.textContent = "Error loading bike information.";
        }
    }
    let currentSubscribedStation = null;
    async function onStationClick(stationNames) {
        let stationName = decodeName(stationNames);
        if (currentSubscribedStation) {
            unsubscribeFromStation(currentSubscribedStation);
        }
        document.querySelector(".dynamic-info").innerHTML = '<div class="loading">進站動態加載中...</div>';
        subscribeToStation(stationName, updateStationDisplay);
        currentSubscribedStation = stationName;
    }

    let currentSubscribedBike = null;
    async function onBikeClick(stationNames) {
        let stationName = decodeName(stationNames);
        
        if (currentSubscribedBike) {
            unsubscribeFromBike(currentSubscribedBike);
        }
        document.querySelector(".dynamic-bike").innerHTML = '<div class="loading">Youbike動態加載中...</div>';
        subscribeToBike(stationName, updateBikeDisplay);
        currentSubscribedBike = stationName;
    }

    let currentSubscribedBus = null;
    async function  onBusClick(stationNames){
        let stationName = decodeName(stationNames);
        if (stationName === "Y板橋"){
            stationName = "板橋"
        }
        if (currentSubscribedBus) {
            unsubscribeFromBus(currentSubscribedBus);
        }
        document.querySelector(".dynamic-bus").innerHTML = '<div class="loading">公車動態加載中...</div>';
        subscribeToBus(stationName, updateBusDisplay);
        currentSubscribedBus = stationName;
        
    }

    let lastSelectedStation = position;

    function updatePositionDisplay(encodedName, stationId) {
        if (lastSelectedStation) {
            d3.selectAll(`.info-${lastSelectedStation}`)
                .style('opacity', 1);
        }
    
        const currentElement = d3.selectAll(`.info-${encodedName}`);
        currentElement.style('opacity', 0);
    
        lastSelectedStation = encodedName;
    
    
        d3.selectAll('.station-box').attr('fill', "white");
        d3.selectAll(`#station-${encodedName}`).attr('fill', "yellow");
    
        position = encodedName;
        stationIds = stationId;
    
        // 調用相關函數
        onStationClick(encodedName);
        onBikeClick(encodedName);
        onBusClick(encodedName);
    
        // 根據當前顯示模式更新信息
        if (currentDisplay === "ticket") {
            updateTickets(encodedName, currentTicket);
        } else {
            updateTimes(encodedName, stationId);
        }
    }


    function splitIntoLines(text, charsPerLine) {
        const lines = [];
        for (let i = 0; i < text.length; i += charsPerLine) {
            lines.push(text.slice(i, i + charsPerLine));
        }
        return lines;
    }

    function drawStations(lineName, line){
        svg.append('path')
            .datum(line.stations)
            .attr('d', d3.line()
                .x(d => d.x)
                .y(d => d.y)
                .curve(d3.curveLinear))
            .attr('stroke', line.color)
            .attr('stroke-width', 7)
            .attr('fill', 'none');

        line.stations.forEach(station => {
            const { x, y, name, stationId } = station;
            const encodedName = stationId == "Y16" ? encodeName("Y板橋") : encodeName(name);
            
            
            const isDefaultSelected = (encodedName === position && stationId === stationIds);
           
            const stationGroup = svg.append('g')
                .attr('class', 'station-group')
                .attr('cursor', 'pointer');

            stationGroup.append('rect')
                .attr('x', x - 12)
                .attr('y', y - 12)
                .attr('width', 25)
                .attr('height', 25)
                .attr('fill', isDefaultSelected ? "yellow" : "white")
                .attr('stroke', line.color)
                .attr('stroke-width', 2)
                .attr('class', 'station-box')
                .attr('id', `station-${encodedName}`)

            stationGroup.append('text')
                .attr('class', `info-${encodedName}`)
                .attr('x', x - 1)
                .attr('y', y)
                .attr('text-anchor', 'middle')
                .attr('alignment-baseline', 'middle')
                .attr('id', 'station-text')
                .text(currentDisplay === "ticket" ? station.full_ticket_price : station.arrive_times)
                .style('fill', 'black')
                .style('pointer-events', 'none')
                .style('opacity', isDefaultSelected ? 0 : 1);

            const nameLines = splitIntoLines(decodeName(name), 3);
            nameLines.forEach((line, index) => {
                stationGroup.append('text')
                    .attr('x', x)
                    .attr('y', y + 25 + (index * 14))
                    .attr('text-anchor', 'middle')
                    .attr('class', 'label')
                    .text(line)
                    .style('font-size', '12px')
                    .style('fill', 'black')
                    .style('pointer-events', 'none');
            });

            stationGroup.on('click', function() {
                updatePositionDisplay(encodedName, stationId);
            })
            .on("mouseover", function() {
                d3.select(this).select(".station-box").attr("fill", "#D2B48C");
            })
            .on("mouseout", function() {
                
                if (encodedName !== position || stationId !== stationIds) {
                    d3.select(this).select(".station-box").attr("fill", "white");
                } else {
                    d3.select(this).select(".station-box").attr("fill", "yellow");
                }
            });
        });
    }

    const buttonContainer = document.querySelector(".map-overlay");

    function handleButtonClick(event) {
        const clickedElement = event.target;
        const newDisplay = clickedElement.value;
        
        updateVar("currentDisplay", newDisplay);
        if (newDisplay === "ticket") {
            const newTicket = clickedElement.dataset.ticket;
            if (newTicket) {
                updateVar("currentTicket", newTicket);
                updateTickets(position, newTicket);
            } else {
                console.error("無效的票價類型");
            }
        }else if(newDisplay === "parking"){
            getParking();
        }
        else {
            updateTimes(position, stationIds);
        }
    }

    buttonContainer.addEventListener("click", handleButtonClick);

    // 初始化顯示
    onStationClick(position);
    onBikeClick(position);
    onBusClick(position);
    // 嘗試更新用戶位置
    function delayedUserPosition(delay = 1000) {
        setTimeout(async function tryUserPosition() {
            try {
                const stationInfo = await updatePosition(result);
                stationIds = stationInfo.stationIds;
                const stationName= stationIds == "Y16" ? encodeName("Y板橋") : encodeName(stationInfo.position);

                console.log("成功獲取位置信息:", stationName, stationIds);

                updatePositionDisplay(stationName, stationIds);
            } catch (error) {
                if (error.message === "PERMISSION_DENIED") {
                    console.log("位置更新失敗: 權限被拒絕");
                } else {
                    console.log("位置更新失敗:", error.message);
                    // 如果不是權限問題，則在短暫延遲後重試
                    setTimeout(tryUserPosition, delay);
                }
            }
        }, delay);
    }
    
    // 使用方法
    delayedUserPosition();
   
});