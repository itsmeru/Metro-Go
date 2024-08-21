let globalWatchId = null;
let currentPosition = null;

function watchPosition() {
  return new Promise((resolve, reject) => {
    if (!("geolocation" in navigator)) {
      reject(new Error("瀏覽器不支持"));
      return;
    }

    globalWatchId = navigator.geolocation.watchPosition(
      (position) => {
        currentPosition = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude
        };
        // console.log(`位置更新：緯度 ${currentPosition.latitude}，經度 ${currentPosition.longitude}`);
        resolve(currentPosition);
      },
      (error) => {
        switch(error.code) {
          case error.PERMISSION_DENIED:
            console.error("用戶拒絕了地理位置請求");
            reject({ type: "PERMISSION_DENIED", message: "用戶拒絕了地理位置請求" });
            break;
          case error.POSITION_UNAVAILABLE:
            console.error("位置信息不可用");
            reject({ type: "POSITION_UNAVAILABLE", message: "位置信息不可用" });
            break;
          case error.TIMEOUT:
            console.error("請求位置信息超時");
            reject({ type: "TIMEOUT", message: "請求位置信息超時" });
            break;
          default:
            console.error("獲取位置時發生未知錯誤");
            reject({ type: "UNKNOWN_ERROR", message: "獲取位置時發生未知錯誤" });
        }
      },
      {
        enableHighAccuracy: true,
        timeout: 5000,
        maximumAge: 0
      }
    );
  });
}

function clearGeolocationWatch() {
  if (globalWatchId !== null) {
    navigator.geolocation.clearWatch(globalWatchId);
    globalWatchId = null;
    currentPosition = null;
    console.log("地理位置監控已停止");
  }
}

async function initGeolocation() {
  try {
    await watchPosition();
    return currentPosition;
  } catch (error) {
    console.error("初始化地理位置時發生錯誤：", error.message);
    if (error.type === "PERMISSION_DENIED") {
      console.log("用戶拒絕了地理位置請求，將使用默認位置");
      currentPosition = "PERMISSION_DENIED"
    } else {
      console.log("無法獲取位置，將使用默認位置");
    }
  }
}

window.addEventListener('beforeunload', clearGeolocationWatch);

async function main() {
  const position = await initGeolocation();
  if (position) {
    // console.log(`位置：緯度 ${position.latitude}，經度 ${position.longitude}`);
  }
}

main();

function getCurrentPosition() {
  return currentPosition; 
}

export { getCurrentPosition };