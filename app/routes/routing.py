from flask import Blueprint, current_app, jsonify, render_template, request

from app.services.map_utils import decode_polyline, get_nearest_hospital
from app.services.routing_engine import compute_route

routing_bp = Blueprint("routing", __name__)


@routing_bp.route("/health", methods=["GET"])
def health():
    return jsonify(
        {
            "status": "OK",
            "service": "Ambulance Routing Backend",
        }
    )


@routing_bp.route("/", methods=["GET"])
def dashboard():
    return render_template(
        "dashboard.html",
        google_maps_key=current_app.config.get("GOOGLE_MAPS_API_KEY", ""),
    )


@routing_bp.route("/start", methods=["POST"])
def start_routing():
    """
    Compute predictive optimized route from nearest hospital
    to selected incident location.
    """

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Request body must be valid JSON.",
                }
            ),
            400,
        )

    incident_lat = data.get("latitude")
    incident_lng = data.get("longitude")

    try:
        incident_lat = float(incident_lat)
        incident_lng = float(incident_lng)
    except (TypeError, ValueError):
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "latitude and longitude must be numeric.",
                }
            ),
            400,
        )

    try:
        nearest_hospital = get_nearest_hospital(incident_lat, incident_lng)
    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Failed to load hospital data: {e}",
                }
            ),
            500,
        )

    if not nearest_hospital:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "No hospitals available.",
                }
            ),
            500,
        )

    start = {
        "lat": nearest_hospital["lat"],
        "lng": nearest_hospital["lng"],
    }

    end = {
        "lat": incident_lat,
        "lng": incident_lng,
    }

    try:
        route_data = compute_route(
            start,
            end,
            current_app.config.get("GOOGLE_MAPS_API_KEY", ""),
        )
    except ValueError as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": str(e),
                }
            ),
            500,
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Failed to compute route: {e}",
                }
            ),
            500,
        )

    if not route_data:
        return (
            jsonify(
                {
                    "status": "route_not_found",
                    "message": "No route could be found for the given locations.",
                }
            ),
            502,
        )

    try:
        path = decode_polyline(route_data["encoded_polyline"])
    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Failed to decode route polyline: {e}",
                }
            ),
            500,
        )

    return jsonify(
        {
            "status": "route_generated",
            "hospital": nearest_hospital["name"],
            "path": path,
            "static_time_sec": route_data["static_duration"],
            "predictive_time_sec": route_data["predictive_duration"],
            "distance_km": route_data["distance_km"],
            "congestion_score": route_data["congestion_score"],
        }
    )

@routing_bp.route("/reroute", methods=["POST"])
def reroute():

    data = request.get_json()

    if not data:
        return jsonify({"status": "error"}), 400

    start = data.get("start")
    end = data.get("end")

    if not start or not end:
        return jsonify({"status": "error"}), 400

    try:
        route_data = compute_route(
            start,
            end,
            current_app.config.get("GOOGLE_MAPS_API_KEY", "")
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    if not route_data:
        return jsonify({"status": "no_route"}), 500

    path = decode_polyline(route_data["encoded_polyline"])

    return jsonify({
        "status": "rerouted",
        "path": path,
        "predictive_time_sec": route_data["predictive_duration"],
        "congestion_score": route_data["congestion_score"]
    })