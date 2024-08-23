let socket;
let latestData = new Map();
let subscribers = new Map();
let cache = new Map();

const WEBSOCKET_URL = "ws://localhost:8765";  // 使用單一端口
const reconnectInterval = 5000;

function connectWebSocket() {
    socket = new WebSocket(WEBSOCKET_URL);

    socket.onopen = () => console.log("WebSocket connected");

    socket.onmessage = (event) => {
        let message = JSON.parse(event.data);

        if (['station', 'bike', 'bus'].includes(message.type)) {
            latestData.set(message.type, updateDynamicInfo(message.type, message.data));
            notifySubscribers(message.type);
        } else {
            console.log("Received unknown data type:", message.type);
        }
    };

    socket.onclose = (event) => {
        console.log("WebSocket closed:", event.reason);
        setTimeout(connectWebSocket, reconnectInterval);
    };

    socket.onerror = (error) => console.error("WebSocket error:", error);
}

function subscribe(type, stationName, callback) {
    // console.log(`GET ${type}:`, stationName);
    if (!subscribers.has(type)) {
        subscribers.set(type, new Map());
    }
    subscribers.get(type).set(stationName, callback);

    if (cache.get(type)?.has(stationName)) {        
        callback(cache.get(type).get(stationName), stationName);
    }
}

function unsubscribe(type, stationName) {
    subscribers.get(type)?.delete(stationName);
}

function notifySubscribers(type) {
    const data = latestData.get(type);
    subscribers.get(type)?.forEach((callback, stationName) => {
        const info = data[stationName];
        if (info) callback(info, stationName);
    });
}

function updateDynamicInfo(type, data) {

    let liveData = {};
    Object.entries(data).forEach(([stationName, info]) => {
        liveData[stationName] = { ...info };
        if (!cache.has(type)) {
            cache.set(type, new Map());
        }
        cache.get(type).set(stationName, info);        
    });
    console.log(type,liveData);
    return liveData;
   
    
}

connectWebSocket();

window.addEventListener("beforeunload", () => {
    if (socket) socket.close();
});

export function subscribeToStation(stationName, callback) {
    subscribe('station', stationName, callback);
}

export function unsubscribeFromStation(stationName) {
    unsubscribe('station', stationName);
}

export function subscribeToBike(stationName, callback) {
    subscribe('bike', stationName, callback);
}

export function unsubscribeFromBike(stationName) {
    unsubscribe('bike', stationName);
}

export function subscribeToBus(stationName, callback) {
    subscribe('bus', stationName, callback);
}

export function unsubscribeFromBus(stationName) {
    unsubscribe('bus', stationName);
}