# app/services/routing_engine.py

import requests
import datetime
from app.ml.stacked_predictor import predict_congestion


def compute_route(start, end, api_key):
    """
    Compute route using Google Directions API,
    then adjust travel time using stacked ML congestion prediction.
    """

    if not api_key:
        raise ValueError("Google Maps API key not configured.")

    url = "https://maps.googleapis.com/maps/api/directions/json"

    params = {
        "origin": f"{start['lat']},{start['lng']}",
        "destination": f"{end['lat']},{end['lng']}",
        "departure_time": "now",
        "traffic_model": "best_guess",
        "key": api_key,
    }

    response = requests.get(url, params=params)
    data = response.json()

    if data.get("status") != "OK":
        return None

    route = data["routes"][0]
    leg = route["legs"][0]

    encoded_polyline = route["overview_polyline"]["points"]

    # Static values from Google
    static_duration = leg["duration"]["value"]  # seconds
    static_distance_km = leg["distance"]["value"] / 1000  # km

    # Calculate average speed
    if static_duration > 0:
        avg_speed = static_distance_km / (static_duration / 3600)
    else:
        avg_speed = 30  # fallback

    # Time features
    now = datetime.datetime.now()
    hour = now.hour
    is_weekend = 1 if now.weekday() >= 5 else 0

    # Assume arterial road type for now
    road_type = 1

    # Predict congestion
    congestion_score = predict_congestion(
        hour=hour,
        is_weekend=is_weekend,
        avg_speed=avg_speed,
        road_type=road_type,
        distance_km=static_distance_km,
    )

    # Adjust time
    predictive_duration = static_duration * (1 + congestion_score)

    return {
        "encoded_polyline": encoded_polyline,
        "static_duration": static_duration,
        "predictive_duration": int(predictive_duration),
        "distance_km": round(static_distance_km, 2),
        "congestion_score": round(congestion_score, 3),
    }

def evaluate_congestion(start, end, api_key):
    """
    Evaluate predicted congestion between two points.
    Used to decide whether rerouting is required.
    """

    route_data = compute_route(start, end, api_key)

    if not route_data:
        return None

    return {
        "congestion_score": route_data["congestion_score"],
        "predictive_duration": route_data["predictive_duration"]
    }