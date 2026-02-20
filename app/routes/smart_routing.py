import os
from datetime import datetime

import requests

from app.ml.stacked_predictor import predict_congestion

GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")


# ==============================
# HELPER: Infer Road Type
# ==============================

def infer_road_type(step):
    """
    Approximate road type from step data.
    Returns numeric encoding (0=local, 1=main, 2=highway).
    """

    name = step.get("html_instructions", "").lower()

    if "highway" in name or "expressway" in name:
        return 2  # highway
    elif "main" in name or "road" in name:
        return 1  # main road
    else:
        return 0  # local road


# ==============================
# ADJUST TIME USING ML
# ==============================

def adjusted_step_time(step):
    """
    Compute ML-adjusted travel time for one segment using the stacked model.
    Falls back gracefully if prediction fails.
    """

    # Raw values from Directions API
    distance_m = step.get("distance", {}).get("value")
    duration_s = step.get("duration", {}).get("value")

    if distance_m is None or duration_s is None:
        # If API response is malformed, be conservative
        return 0

    traffic_duration_s = step.get("duration_in_traffic", {}).get("value", duration_s)

    distance_km = distance_m / 1000.0

    # Avoid division by zero when computing speed
    if traffic_duration_s <= 0:
        avg_speed_kmh = 30.0
    else:
        avg_speed_kmh = (distance_km / (traffic_duration_s / 3600.0))

    road_type = infer_road_type(step)

    now = datetime.now()
    hour = now.hour
    is_weekend = 1 if now.weekday() >= 5 else 0

    try:
        congestion = predict_congestion(
            hour=hour,
            is_weekend=is_weekend,
            avg_speed=avg_speed_kmh,
            road_type=road_type,
            distance_km=distance_km,
        )
    except Exception:
        # Any ML failure should not break routing; assume moderate congestion
        congestion = 0.5

    adjusted_time = traffic_duration_s * (1.0 + float(congestion))

    return adjusted_time


# ==============================
# SCORE A ROUTE
# ==============================

def compute_route_eta(route):
    """
    Sum adjusted times for all segments.
    """

    total_time = 0.0

    for leg in route.get("legs", []):
        for step in leg.get("steps", []):
            total_time += adjusted_step_time(step)

    return total_time


# ==============================
# MAIN FUNCTION
# ==============================

def get_best_route(origin, destination):
    """
    Returns best route using ML-based ETA.

    Args:
        origin: Starting location (lat,lng string or tuple)
        destination: Destination location (lat,lng string or tuple)

    Returns:
        dict with 'route' and 'eta_seconds' keys, or None if route not found

    Raises:
        ValueError: If API key is not configured
    """

    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_MAPS_API_KEY environment variable not set")

    url = "https://maps.googleapis.com/maps/api/directions/json"

    params = {
        "origin": origin,
        "destination": destination,
        "alternatives": "true",
        "departure_time": "now",
        "traffic_model": "best_guess",
        "key": GOOGLE_API_KEY,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling Google Maps API: {e}")
        return None

    routes = data.get("routes", [])

    if not routes:
        return None

    best_route = None
    best_eta = float("inf")

    for route in routes:
        eta = compute_route_eta(route)

        if eta < best_eta:
            best_eta = eta
            best_route = route

    return {
        "route": best_route,
        "eta_seconds": best_eta,
    }
