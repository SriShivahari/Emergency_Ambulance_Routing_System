import requests

def compute_route(start, end, api_key):
    """
    Compute route between two points using Google Maps API.
    
    Args:
        start: dict with 'lat' and 'lng' keys
        end: dict with 'lat' and 'lng' keys
        api_key: Google Maps API key
    
    Returns:
        Encoded polyline string if successful, None otherwise
    """
    
    if not api_key:
        raise ValueError("API key is required")
    
    url = "https://maps.googleapis.com/maps/api/directions/json"

    params = {
        "origin": f"{start['lat']},{start['lng']}",
        "destination": f"{end['lat']},{end['lng']}",
        "mode": "driving",
        "alternatives": "false",
        "key": api_key
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling Google Maps API: {e}")
        return None

    if "routes" not in data or len(data["routes"]) == 0:
        return None

    return data["routes"][0]["overview_polyline"]["points"]
