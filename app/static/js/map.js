let map;
let incidentMarker = null;
let hospitalMarker = null;
let ambulanceMarker = null;
let incidentLatLng = null;
let routePolyline = null;
let routePath = [];
let selectionMode = "address";
let searchBoxInstance = null;
let routeInfoDiv = null;

let trackingInterval = null;
let rerouteInterval = null;

let routeIndex = 0;

let congestionThreshold = 0.45;

const DEFAULT_CENTER = { lat: 13.0814, lng: 80.2200 };

function initMap() {

    map = new google.maps.Map(document.getElementById("map"), {
        center: DEFAULT_CENTER,
        zoom: 12
    });

    routeInfoDiv = document.createElement("div");
    routeInfoDiv.style.background = "rgba(255,255,255,0.95)";
    routeInfoDiv.style.padding = "12px 16px";
    routeInfoDiv.style.borderRadius = "12px";
    routeInfoDiv.style.boxShadow = "0 6px 18px rgba(0,0,0,0.2)";
    routeInfoDiv.style.fontSize = "14px";
    routeInfoDiv.style.margin = "16px";
    routeInfoDiv.style.minWidth = "230px";
    routeInfoDiv.style.transition = "all 0.3s ease";
    routeInfoDiv.style.borderLeft = "5px solid #d32f2f";
    routeInfoDiv.style.display = "none";
    routeInfoDiv.innerHTML = "";

    map.controls[google.maps.ControlPosition.BOTTOM_LEFT].push(routeInfoDiv);

    setupControls();
    setupAddressSearch();

    map.addListener("click", (event) => {
        if (selectionMode === "map") {
            setIncidentLocation(event.latLng);
        }
    });
}

function setupControls() {

    const addressBtn = document.getElementById("addressMode");
    const mapBtn = document.getElementById("mapMode");
    const searchInput = document.getElementById("searchBox");

    addressBtn.onclick = () => {
        selectionMode = "address";
        addressBtn.classList.add("active");
        mapBtn.classList.remove("active");
        searchInput.style.visibility = "visible";
    };

    mapBtn.onclick = () => {
        selectionMode = "map";
        mapBtn.classList.add("active");
        addressBtn.classList.remove("active");
        searchInput.style.visibility = "hidden";
    };

    document.getElementById("startBtn").onclick = startRouting;
    document.getElementById("liveTrackBtn").onclick = startLiveTracking;
    document.getElementById("clearBtn").onclick = clearRoute;
}

function setupAddressSearch() {

    const input = document.getElementById("searchBox");

    searchBoxInstance = new google.maps.places.SearchBox(input);

    searchBoxInstance.addListener("places_changed", () => {

        if (selectionMode !== "address") return;

        const places = searchBoxInstance.getPlaces();

        if (!places || places.length === 0) return;

        setIncidentLocation(places[0].geometry.location);

    });
}

function setIncidentLocation(location) {

    incidentLatLng = location;

    if (incidentMarker) incidentMarker.setMap(null);

    incidentMarker = new google.maps.Marker({
        position: location,
        map: map,
        title: "Incident Location",
        icon: "http://maps.google.com/mapfiles/ms/icons/red-dot.png"
    });

    map.panTo(location);
    map.setZoom(15);
}

function startRouting() {

    if (!incidentLatLng) {
        alert("Please select an incident location");
        return;
    }

    fetch("/start", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            latitude: incidentLatLng.lat(),
            longitude: incidentLatLng.lng()
        })
    })
    .then(res => res.json())
    .then(data => {

        if (!data.path) {
            alert("Route not found");
            return;
        }

        routePath = data.path;

        if (routePolyline) routePolyline.setMap(null);

        routePolyline = new google.maps.Polyline({
            path: routePath,
            geodesic: true,
            strokeColor: "#d32f2f",
            strokeWeight: 5
        });

        routePolyline.setMap(map);

        if (hospitalMarker) hospitalMarker.setMap(null);

        hospitalMarker = new google.maps.Marker({
            position: routePath[0],
            map: map,
            title: "Nearest Hospital",
            icon: "http://maps.google.com/mapfiles/ms/icons/blue-dot.png"
        });

        routeInfoDiv.style.display = "block";

        const staticMinutes = Math.round(data.static_time_sec / 60);
        const predictiveMinutes = Math.round(data.predictive_time_sec / 60);
        const timeDiff = predictiveMinutes - staticMinutes;

        let diffColor = timeDiff > 0 ? "#d32f2f" : "#2e7d32";

        routeInfoDiv.innerHTML = `
            <div style="font-weight:600; margin-bottom:6px;">Route Intelligence</div>
            <div><b>Distance:</b> ${data.distance_km} km</div>
            <div><b>Static ETA:</b> ${staticMinutes} mins</div>
            <div><b>Predictive ETA:</b> ${predictiveMinutes} mins</div>
            <div style="color:${diffColor};"><b>Time Impact:</b> ${timeDiff} mins</div>
            <div><b>Congestion Score:</b> ${data.congestion_score}</div>
        `;

    })
    .catch(err => {
        console.error("Routing error:", err);
    });
}

