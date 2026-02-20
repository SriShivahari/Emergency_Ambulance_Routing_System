import csv
import math
import os
import polyline

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOSPITALS_PATH = os.path.join(
    BASE_DIR, "static", "assets", "hospitals_chennai.csv"
)

def load_hospitals():
    """Load hospital data from CSV file."""
    if not os.path.exists(HOSPITALS_PATH):
        raise FileNotFoundError(f"Hospitals CSV file not found at {HOSPITALS_PATH}")
    
    hospitals = []
    try:
        with open(HOSPITALS_PATH, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                hospitals.append({
                    "name": row["Hospital_Name"],
                    "lat": float(row["Latitude"]),
                    "lng": float(row["Longitude"])
                })
    except (KeyError, ValueError) as e:
        raise ValueError(f"Error parsing hospitals CSV: {e}")
    
    return hospitals

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate great-circle distance between two points on Earth."""
    R = 6371  # Earth's radius in kilometers
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def get_nearest_hospital(incident_lat, incident_lng):
    """Find the nearest hospital to an incident location."""
    hospitals = load_hospitals()

    if not hospitals:
        raise ValueError("No hospitals loaded from CSV")

    nearest = None
    min_dist = float("inf")

    for hospital in hospitals:
        dist = haversine_distance(
            incident_lat,
            incident_lng,
            hospital["lat"],
            hospital["lng"]
        )
        if dist < min_dist:
            min_dist = dist
            nearest = hospital

    return nearest

def decode_polyline(encoded_polyline):
    """Decode a Google Maps polyline."""
    decoded = polyline.decode(encoded_polyline)
    return [{"lat": lat, "lng": lng} for lat, lng in decoded]
