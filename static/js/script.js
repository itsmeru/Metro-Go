import {position} from "./globalVar.js";
document.addEventListener('DOMContentLoaded', (event) => {

    const parkingButton = document.getElementById('ParkingButton');
    const modal = document.getElementById('parkingModal');
    const closeButton = document.querySelector('.close-button');
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    const buttons = document.querySelectorAll('.map-overlay button');
    const timeInfo = document.querySelector('.time-info');


    // Set the first button as active by default
    buttons[0].classList.add('active');

    buttons.forEach(button => {
        button.addEventListener('click', function() {
            if (button.value === "time") {
                timeInfo.style.display = 'block';
            } else {
                timeInfo.style.display = 'none';
            }
            buttons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
        });
    })
    parkingButton.addEventListener('click', () => {
        modal.style.display = 'block';
        initMap();
    });

    closeButton.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');
            
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            button.classList.add('active');
            document.getElementById(`${tabName}Tab`).classList.add('active');
        });
    });
});


async function initMap() {
    let res = await fetch(`/api/mrt/parking/${position}`);
    let result = await res.json();
    let parking_data = Object.values(result)[0];
    document.getElementById('currentPosition').textContent = `目前位置：${position}`;
    let map = new google.maps.Map(document.getElementById('map'), {
        zoom: 18,
        center: { lat: parking_data["station_latitude"], lng: parking_data["station_longitude"] },
    });

    let parking_lots = parking_data["parking_lots"];
    const bounds = new google.maps.LatLngBounds();
    let currentOpenInfoWindow = null;
    parking_lots.forEach(lot => {
        const position = { lat: lot["parking_lot_latitude"], lng: lot["parking_lot_longitude"] };
        const marker = new google.maps.Marker({
            position: position,
            map: map,
            title: lot["parking_lot_name"]
        });

        bounds.extend(position);

        const infoWindow = new google.maps.InfoWindow({
            content: createInfoWindowContent(lot["parking_lot_name"], position.lat, position.lng)
        });

        marker.addListener('click', () => {
            if (currentOpenInfoWindow) {
                currentOpenInfoWindow.close();
            }
            infoWindow.open(map, marker);
            currentOpenInfoWindow = infoWindow;
        });
    });

    map.fitBounds(bounds);

    google.maps.event.addListenerOnce(map, 'bounds_changed', function() {
        if (this.getZoom() > 16) {
            this.setZoom(16);
        }
    });
}

function createInfoWindowContent(title, lat, lng) {
    const div = document.createElement('div');
    div.className = 'map_info';
    div.innerHTML = `<h3>${title}</h3>`;
    
    const button = document.createElement('button');
    button.textContent = '導航';
    button.addEventListener('click', () => navigate(lat, lng, title));
    
    div.appendChild(button);
    return div;
}

function navigate(latitude, longitude, placeName) {
    const url = `https://www.google.com/maps/dir/?api=1&destination=${latitude},${longitude}&destination_place_id=${encodeURIComponent(placeName)}`;
    window.open(url, '_blank');
}