function startLiveTracking() {

    if (!routePath.length) {
        alert("Please generate a route first");
        return;
    }

    if (trackingInterval) clearInterval(trackingInterval);

    routeIndex = 0;

    if (ambulanceMarker) ambulanceMarker.setMap(null);

    ambulanceMarker = new google.maps.Marker({
        position: routePath[0],
        map: map,
        title: "Ambulance",
        icon: "http://maps.google.com/mapfiles/ms/icons/green-dot.png"
    });

    // Check if the browser supports geolocation
    if (!navigator.geolocation) {
        alert("Geolocation is not supported by your browser");
        return;
    }

    // Function to handle geolocation success
    function success(position) {

        const currentPos = {
            lat: position.coords.latitude,
            lng: position.coords.longitude
        };

        ambulanceMarker.setPosition(currentPos);
        map.panTo(currentPos);
    }

    // Function to handle geolocation errors
    function error() {
        alert("Unable to retrieve your location");
    }

    if (trackingInterval) clearInterval(trackingInterval);

    routeIndex = 0;

    trackingInterval = setInterval(() => {

        routeIndex++;

        if (routeIndex >= routePath.length) {
            clearInterval(trackingInterval);
            return;
        }

        navigator.geolocation.getCurrentPosition(success, error);

    }, 2000);

    // START AUTO REROUTE MONITOR
    startAutoRerouting();

    // Request the user's location
    navigator.geolocation.getCurrentPosition(success, error);
}

function startAutoRerouting() {

    if (rerouteInterval) clearInterval(rerouteInterval);

    rerouteInterval = setInterval(() => {

        if (!ambulanceMarker || !incidentLatLng) return;

        const currentPos = ambulanceMarker.getPosition();

        fetch("/reroute", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                start: {
                    lat: currentPos.lat(),
                    lng: currentPos.lng()
                },
                end: {
                    lat: incidentLatLng.lat(),
                    lng: incidentLatLng.lng()
                }
            })
        })
        .then(res => res.json())
        .then(data => {

            if (!data.path) return;

            if (data.congestion_score < congestionThreshold) return;

            console.log("⚠ Congestion detected → Rerouting");

            routePath = data.path;

            if (routePolyline) routePolyline.setMap(null);

            routePolyline = new google.maps.Polyline({
                path: routePath,
                geodesic: true,
                strokeColor: "#ff0000",
                strokeWeight: 5
            });

            routePolyline.setMap(map);

        });

    }, 8000);
}

function clearRoute() {

    if (trackingInterval) {
        clearInterval(trackingInterval);
        trackingInterval = null;
    }

    if (rerouteInterval) {
        clearInterval(rerouteInterval);
        rerouteInterval = null;
    }

    if (routePolyline) {
        routePolyline.setMap(null);
        routePolyline = null;
    }

    if (incidentMarker) {
        incidentMarker.setMap(null);
        incidentMarker = null;
    }

    if (hospitalMarker) {
        hospitalMarker.setMap(null);
        hospitalMarker = null;
    }

    if (ambulanceMarker) {
        ambulanceMarker.setMap(null);
        ambulanceMarker = null;
    }

    routePath = [];
    incidentLatLng = null;
    routeIndex = 0;

    if (routeInfoDiv) {
        routeInfoDiv.style.display = "none";
        routeInfoDiv.innerHTML = "";
    }

    map.setCenter(DEFAULT_CENTER);
    map.setZoom(12);
}