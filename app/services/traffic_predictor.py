from app.ml.stacked_predictor import predict_congestion

# Re-export the function from stacked_predictor.
# Signature:
#   predict_congestion(hour, is_weekend, avg_speed, road_type, distance_km)
# All parameters are required for accurate ML prediction.
