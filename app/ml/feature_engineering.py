def build_features(df):

    df["peak_hour"] = df["hour"].apply(
        lambda x: 1 if (8 <= x <= 10 or 17 <= x <= 19) else 0
    )

    df["speed_ratio"] = df["avg_speed"] / 60.0

    return df[[
        "hour",
        "is_weekend",
        "avg_speed",
        "road_type",
        "peak_hour",
        "speed_ratio"
    ]]
