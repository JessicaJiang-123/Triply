import requests
from urllib.parse import quote
import configparser
import os

# Load API key from config.ini
config_path = os.path.join(os.path.dirname(__file__), '../../', 'config.ini')
config = configparser.ConfigParser()
config.read(config_path)

def get_coordinate_from_address(address):
    """
    Convert a physical address to geographic coordinates (latitude and longitude)
    using the OpenCage Geocoding API.
    """
    if not address:
        return None, None

    mapbox_api_key = config.get('Mapbox', 'API_KEY', fallback=None)
    if not mapbox_api_key:
        print("Mapbox API key not found in config.ini")
        return None, None

    encoded_address = quote(address)
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{encoded_address}.json?access_token={mapbox_api_key}"

    try:
        response = requests.get(
            url,
            timeout=5,
        )
        response.raise_for_status()

        data = response.json()
        features = data.get("features", [])

        if not features:
            return None, None

        coordinates = features[0].get("center", [])

        if len(coordinates) != 2:
            return None, None

        return float(coordinates[0]), float(coordinates[1])

    except requests.RequestException as e:
        print(f"Error fetching coordinates for {address}: {e}")
        return None, None
