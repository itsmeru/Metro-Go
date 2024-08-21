document.addEventListener('DOMContentLoaded', (event) => {
 
    const parkingButton = document.getElementById('ParkingButton');
    const modal = document.getElementById('parkingModal');
    const closeButton = document.querySelector('.close-button');
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

        
    const buttons = document.querySelectorAll('.map-overlay button');
    
    // Set the first button as active by default
    buttons[0].classList.add('active');

    buttons.forEach(button => {
        button.addEventListener('click', function() {
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


function initMap() {
    let map = new google.maps.Map(document.getElementById('map'), {
        zoom: 18,
        center: { lat: 25.02373600, lng: 121.46836300 },
    });

    const markers = [
        {
            position: { lat: 25.02587920, lng: 121.47090680 },
            title: "文化路二段124巷停車場",
            address: "220台灣新北市板橋區文化路二段124巷"
        },
        { lat: 25.02552670, lng: 121.46660100 }
    ];

    const bounds = new google.maps.LatLngBounds();

    markers.forEach(markerInfo => {
        const position = markerInfo.position || markerInfo;
        const marker = new google.maps.Marker({
            position: position,
            map: map,
            title: markerInfo.title || ''
        });

        bounds.extend(position);

        if (markerInfo.title) {
            const infoWindow = new google.maps.InfoWindow({
                content: `
                    <div class="map_info">
                        <h3>${markerInfo.title}</h3>
                        <button onclick="navigate('${markerInfo.address}')">導航</button>
                    </div>
                `
            });

            marker.addListener('click', () => {
                infoWindow.open(map, marker);
            });
        }
    });

    map.fitBounds(bounds);

    google.maps.event.addListenerOnce(map, 'bounds_changed', function() {
        if (this.getZoom() > 16) {
            this.setZoom(16);
        }
    });
}

function navigate(address) {
    const url = `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(address)}`;
    window.open(url, '_blank');
}