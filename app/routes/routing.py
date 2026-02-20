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
    Compute a route from the nearest hospital to the incident location.

    Expects JSON with:
        latitude: float
        longitude: float
    """

    # region agent log
    import json as _json  # type: ignore
    from time import time as _time  # type: ignore

    try:
        _payload = {
            "id": f"log_{int(_time()*1000)}_start_entry",
            "timestamp": int(_time() * 1000),
            "location": "app/routes/routing.py:start_routing:entry",
            "message": "start_routing called",
            "data": {},
            "runId": "run1",
            "hypothesisId": "H1",
        }
        with open(
            r"c:\Users\admin\Desktop\Iternation 2\ambulance-routing-system-main\.cursor\debug.log",
            "a",
            encoding="utf-8",
        ) as _f:
            _f.write(_json.dumps(_payload) + "\n")
    except Exception:
        # Debug logging must never break the app
        pass
    # endregion

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

    # region agent log
    try:
        _payload = {
            "id": f"log_{int(_time()*1000)}_coords",
            "timestamp": int(_time() * 1000),
            "location": "app/routes/routing.py:start_routing:coords",
            "message": "Validated incident coordinates",
            "data": {"lat": incident_lat, "lng": incident_lng},
            "runId": "run1",
            "hypothesisId": "H2",
        }
        with open(
            r"c:\Users\admin\Desktop\Iternation 2\ambulance-routing-system-main\.cursor\debug.log",
            "a",
            encoding="utf-8",
        ) as _f:
            _f.write(_json.dumps(_payload) + "\n")
    except Exception:
        pass
    # endregion

    try:
        nearest_hospital = get_nearest_hospital(incident_lat, incident_lng)
    except FileNotFoundError as e:
        # region agent log
        try:
            _payload = {
                "id": f"log_{int(_time()*1000)}_hospital_file_error",
                "timestamp": int(_time() * 1000),
                "location": "app/routes/routing.py:start_routing:hospital_error",
                "message": "Hospital CSV missing or unreadable",
                "data": {"error": str(e)},
                "runId": "run1",
                "hypothesisId": "H2",
            }
            with open(
                r"c:\Users\admin\Desktop\Iternation 2\ambulance-routing-system-main\.cursor\debug.log",
                "a",
                encoding="utf-8",
            ) as _f:
                _f.write(_json.dumps(_payload) + "\n")
        except Exception:
            pass
        # endregion
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
        # region agent log
        try:
            _payload = {
                "id": f"log_{int(_time()*1000)}_hospital_generic_error",
                "timestamp": int(_time() * 1000),
                "location": "app/routes/routing.py:start_routing:hospital_error_generic",
                "message": "Failed to load hospital data",
                "data": {"error": str(e)},
                "runId": "run1",
                "hypothesisId": "H2",
            }
            with open(
                r"c:\Users\admin\Desktop\Iternation 2\ambulance-routing-system-main\.cursor\debug.log",
                "a",
                encoding="utf-8",
            ) as _f:
                _f.write(_json.dumps(_payload) + "\n")
        except Exception:
            pass
        # endregion
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
        encoded_route = compute_route(
            start,
            end,
            current_app.config.get("GOOGLE_MAPS_API_KEY", ""),
        )
    except ValueError as e:
        # Typically missing API key
        # region agent log
        try:
            _payload = {
                "id": f"log_{int(_time()*1000)}_api_value_error",
                "timestamp": int(_time() * 1000),
                "location": "app/routes/routing.py:start_routing:api_value_error",
                "message": "compute_route raised ValueError",
                "data": {"error": str(e)},
                "runId": "run1",
                "hypothesisId": "H3",
            }
            with open(
                r"c:\Users\admin\Desktop\Iternation 2\ambulance-routing-system-main\.cursor\debug.log",
                "a",
                encoding="utf-8",
            ) as _f:
                _f.write(_json.dumps(_payload) + "\n")
        except Exception:
            pass
        # endregion
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
        # region agent log
        try:
            _payload = {
                "id": f"log_{int(_time()*1000)}_api_generic_error",
                "timestamp": int(_time() * 1000),
                "location": "app/routes/routing.py:start_routing:api_generic_error",
                "message": "compute_route raised unexpected exception",
                "data": {"error": str(e)},
                "runId": "run1",
                "hypothesisId": "H3",
            }
            with open(
                r"c:\Users\admin\Desktop\Iternation 2\ambulance-routing-system-main\.cursor\debug.log",
                "a",
                encoding="utf-8",
            ) as _f:
                _f.write(_json.dumps(_payload) + "\n")
        except Exception:
            pass
        # endregion
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Failed to compute route: {e}",
                }
            ),
            500,
        )

    if not encoded_route:
        # region agent log
        try:
            _payload = {
                "id": f"log_{int(_time()*1000)}_route_not_found",
                "timestamp": int(_time() * 1000),
                "location": "app/routes/routing.py:start_routing:route_not_found",
                "message": "compute_route returned no route",
                "data": {},
                "runId": "run1",
                "hypothesisId": "H3",
            }
            with open(
                r"c:\Users\admin\Desktop\Iternation 2\ambulance-routing-system-main\.cursor\debug.log",
                "a",
                encoding="utf-8",
            ) as _f:
                _f.write(_json.dumps(_payload) + "\n")
        except Exception:
            pass
        # endregion
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
        path = decode_polyline(encoded_route)
    except Exception as e:
        # region agent log
        try:
            _payload = {
                "id": f"log_{int(_time()*1000)}_polyline_error",
                "timestamp": int(_time() * 1000),
                "location": "app/routes/routing.py:start_routing:polyline_error",
                "message": "Failed to decode polyline",
                "data": {"error": str(e)},
                "runId": "run1",
                "hypothesisId": "H3",
            }
            with open(
                r"c:\Users\admin\Desktop\Iternation 2\ambulance-routing-system-main\.cursor\debug.log",
                "a",
                encoding="utf-8",
            ) as _f:
                _f.write(_json.dumps(_payload) + "\n")
        except Exception:
            pass
        # endregion
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Failed to decode route polyline: {e}",
                }
            ),
            500,
        )

    # region agent log
    try:
        _payload = {
            "id": f"log_{int(_time()*1000)}_route_success",
            "timestamp": int(_time() * 1000),
            "location": "app/routes/routing.py:start_routing:success",
            "message": "Successfully generated route",
            "data": {"hospital": nearest_hospital["name"], "path_len": len(path)},
            "runId": "run1",
            "hypothesisId": "H1",
        }
        with open(
            r"c:\Users\admin\Desktop\Iternation 2\ambulance-routing-system-main\.cursor\debug.log",
            "a",
            encoding="utf-8",
        ) as _f:
            _f.write(_json.dumps(_payload) + "\n")
    except Exception:
        pass
    # endregion

    return jsonify(
        {
            "status": "route_generated",
            "hospital": nearest_hospital["name"],
            "path": path,
        }
    )
