from flask import Blueprint, jsonify, request

from app.ml.stacked_predictor import predict_congestion

ml_bp = Blueprint("ml", __name__)


@ml_bp.route("/ml/health", methods=["GET"])
def ml_health():
    return jsonify({"ml_service": "ready"})


@ml_bp.route("/ml/predict_congestion", methods=["POST"])
def ml_predict_congestion():
    """
    Predict traffic congestion using the stacked ML model.

    Expects JSON payload with:
        hour: 0–23
        is_weekend: 0 or 1
        avg_speed: km/h
        road_type: integer encoding
        distance_km: segment length in kilometers
    """

    data = request.get_json(silent=True) or {}

    required_fields = ["hour", "is_weekend", "avg_speed", "road_type", "distance_km"]
    missing = [f for f in required_fields if f not in data]
    if missing:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Missing required fields: {', '.join(missing)}",
                }
            ),
            400,
        )

    try:
        hour = int(data["hour"])
        is_weekend = int(data["is_weekend"])
        avg_speed = float(data["avg_speed"])
        road_type = int(data["road_type"])
        distance_km = float(data["distance_km"])
    except (TypeError, ValueError):
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Invalid data types; ensure numeric values for all fields.",
                }
            ),
            400,
        )

    if not (0 <= hour <= 23):
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "hour must be between 0 and 23.",
                }
            ),
            400,
        )

    if is_weekend not in (0, 1):
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "is_weekend must be 0 or 1.",
                }
            ),
            400,
        )

    if distance_km <= 0:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "distance_km must be positive.",
                }
            ),
            400,
        )

    try:
        score = predict_congestion(
            hour=hour,
            is_weekend=is_weekend,
            avg_speed=avg_speed,
            road_type=road_type,
            distance_km=distance_km,
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Failed to compute congestion: {e}",
                }
            ),
            500,
        )

    return jsonify(
        {
            "status": "ok",
            "congestion": float(score),
        }
    )