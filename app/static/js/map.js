let map;
let incidentMarker = null;
let hospitalMarker = null;
let ambulanceMarker = null;
let incidentLatLng = null;
let routePolyline = null;
let routePath = [];
let selectionMode = "address";
let searchBoxInstance = null;
let trackingInterval = null;
let routeIndex = 0;

const DEFAULT_CENTER = { lat: 13.0814, lng: 80.2200 };

function initMap() {
    map = new google.maps.Map(document.getElementById("map"), {
        center: DEFAULT_CENTER,
        zoom: 12
    });

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
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            latitude: incidentLatLng.lat(),
            longitude: incidentLatLng.lng()
        })
    })
    .then(res => res.json())
    .then(data => {
        // #region agent log
        fetch('http://127.0.0.1:7242/ingest/6c02d037-1a11-4dc9-84cb-d53f9aa46451',{
          method:'POST',
          headers:{'Content-Type':'application/json'},
          body:JSON.stringify({
            id:'log_'+Date.now()+'_startRouting_response',
            timestamp:Date.now(),
            location:'app/static/js/map.js:startRouting',
            message:'/start response payload',
            data:{status:data.status, message:data.message, hasPath:!!data.path},
            runId:'run1',
            hypothesisId:'H4'
          })
        }).catch(()=>{});
        // #endregion

        if (!data.path) return;

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
    })
    .catch(err => {
        // #region agent log
        fetch('http://127.0.0.1:7242/ingest/6c02d037-1a11-4dc9-84cb-d53f9aa46451',{
          method:'POST',
          headers:{'Content-Type':'application/json'},
          body:JSON.stringify({
            id:'log_'+Date.now()+'_startRouting_fetch_error',
            timestamp:Date.now(),
            location:'app/static/js/map.js:startRouting',
            message:'fetch /start failed',
            data:{error:String(err)},
            runId:'run1',
            hypothesisId:'H5'
          })
        }).catch(()=>{});
        // #endregion
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
        title: "Ambulance (Live)",
        icon: "http://maps.google.com/mapfiles/ms/icons/green-dot.png"
    });

    trackingInterval = setInterval(() => {
        routeIndex++;

        if (routeIndex >= routePath.length) {
            clearInterval(trackingInterval);
            return;
        }

        ambulanceMarker.setPosition(routePath[routeIndex]);
        map.panTo(routePath[routeIndex]);

    }, 1500); // moves every 1.5 seconds
}

function clearRoute() {
    if (trackingInterval) clearInterval(trackingInterval);

    if (routePolyline) routePolyline.setMap(null);
    if (incidentMarker) incidentMarker.setMap(null);
    if (hospitalMarker) hospitalMarker.setMap(null);
    if (ambulanceMarker) ambulanceMarker.setMap(null);

    routePolyline = null;
    incidentMarker = null;
    hospitalMarker = null;
    ambulanceMarker = null;
    routePath = [];
    incidentLatLng = null;

    map.setCenter(DEFAULT_CENTER);
    map.setZoom(12);
}
