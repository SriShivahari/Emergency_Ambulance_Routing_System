# app/ml/train_stacked_model.py

import os
import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split, KFold
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "traffic_proxy_tomtom.csv")

RF_PATH = os.path.join(BASE_DIR, "rf_model.pkl")
XGB_PATH = os.path.join(BASE_DIR, "xgb_model.pkl")
META_PATH = os.path.join(BASE_DIR, "meta_model.pkl")

FEATURE_COLS = ["hour", "is_weekend", "avg_speed", "road_type", "distance_km"]
TARGET_COL = "congestion"

data = pd.read_csv(DATA_PATH)

X = data[FEATURE_COLS]
y = data[TARGET_COL]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# -----------------------
# Base Models
# -----------------------

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


kf = KFold(n_splits=5, shuffle=True, random_state=42)
meta_features = np.zeros((X_train.shape[0], 2))

for train_idx, val_idx in kf.split(X_train):
    X_t, X_val = X_train.iloc[train_idx], X_train.iloc[val_idx]
    y_t = y_train.iloc[train_idx]

    rf_temp = RandomForestRegressor(n_estimators=200, max_depth=12, random_state=42)
    xgb_temp = XGBRegressor(n_estimators=300, learning_rate=0.05, max_depth=6)

    rf_temp.fit(X_t, y_t)
    xgb_temp.fit(X_t, y_t)

    meta_features[val_idx, 0] = rf_temp.predict(X_val)
    meta_features[val_idx, 1] = xgb_temp.predict(X_val)

meta_model = LinearRegression()
meta_model.fit(meta_features, y_train)

rf.fit(X_train, y_train)
xgb.fit(X_train, y_train)

# -----------------------
# Evaluation
# -----------------------

rf_test = rf.predict(X_test)
xgb_test = xgb.predict(X_test)

meta_test_input = np.column_stack((rf_test, xgb_test))
stacked_pred = meta_model.predict(meta_test_input)

print("\n===== MODEL PERFORMANCE =====")

print("\nRandom Forest:")
print("MAE :", mean_absolute_error(y_test, rf_test))
print("RMSE:", mean_squared_error(y_test, rf_test) ** 0.5)
print("R2  :", r2_score(y_test, rf_test))

print("\nXGBoost:")
print("MAE :", mean_absolute_error(y_test, xgb_test))
print("RMSE:", mean_squared_error(y_test, xgb_test) ** 0.5)
print("R2  :", r2_score(y_test, xgb_test))

print("\nStacked Model:")
print("MAE :", mean_absolute_error(y_test, stacked_pred))
print("RMSE:", mean_squared_error(y_test, stacked_pred) ** 0.5)
print("R2  :", r2_score(y_test, stacked_pred))

# Save models
joblib.dump(rf, RF_PATH)
joblib.dump(xgb, XGB_PATH)
joblib.dump(meta_model, META_PATH)

print("\n✅ Stacked models saved successfully.")