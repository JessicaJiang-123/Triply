import requests
from urllib.parse import quote
import configparser
import os

# Load API key from config.ini
config_path = os.path.join(os.path.dirname(__file__), '../../', 'config.ini')
config = configparser.ConfigParser()
config.read(config_path)

def fetch_route_between_points(from_coords, to_coords):
    """
    Calls the Mapbox Directions API to fetch route info between two coordinates.
    Returns dict with coordinates, duration, and distance.
    """
    if not from_coords or not to_coords:
        return None

    mapbox_api_key = config.get('Mapbox', 'API_KEY', fallback=None)
    if not mapbox_api_key:
        print("Mapbox API key not found in config.ini")
        return None

    url = (
        f"https://api.mapbox.com/directions/v5/mapbox/driving/"
        f"{from_coords[0]},{from_coords[1]};{to_coords[0]},{to_coords[1]}"
    )

    params = {
        "geometries": "geojson",
        "access_token": mapbox_api_key,
    }

    try:
        response = requests.get(url, params=params, timeout=8)
        response.raise_for_status()

        data = response.json()
        if not data.get("routes"):
            return None

        route = data["routes"][0]
        return {
            "coordinates": route["geometry"]["coordinates"],
            "duration": route["duration"],  # seconds
            "distance": route["distance"],  # meters
        }
    
    except requests.RequestException as e:
        print(f"Error fetching route between points {from_coords} and {to_coords}: {e}")
        return None
