
import os
import warnings

import joblib
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RF_PATH = os.path.join(BASE_DIR, "rf_model.pkl")
XGB_PATH = os.path.join(BASE_DIR, "xgb_model.pkl")
META_PATH = os.path.join(BASE_DIR, "meta_model.pkl")

FEATURE_COLS = ["hour", "is_weekend", "avg_speed", "road_type", "distance_km"]

rf = None
xgb = None
meta = None
_warned_missing_models = False


def _load_models():
    """Internal helper to load models lazily."""
    global rf, xgb, meta, _warned_missing_models

    if rf is not None and xgb is not None and meta is not None:
        return

    try:
        rf_local = joblib.load(RF_PATH)
        xgb_local = joblib.load(XGB_PATH)
        meta_local = joblib.load(META_PATH)
    except FileNotFoundError as e:
        if not _warned_missing_models:
            warnings.warn(
                f"Stacked models not found: {e}. "
                "Run app/ml/train_stacked_model.py to train and save models. "
                "Falling back to heuristic congestion estimate.",
                RuntimeWarning,
            )
            _warned_missing_models = True
        rf_local = None
        xgb_local = None
        meta_local = None

    rf, xgb, meta = rf_local, xgb_local, meta_local


def _heuristic_congestion(avg_speed, road_type):
    """
    Simple, safe fallback if models are missing.
    Uses speed-based congestion with a small road-type adjustment.
    """

    if avg_speed is None or avg_speed <= 0:
        base = 0.6
    else:
        base = 1.0 - (avg_speed / 80.0)

    # Road-type adjustment: highways slightly less congested
    if road_type == 2:
        base -= 0.1
    elif road_type == 0:
        base += 0.05

    return float(max(0.0, min(1.0, base)))


def predict_congestion(hour, is_weekend, avg_speed, road_type, distance_km):
    """
    Hybrid congestion prediction using stacked RF + XGBoost + meta-model.

    All numeric features correspond to the synthetic dataset schema:
        - hour: 0–23 (int)
        - is_weekend: 0 (weekday) or 1 (weekend)
        - avg_speed: km/h
        - road_type: categorical encoding (e.g. 0 local, 1 main, 2 highway)
        - distance_km: segment distance in kilometers

    Returns:
        Congestion score between 0.0 and 1.0.
    """

    try:
        features = np.array(
            [
                [
                    int(hour),
                    int(is_weekend),
                    float(avg_speed),
                    int(road_type),
                    float(distance_km),
                ]
            ],
            dtype=float,
        )
    except (TypeError, ValueError) as e:
        raise ValueError(f"Invalid feature values for congestion prediction: {e}") from e

    _load_models()

    if rf is None or xgb is None or meta is None:
        return _heuristic_congestion(features[0, 2], int(features[0, 3]))

    rf_pred = rf.predict(features)
    xgb_pred = xgb.predict(features)
    meta_input = np.column_stack((rf_pred, xgb_pred))
    final_pred = float(meta.predict(meta_input)[0])
    return max(0.0, min(1.0, final_pred))

