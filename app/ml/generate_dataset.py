import pandas as pd
import numpy as np

np.random.seed(42)
records = []

for hour in range(24):
    for is_weekend in [0, 1]:
        for road_type in [1, 2, 3]:
            for _ in range(2):  # 24*2*3*2 = 288 → we'll trim later
                if road_type == 1:
                    base_speed = np.random.uniform(50, 70)
                elif road_type == 2:
                    base_speed = np.random.uniform(30, 50)
                else:
                    base_speed = np.random.uniform(15, 30)

                peak = 1 if (8 <= hour <= 10 or 17 <= hour <= 19) else 0
                weekend_factor = -0.1 if is_weekend else 0

                congestion = (
                    1 - (base_speed / 80)
                    + peak * 0.3
                    + weekend_factor
                    + np.random.normal(0, 0.05)
                )
                congestion = max(0, min(1, congestion))
                distance_km = np.random.uniform(0.5, 8.0)

                records.append([
                    hour,
                    is_weekend,
                    round(base_speed, 1),
                    road_type,
                    round(distance_km, 2),
                    round(congestion, 2)
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
df = df.sample(n=120, random_state=42).reset_index(drop=True)
df.to_csv("traffic_dataset.csv", index=False)
print("Dataset generated: traffic_dataset.csv (120 records)")
