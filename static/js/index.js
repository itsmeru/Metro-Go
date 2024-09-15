import {getStation,getTicket,getStationTimes,haversineDistance } from "./getFunction.js";
import { subscribeToStation, unsubscribeFromStation, subscribeToBike, unsubscribeFromBike,subscribeToBus,unsubscribeFromBus} from "./websockets.js";
import { lines, lineCoordinates } from "./coord.js"
import { currentDisplay, currentTicket, encodeName, decodeName, updateVar, svg, serverName } from "./globalVar.js"
import { updateTickets, updateTimes } from "./updateStatus.js"
import { createCountdownCircle, updateCountdownCircle } from "./circle.js"
import { getCurrentPosition} from "./gps.js";
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
    const ticket = await getTicket(position);
    const times = await getStationTimes(position, stationIds);
    // 定義路線顏色映射
    const lineColors = {
        'R': "#CE0000",
        'G': "green",
        'O': "orange",
        'BL': "blue",
        'BR': "#B18145",
        'Y': "#FFD700"
    };

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
                <h3>旅程規劃(請在地圖上點選起迄站)</h3>
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
        document.getElementById('goButton').addEventListener('click', ()=>{
            calculateTrip();
            document.getElementById('goButton').disabled = true;
        });
        document.getElementById('resetButton').addEventListener('click', ()=>{
            resetSelection();
            document.getElementById('goButton').disabled = false;
        });
      
        document.getElementById('closeTripInfo').addEventListener('click',()=>{
            document.getElementById('refreshButton').style.display = 'none';

        })   
    }
  
    function toggleTripPlanner() {
        tripPlannerActive = !tripPlannerActive;
        const tripInfoDiv = document.getElementById('tripInfo');
        const metroMap = d3.selectAll('.station-group,path:not(.route-group path)');
    
        if (tripPlannerActive) {
            tripInfoDiv.style.display = 'block';
            clearStationBoxes();
            if (metroMap) {
                metroMap.style('opacity', 0.7); ;
            }
        } else {
            closeTripPlanner();
            if (metroMap) {
                metroMap.style('opacity', 1); ;
            }
        }
    }
    function closeTripPlanner() {
        tripPlannerActive = false;
        const tripInfoDiv = document.getElementById('tripInfo');
        const metroMap = d3.selectAll('.station-group,path:not(.route-group path)');

        tripInfoDiv.style.display = 'none';
        const routeDisplay = document.getElementById('routeDisplay');
        routeDisplay.style.display = 'none';
        if (metroMap){
            metroMap.style('opacity', 1); ;
        }
        svg.selectAll('.route-group').remove();
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
        document.getElementById('startPointDisplay').textContent = '起站: 未選擇';
        document.getElementById('endPointDisplay').textContent = '訖站: 未選擇';
        document.getElementById('goButton').disabled = true;
        const routeDisplay = document.getElementById('routeDisplay');
        routeDisplay.style.display = 'none';
        d3.selectAll('.station-box').attr('fill', 'white');
        svg.selectAll('.route-group').remove();
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
        let startStation = startPointDisplay.split(" ")[1];
        let endStation= endPointDisplay.split(" ")[1];
        
        const url = `${serverName}/api/mrt/planning?start_station_id=${encodeURIComponent(startStationId)}&end_station_id=${encodeURIComponent(endStationId)}`;
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
            let selectedData;
           
            selectedData = data["result"][0];
         
            
            displayRoutes(selectedData, startStation, endStation);
            // 在這裡處理返回的數據
            document.getElementById('refreshButton').style.display = 'block';
            } catch (error) {
            console.error("There was a problem with the fetch operation:", error);
        }
        

    }
    function getLineColor(stationCode) {
            
        let lineCode = stationCode.charAt(0);

        if (lineColors.hasOwnProperty(stationCode.substring(0, 2))) {
            lineCode = stationCode.substring(0, 2);
        }
        
        return lineColors[lineCode] || "#CCCCCC"; 
    }

  
    function displayRoutes(data, startStation, endStation) {
        const routeDisplay = document.getElementById('routeDisplay');
        routeDisplay.innerHTML = '';
        routeDisplay.style.display = 'block';
        
        const mainHeader = document.createElement('h2');
        mainHeader.textContent = `從 ${startStation} 到 ${endStation} 的可行路線`;
        routeDisplay.appendChild(mainHeader);
    
        // 清除之前的路徑
        svg.selectAll('.route-group').remove();
    
        // 創建新的路徑組
        const routeGroup = svg.append('g')
            .attr('class', 'route-group')
            .attr('opacity', 1);
        
       
        data.options.forEach((option, pathIndexs) => {

            const pathElement = document.createElement('div');
            pathElement.className = 'path';
    
            const optionElement = document.createElement('div');
            optionElement.className = 'option';
    
            const totalMinutes = Math.floor(option.total_time / 60);
            const totalSeconds = Math.round(option.total_time % 60);
            const arrivalTime = new Date(option.arrival_time);
            
            optionElement.innerHTML = `
                <button id="refreshButton" aria-label="更新時間">
                    <i class="fas fa-sync-alt"></i>
                </button>
                <p>總行程時長： ${totalMinutes} 分 ${totalSeconds} 秒</p>
                <p>預計到達時間： 
                ${new Date(arrivalTime).toLocaleTimeString('zh-TW', {hour: '2-digit', minute:'2-digit', timeZone: 'Asia/Taipei', hour12: false})} 
                </p>
            `;
            
            const refreshButton = optionElement.querySelector('#refreshButton');
            refreshButton.addEventListener('click', calculateTrip);
    
            const detailsList = document.createElement('ul');
    
            option.journey_details.forEach((detail, index) => {
                
                const detailItem = document.createElement('li');
                const minutes = Math.floor(detail.time / 60);
                const seconds = Math.round(detail.time % 60);
                
                let stationCode, stationColor;
                if (detail.action === '等待') {
                    stationCode = detail.station_id;
                    stationColor = getLineColor(stationCode);
                    detailItem.innerHTML = `
                        <span class="line-color">${detail.station}</span>
                        <div>等待 ${minutes} 分 ${seconds} 秒, 往<span class="direction-color">${detail.direction}</span>方向</div>
                        <div>搭乘 
                        ${new Date(detail.train_time).toLocaleTimeString('zh-TW', {hour: '2-digit', minute:'2-digit', timeZone: 'Asia/Taipei', hour12: false})} 
                        的列車</div>
                    `;
                } else if (detail.action === '乘車' && index === option.journey_details.length - 1) {
                    stationCode = detail.station_id;
                    stationColor = getLineColor(stationCode);
                    detailItem.innerHTML = `
                        <span class="line-color">${detail.to_station}</span>
                        <div>抵達時間: 
                        ${new Date(arrivalTime).toLocaleTimeString('zh-TW', {hour: '2-digit', minute:'2-digit', timeZone: 'Asia/Taipei', hour12: false})} 
                        </div>
                    `;
                } else if (detail.action === '轉乘') {
                    
                    stationCode = detail.station_id;
                    stationColor = getLineColor(stationCode);
                    detailItem.innerHTML = `
                        <span class="line-color">${detail.station}</span>
                        <div>轉乘步行約 ${minutes} 分鐘</div>
                    `;
                
                }
                
            
                // 設置背景顏色
                const lineColorElement = detailItem.querySelector('.line-color');
                const directionColor = detailItem.querySelector('.direction-color');
                if (lineColorElement) {
                    lineColorElement.style.backgroundColor = stationColor;
                }
                if(directionColor){
                    directionColor.style.color = stationColor;
                    directionColor.style.padding = '0';
                    directionColor.style.margin = '0 5px';
                }
                

                if (detailItem.innerHTML !== '') {
                    detailsList.appendChild(detailItem);
                }
                
            });
    
            optionElement.appendChild(detailsList);
            pathElement.appendChild(optionElement);
            routeDisplay.appendChild(pathElement);
    
            drawPathAndStations(routeGroup, data.path[1]);
        });
    }
    
    function drawPathAndStations(routeGroup, stationCodes) {
        
        const pathCoordinates = stationCodes.map(getStationCoordinates).filter(coord => coord !== null);
        
        if (pathCoordinates.length > 1) {
            const pathColor = "#484848";  // 路徑
            const stationFillColor = "#FFFFFF";  // 點
            const stationStrokeColor = "#696969";  // 邊框
    
            // 路徑
            routeGroup.append('path')
                .datum(pathCoordinates)
                .attr('d', d3.line()
                    .x(d => d.x+2)
                    .y(d => d.y)
                    .curve(d3.curveLinear))
                .attr('stroke-width', 15)
                .attr('stroke', pathColor)
                .attr('fill', 'none')
          
            // 站點
            routeGroup.selectAll('.station-point')
                .data(pathCoordinates)
                .enter()
                .append('circle')
                .attr('class', 'station-point')
                .attr('cx', d => d.x+2)
                .attr('cy', d => d.y+3)
                .attr('r', 9)  
                .attr('fill', stationFillColor)
                .attr('stroke', stationStrokeColor)
                .attr('stroke-width', 4);
    
           
        }
    }
    
    function getStationCoordinates(stationCode) {
        
        for (const lineName in lines) {
            const station = lines[lineName].stations.find(s => s.stationId === stationCode);
            if (station) {
                return { x: station.x, y: station.y,};
            }
        }
        console.warn(`無法找到站點代碼 ${stationCode} 的座標`);
        return null;
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
    const coordinates = lineCoordinates[lineName];
        
    if (lineName === "O Line") {
        const mainSegmentEnd = 20;  
        const branchStart = 21;     

        for (let i = 0; i <= mainSegmentEnd; i++) {
            StationToLine(stations[i], lines[lineName], coordinates[i][0], coordinates[i][1]);
            if (i < mainSegmentEnd) {
                StationToLine(stations[i+1], lines[lineName], coordinates[i+1][0], coordinates[i+1][1]);
            }
        }

        for(let i=20;i>=11;i--){
            StationToLine(stations[i], lines[lineName], coordinates[i][0], coordinates[i][1]);
        }
        StationToLine(stations[branchStart], lines[lineName], coordinates[branchStart][0], coordinates[branchStart][1]);

        for (let i = branchStart; i < coordinates.length - 1; i++) {
            StationToLine(stations[i], lines[lineName], coordinates[i][0], coordinates[i][1]);
            StationToLine(stations[i+1], lines[lineName], coordinates[i+1][0], coordinates[i+1][1]);
        }
    }else if (lineName === "GREEN Line") {
        const mainSegmentEnd = 18
        for (let i = 0; i < mainSegmentEnd; i++) {
            StationToLine(stations[i], lines[lineName], coordinates[i][0], coordinates[i][1]);
            if (i < mainSegmentEnd) {
                StationToLine(stations[i+1], lines[lineName], coordinates[i+1][0], coordinates[i+1][1]);
            }
        }
        for(let i=18;i>=2;i--){
            StationToLine(stations[i], lines[lineName], coordinates[i][0], coordinates[i][1]);
        }
        StationToLine(stations[19], lines[lineName], coordinates[19][0], coordinates[19][1]);
        StationToLine(stations[2], lines[lineName], coordinates[2][0], coordinates[2][1]);
        StationToLine(stations[1], lines[lineName], coordinates[1][0], coordinates[1][1]);
        StationToLine(stations[0], lines[lineName], coordinates[0][0], coordinates[0][1]);


    }
    else {
        // 处理其他线路的站点
        lineCoordinates[lineName].forEach((coords, idx) => {
            StationToLine(stations[idx], lines[lineName], coords[0], coords[1]);
        });
    }
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
            if (info.noData) {
                dynamicInfo.innerHTML = `
                    <h2>列車進站動態</h2>
                    <div class="update-info">
                        <div class="current-location">現在位置: ${stationName}</div>
                        <div class="no-data-message">目前沒有可用的數據</div>
                        <div class="last-update">最後更新: ${new Date(info.lastUpdate).toLocaleString()}</div>
                    </div>
                `;
                return;
            }
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
        const dynamicInfo = document.querySelector(".dynamic-bike");
        if (!dynamicInfo) {
            console.error("No element with class 'dynamic-bike' found");
            return;
        }
        
       
        try {
            if (info.noData) {
                dynamicInfo.innerHTML = `
                    <h2>YouBike 動態</h2>
                    <div class="update-info">
                        <div class="current-location">現在位置: ${stationName}</div>
                        <div class="no-data-message">目前沒有可用的 YouBike 數據</div>
                        <div class="last-update">最後更新: ${new Date(info.lastUpdate).toLocaleString()}</div>
                    </div>
                `;
                return;
            }
    
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
    
            const bikeInfoContainer = document.createElement("div");
            bikeInfoContainer.className = "bike-info-container";
            dynamicInfo.appendChild(bikeInfoContainer);
    
            const infoArray = Object.values(info);
            const pageSize = 8;
            const totalPages = Math.ceil(infoArray.length / pageSize);
            let currentPage = 0;
    
            function createPaginationControls() {
                const paginationContainer = document.createElement("div");
                paginationContainer.className = "pagination-container";
    
                const prevButton = document.createElement("button");
                prevButton.className = "pagination-button";
                prevButton.addEventListener("click", () => changePage(currentPage - 1));
    
                const nextButton = document.createElement("button");
                nextButton.className = "pagination-button";
                nextButton.addEventListener("click", () => changePage(currentPage + 1));
    
                const pageIndicator = document.createElement("div");
                pageIndicator.className = "page-indicator-bike";
    
                paginationContainer.append(prevButton, pageIndicator, nextButton);
                dynamicInfo.insertBefore(paginationContainer, bikeInfoContainer);
            }
    
            function updatePagination() {
                const pageIndicator = dynamicInfo.querySelector(".page-indicator-bike");
                pageIndicator.innerHTML = '';
    
                for (let i = 0; i < totalPages; i++) {
                    const pageNumber = document.createElement("span");
                    pageNumber.textContent = i + 1;
                    pageNumber.className = i === currentPage ? "page-number current-page" : "page-number";
                    pageNumber.addEventListener("click", () => changePage(i));
                    pageIndicator.appendChild(pageNumber);
                }
            }
    
            function displayPage(page) {
                bikeInfoContainer.innerHTML = `
                    <div class="metro-coming header">
                        <div class='coming-title'>地點</div>
                        <div class='coming-title'>可還車數量</div>
                        <div class='coming-title'>可租車數量</div>
                    </div>
                `;
    
                const start = page * pageSize;
                const end = Math.min(start + pageSize, infoArray.length);
    
                for (let i = start; i < end; i++) {
                    const bikeInfo = infoArray[i];
                    const div = document.createElement("div");
                    div.className = "metro-coming";
    
                    const bikeNameDiv = document.createElement("div");
                    bikeNameDiv.className = "coming-info";
                    bikeNameDiv.textContent = bikeInfo["StationName"] || "N/A";
    
                    const returnDiv = document.createElement("div");
                    returnDiv.className = "coming-info";
                    returnDiv.textContent = bikeInfo["AvailableReturnBikes"] ? `${bikeInfo["AvailableReturnBikes"]}` : "0";
    
                    const rentDiv = document.createElement("div");
                    rentDiv.className = "coming-info";
                    rentDiv.textContent = bikeInfo["AvailableRentBikes"] ? ` ${bikeInfo["AvailableRentBikes"]}` : "0";
    
                    div.append(bikeNameDiv, returnDiv, rentDiv);
                    bikeInfoContainer.appendChild(div);
                }
    
                updatePagination();
            }
    
            function changePage(newPage) {
                currentPage = (newPage + totalPages) % totalPages;
                displayPage(currentPage);
            }
    
            createPaginationControls();
            displayPage(currentPage);
    
        } catch (error) {
            console.error("Error fetching bike info:", error);
            dynamicInfo.textContent = "Error loading bike information.";
        }
    }
    function updateBusDisplay(info, stationName) {
        const dynamicInfo = document.querySelector(".dynamic-bus");
        if (!dynamicInfo) {
            console.error("No element with class 'dynamic-bus' found");
            return;
        }
    
    
        try {
            if (info.noData) {
                dynamicInfo.innerHTML = `
                    <h2>Bus 動態</h2>
                    <div class="update-info">
                        <div class="current-location">現在位置: ${stationName}</div>
                        <div class="no-data-message">目前沒有可用的公車數據</div>
                        <div class="last-update">最後更新: ${new Date(info.lastUpdate).toLocaleString()}</div>
                    </div>
                `;
                return;
            }
    
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
    
            const busInfoContainer = document.createElement("div");
            busInfoContainer.className = "bus-info-container";
            dynamicInfo.appendChild(busInfoContainer);
    
            const infoArray = Object.values(info);
            const pageSize = 8;
            const totalPages = Math.ceil(infoArray.length / pageSize);
          
            
            let currentPage = 0;
    
            function createPaginationControls() {
                const paginationContainer = document.createElement("div");
                paginationContainer.className = "pagination-container";
    
                const prevButton = document.createElement("button");
                prevButton.className = "pagination-button";
                prevButton.addEventListener("click", () => changePage(currentPage - 1));
    
                const nextButton = document.createElement("button");
                nextButton.className = "pagination-button";
                nextButton.addEventListener("click", () => changePage(currentPage + 1));
    
                const pageIndicator = document.createElement("div");
                pageIndicator.className = "page-indicator";
    
                paginationContainer.append(prevButton, pageIndicator, nextButton);
                dynamicInfo.insertBefore(paginationContainer, busInfoContainer);
            }
    
            function updatePagination() {
                const pageIndicator = document.querySelector(".page-indicator");
                pageIndicator.innerHTML = '';
    
                for (let i = 0; i < totalPages; i++) {
                    const pageNumber = document.createElement("span");
                    pageNumber.textContent = i + 1;
                    pageNumber.className = i === currentPage ? "page-number current-page" : "page-number";
                    pageNumber.addEventListener("click", () => changePage(i));
                    pageIndicator.appendChild(pageNumber);
                }
            }
    
            function displayPage(page) {
                busInfoContainer.innerHTML = `
                    <div class="metro-coming header">
                        <div class='coming-title'>公車號碼</div>
                        <div class='coming-title'>倒數進站時間</div>
                        <div class='coming-title'>方向</div>
                    </div>
                `;
    
                const start = page * pageSize;
                const end = Math.min(start + pageSize, infoArray.length);
                
                for (let i = start; i < end; i++) {
                    const busInfo = infoArray[i];
                    const div = document.createElement("div");
                    div.className = "metro-coming";
    
                    const busNameDiv = document.createElement("div");
                    busNameDiv.className = "coming-info";
                    busNameDiv.textContent = busInfo["RouteName"] || "N/A";
    
                    const nowTimeDiv = document.createElement("div");
                    nowTimeDiv.className = "coming-info";
                    nowTimeDiv.textContent = busInfo["EstimateTime"];
    
                    const destinationDiv = document.createElement("div");
                    destinationDiv.className = "coming-info";
                    destinationDiv.textContent = `${busInfo["Direction"]}`;
    
                    div.append(busNameDiv, nowTimeDiv, destinationDiv);
                    busInfoContainer.appendChild(div);
                }
    
                updatePagination();
            }
    
            function changePage(newPage) {
                currentPage = (newPage + totalPages) % totalPages;
                displayPage(currentPage);
            }
    
            createPaginationControls();
            displayPage(currentPage);
    
    
        } catch (error) {
            console.error("Error fetching bus info:", error);
            dynamicInfo.textContent = "Error loading bus information.";
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
        d3.selectAll(`#station-${encodedName}`)
        .attr('fill', "yellow")
       

    
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
            .attr('stroke-width', 9)
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
                .attr('width', 30)
                .attr('height', 30)
                .attr('fill', isDefaultSelected ? "yellow" : "white")
                .attr('stroke', line.color)
                .attr('stroke-width', 3)
                .attr('class', 'station-box')
                .attr('id', `station-${encodedName}`)

            stationGroup.append('text')
                .attr('class', `info-${encodedName}`)
                .attr('x', x+2 )
                .attr('y', y+2)
                .attr('text-anchor', 'middle')
                .attr('alignment-baseline', 'middle')
                .attr('id', 'station-text')
                .text(currentDisplay === "ticket" ? station.full_ticket_price : station.arrive_times)
                .style('fill', 'black')
                .style('pointer-events', 'none')
                .style('font-size', '18px')
                .style('opacity', isDefaultSelected ? 0 : 1);

            const nameLines = splitIntoLines(decodeName(name), 3);
            nameLines.forEach((line, index) => {
                stationGroup.append('text')
                    .attr('x', x + 29)
                    .attr('y', y + 35 + (index * 14))
                    .attr('text-anchor', 'middle')
                    .attr('class', 'label')
                    .text(line)
                    .style('font-size', '18px')
                    .style('fill', 'black')
                    .style('font-weight', '150')
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
                        addPin(this, x, y, "#0070BF", "起");
                        startPin = this;
                    } else if (!endPoint && (stationName !== startPoint || stationId !== startId) ) {
                        endPoint = stationName;
                        document.getElementById('endPointDisplay').textContent = `終點: ${stationName} (${stationId})`;
                        addPin(this, x, y, "#0070BF", "迄");
                        endPin = this;
                        document.getElementById('goButton').disabled = false;
                    }
                    
                    
                } else {
                    updatePositionDisplay(encodedName, stationId);
                }
            })
            .on("mouseover", function() {
                d3.select(this).select(".station-box").attr("fill", "#FFD306")
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
        let count = 0;
        const maxAttempts = 10;
    
        function tryUserPosition() {
            if (count >= maxAttempts) {
                console.log("已嘗試10次，停止更新位置");
                return;
            }
    
            setTimeout(async function() {
                try {
                    const stationInfo = await updatePosition(result);
                    stationIds = stationInfo.stationIds;
                    const stationName = stationIds == "Y16" ? encodeName("Y板橋") : encodeName(stationInfo.position);
    
                    console.log("成功獲取位置信息:", stationName, stationIds);
    
                    updatePositionDisplay(stationName, stationIds);
                } catch (error) {
                    count++;
                    if (error.message === "PERMISSION_DENIED") {
                        console.log("位置更新失敗: 權限被拒絕");
                    } else {
                        console.log(`位置更新失敗 (第${count}次嘗試):`, error.message);
                        if (count < maxAttempts) {
                            tryUserPosition();
                        } else {
                            console.log("已達到最大嘗試次數，停止更新位置");
                        }
                    }
                }
            }, delay);
        }
    
        tryUserPosition();
    }
    // 使用方法
    delayedUserPosition();
   
});