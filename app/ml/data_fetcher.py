import os
import requests
import pandas as pd
import datetime

TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY", "")

# Chennai sample bounding box
LAT = 13.0827
LON = 80.2707

def fetch_tomtom_data():

    url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"

    params = {
        "point": f"{LAT},{LON}",
        "key": TOMTOM_API_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()

    flow = data["flowSegmentData"]

    speed = flow["currentSpeed"]
    free_speed = flow["freeFlowSpeed"]

    congestion = 1 - (speed / free_speed)

    now = datetime.datetime.now()

    df = pd.DataFrame([{
        "hour": now.hour,
        "is_weekend": 1 if now.weekday() >= 5 else 0,
        "avg_speed": speed,
        "road_type": 2,   # arterial assumed
        "congestion": congestion
    }])

    return df
