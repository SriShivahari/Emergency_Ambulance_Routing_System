import pandas as pd
import numpy as np

np.random.seed(42)

records = []

for day in range(1, 31):  
    for hour in range(24):
        for _ in range(3):  
            is_weekend = 1 if day % 7 in [6, 0] else 0

            peak = 1 if (8 <= hour <= 10 or 17 <= hour <= 19) else 0

            road_type = np.random.choice([1, 2, 3])  

            if road_type == 1:
                base_speed = np.random.uniform(50, 70)
            elif road_type == 2:
                base_speed = np.random.uniform(30, 50)
            else:
                base_speed = np.random.uniform(15, 30)

            congestion = (
                1 - base_speed / 80
                + peak * 0.35
                + is_weekend * (-0.1)
                + np.random.normal(0, 0.05)
            )

            congestion = max(0, min(1, congestion))

            # Synthetic segment distance in kilometers
            # Assume realistic ambulance leg length between 0.5 km and 10 km
            distance_km = np.random.uniform(0.5, 10.0)

            records.append([
                hour,
                is_weekend,
                round(base_speed, 2),
                road_type,
                round(distance_km, 2),
                round(congestion, 3)
            ])

df = pd.DataFrame(
    records,
    columns=[
        "hour",
        "is_weekend",
        "avg_speed",
        "road_type",
        "distance_km",
        "congestion",
    ],
)

df.to_csv("app/ml/traffic_proxy_tomtom.csv", index=False)

print("Proxy TomTom-style dataset created with", len(df), "records")
