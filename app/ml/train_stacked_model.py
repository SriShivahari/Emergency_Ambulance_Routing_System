# app/ml/train_stacked_model.py

import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor


# ==============================
# PATHS & CONSTANTS
# ==============================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "traffic_proxy_tomtom.csv")
RF_PATH = os.path.join(BASE_DIR, "rf_model.pkl")
XGB_PATH = os.path.join(BASE_DIR, "xgb_model.pkl")
META_PATH = os.path.join(BASE_DIR, "meta_model.pkl")

# Feature order is critical – keep in sync with stacked_predictor.predict_congestion
FEATURE_COLS = ["hour", "is_weekend", "avg_speed", "road_type", "distance_km"]
TARGET_COL = "congestion"


# ==============================
# LOAD DATASET
# ==============================

if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(
        f"Dataset not found at {DATA_PATH}. "
        "Please run generate_proxy_dataset.py to create traffic_proxy_tomtom.csv."
    )

data = pd.read_csv(DATA_PATH)

missing = [c for c in FEATURE_COLS + [TARGET_COL] if c not in data.columns]
if missing:
    raise ValueError(
        f"Dataset at {DATA_PATH} is missing required columns: {missing}. "
        "Expected columns: " + ", ".join(FEATURE_COLS + [TARGET_COL])
    )

X = data[FEATURE_COLS]
y = data[TARGET_COL]  # scaled 0–1


# ==============================
# TRAIN TEST SPLIT
# ==============================

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)


# ==============================
# LEVEL 1 MODELS
# ==============================

rf = RandomForestRegressor(
    n_estimators=200,
    max_depth=12,
    random_state=42,
    n_jobs=-1,
)

xgb = XGBRegressor(
    n_estimators=300,
    learning_rate=0.05,
    max_depth=6,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
)

rf.fit(X_train, y_train)
xgb.fit(X_train, y_train)


# ==============================
# CREATE META FEATURES
# ==============================

rf_pred_train = rf.predict(X_train)
xgb_pred_train = xgb.predict(X_train)

meta_X_train = np.column_stack((rf_pred_train, xgb_pred_train))


# ==============================
# META MODEL
# ==============================

meta_model = LinearRegression()
meta_model.fit(meta_X_train, y_train)


# ==============================
# SAVE MODELS
# ==============================

joblib.dump(rf, RF_PATH)
joblib.dump(xgb, XGB_PATH)
joblib.dump(meta_model, META_PATH)

print(f"✅ Stacked models saved successfully to {BASE_DIR}")
