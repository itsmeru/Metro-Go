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
import { addPin} from "./tripPlanner.js";


document.addEventListener('DOMContentLoaded', async () => {
    let position = "民權西路";
    let stationIds = "O11";
    let tripPlannerActive = false;
    let startPoint = null;
    let endPoint = null;
    let startPin = null;
    let endPin = null;
    let startId = null;

   
    const result = await getStation();
    console.log(result);
    
    const ticket = await getTicket(position);
    const times = await getStationTimes(position, stationIds);

    // 初始化地圖
    initializeMap();
    initializeTripPlanner();

    function initializeTripPlanner() {
        const tripPlannerButton = document.querySelector('#tripPlanButton');

        const tripInfoDiv = document.createElement('div');
        tripInfoDiv.id = 'tripInfo';
        tripInfoDiv.style.display = 'none';
        tripInfoDiv.innerHTML = `
            <div class="trip-info-header">
                <h3>旅程規劃</h3>
                <button id="closeTripInfo">X</button>
            </div>
            <div id="startPointDisplay">起站: 未選擇</div>
            <div id="endPointDisplay">訖站: 未選擇</div>
            <button id="goButton" disabled>Go</button>
            <button id="resetButton">重置</button>
        `;
        document.body.appendChild(tripInfoDiv);

        tripPlannerButton.addEventListener('click', toggleTripPlanner);
        document.getElementById('closeTripInfo').addEventListener('click', closeTripPlanner);
        document.getElementById('goButton').addEventListener('click', calculateTrip);
        document.getElementById('resetButton').addEventListener('click', resetSelection);
    }
    function toggleTripPlanner() {
        tripPlannerActive = !tripPlannerActive;
        const tripInfoDiv = document.getElementById('tripInfo');
        if (tripPlannerActive) {
            tripInfoDiv.style.display = 'block';
            clearStationBoxes();
        } else {
            closeTripPlanner();
        }
    }
    function closeTripPlanner() {
        tripPlannerActive = false;
        const tripInfoDiv = document.getElementById('tripInfo');
        tripInfoDiv.style.display = 'none';
        resetSelection();
        restoreOriginalDisplay();
    }

    function clearStationBoxes() {
        d3.selectAll('.station-box').attr('fill', 'white');
        d3.selectAll('#station-text').text('');
        resetSelection();
        clearPins();
    }

    function resetSelection() {
        startPoint = null;
        endPoint = null;
        document.getElementById('startPointDisplay').textContent = '起點: 未選擇';
        document.getElementById('endPointDisplay').textContent = '終點: 未選擇';
        document.getElementById('goButton').disabled = true;
        d3.selectAll('.station-box').attr('fill', 'white');
        clearPins();
    }

    function restoreOriginalDisplay() {
        if (currentDisplay === "ticket") {
            updateTickets(position, currentTicket);
        } else {
            updateTimes(position, stationIds);
        }
        updatePositionDisplay(position, stationIds);
    }

    function clearPins() {
        d3.selectAll(".pin-marker").remove();
        startPin = null;
        endPin = null;
        
    }

    async function calculateTrip(){
        let startPointDisplay = document.querySelector("#startPointDisplay").textContent;
        let endPointDisplay = document.querySelector("#endPointDisplay").textContent;
        let startStationId = startPointDisplay.split("(")[1].replace(")", "").trim();
        let endStationId = endPointDisplay.split("(")[1].replace(")", "").trim();
        const url = `/api/mrt/planning?start_station_id=${encodeURIComponent(startStationId)}&end_station_id=${encodeURIComponent(endStationId)}`;
        try {
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
    
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
    
            const data = await response.json();
            console.log("Planning result:", data);
            // 在這裡處理返回的數據
        } catch (error) {
            console.error("There was a problem with the fetch operation:", error);
        }
        console.log("2",startStationId,endStationId);
        

    }
    

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
                updateVar("gpsLat",userLat);
                updateVar("gpsLon",userLon);
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
        if (tripPlannerActive) {
            return;
        }
        
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
        updateVar("position",position);
        updateVar("stationIds",stationIds);
    
        // 更新狀態
        onStationClick(encodedName);
        onBikeClick(encodedName);
        onBusClick(encodedName);
    
        if (currentDisplay === "ticket") {
            updateTickets(encodedName, currentTicket);
        } else {
            updateTimes(encodedName, stationId);
        }
    }

    // 字太多換行
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
                    .attr('y', y + 30 + (index * 14))
                    .attr('text-anchor', 'middle')
                    .attr('class', 'label')
                    .text(line)
                    .style('font-size', '14px')
                    .style('fill', 'black')
                    .style('pointer-events', 'none');
            });

            stationGroup.on('click', function() {
                const stationBox = d3.select(this).select(".station-box");
                const stationName = getFullStationName(this);
                const x = parseFloat(stationBox.attr("x")) + 12.5; // 站點中心 X 座標
                const y = parseFloat(stationBox.attr("y")) + 12.5; // 站點中心 Y 座標
        
                if (tripPlannerActive) {
                    if (!startPoint) {
                        startPoint = stationName;
                        startId = stationId;
                        document.getElementById('startPointDisplay').textContent = `起點: ${stationName} (${stationId})`;
                        addPin(this, x, y, "#4CAF50", "S");
                        startPin = this;
                    } else if (!endPoint && stationName !== startPoint || stationId !== startId ) {
                        endPoint = stationName;
                        document.getElementById('endPointDisplay').textContent = `終點: ${stationName} (${stationId})`;
                        addPin(this, x, y, "#FF5722", "E");
                        endPin = this;
                        document.getElementById('goButton').disabled = false;
                    }
                } else {
                    updatePositionDisplay(encodedName, stationId);
                }
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
        function getFullStationName(stationGroup) {
            const labels = d3.select(stationGroup).selectAll('.label');
            return labels.nodes().map(node => node.textContent).join('');
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