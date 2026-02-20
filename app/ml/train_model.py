import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from joblib import dump

from app.ml.feature_engineering import build_features

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_PATH = os.path.join(BASE_DIR, "traffic_proxy_tomtom.csv")

RF_PATH = os.path.join(BASE_DIR, "rf_model.pkl")
XGB_PATH = os.path.join(BASE_DIR, "xgb_model.pkl")

df = pd.read_csv(DATA_PATH)

X = build_features(df)
y = df["congestion"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# ---------------- Random Forest ----------------

rf = RandomForestRegressor(
    n_estimators=200,
    max_depth=12,
    random_state=42
)

rf.fit(X_train, y_train)

rf_pred = rf.predict(X_test)

rf_mae = mean_absolute_error(y_test, rf_pred)
rf_rmse = mean_squared_error(y_test, rf_pred) ** 0.5
rf_r2 = r2_score(y_test, rf_pred)

dump(rf, RF_PATH)

# ---------------- XGBoost ----------------

xgb = XGBRegressor(
    n_estimators=300,
    learning_rate=0.07,
    max_depth=6,
    subsample=0.85,
    colsample_bytree=0.85,
    random_state=42
)

xgb.fit(X_train, y_train)

xgb_pred = xgb.predict(X_test)

xgb_mae = mean_absolute_error(y_test, xgb_pred)
xgb_rmse = mean_squared_error(y_test, xgb_pred) ** 0.5
xgb_r2 = r2_score(y_test, xgb_pred)

dump(xgb, XGB_PATH)

# ---------------- Results ----------------

print("\n======= MODEL COMPARISON =======")

print("\nRandom Forest")
print("MAE :", round(rf_mae,4))
print("RMSE:", round(rf_rmse,4))
print("R2  :", round(rf_r2,4))

print("\nXGBoost")
print("MAE :", round(xgb_mae,4))
print("RMSE:", round(xgb_rmse,4))
print("R2  :", round(xgb_r2,4))

print("\nModels saved successfully.")
