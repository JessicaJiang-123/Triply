import requests
from urllib.parse import quote
import configparser
import os

# Load API key from config.ini
config_path = os.path.join(os.path.dirname(__file__), '../../', 'config.ini')
config = configparser.ConfigParser()
config.read(config_path)

def search_place(place_name=None, coordinates=None, city=None, country=None):
    """
    Search for a place using Mapbox Searchbox API.
    
    Modes:
    - Forward search: provide place_name, city, country
    - Reverse search: provide coordinates=(longitude, latitude)

    Returns structured dict:
        { mapbox_id, name, full_address }
    or None if no valid result.
    """
    if (not place_name and not coordinates) or not city or not country:
        return None
    
    mapbox_api_key = config.get('Mapbox', 'API_KEY', fallback=None)
    if not mapbox_api_key:
        print("Mapbox API key not found in config.ini")
        return None
    
    if place_name:
        params = {
            "q": place_name,
            "access_token": mapbox_api_key,
            "types": "poi,address", # ensure POIs + address results
            "limit": 10,
            "language": "en"
        }
    if coordinates:
        params = {
            "longitude": coordinates[0],
            "latitude": coordinates[1],
            "access_token": mapbox_api_key,
            "types": "poi,address", # ensure POIs + address results
            "limit": 10,
            "language": "en"
        }

    url_forward = "https://api.mapbox.com/search/searchbox/v1/forward"
    url_reverse = "https://api.mapbox.com/search/searchbox/v1/reverse"

    try:
        url = url_forward if place_name else url_reverse
        response = requests.get(url, params=params, timeout=6)
        response.raise_for_status()

        data = response.json()
        features = data.get("features", [])
        if not features:
            # print(f"No results found for place '{place_name}' in mapbox searchbox.")
            return None
        
        city_lower = city.strip().lower()
        country_lower = country.strip().lower()
        
        valid_results = []
        for feature in features:
            props = feature.get("properties", {})
            context = props.get("context", {})

            # Extract fields
            feature_country = context.get("country", {}).get("name", "")
            feature_country_code = context.get("country", {}).get("country_code", "")
            feature_city = context.get("place", {}).get("name", "")

            # check country match
            country_match = (feature_country.lower() == country_lower or feature_country_code.lower() == country_lower)
            if not country_match:
                continue

            # check city match
            city_match = feature_city.lower() == city_lower
            if not city_match:
                continue

            valid_results.append(feature)
            break
        
        if not valid_results:
            # print(f"No valid results matching for place '{place_name}' in {city}, {country}.")
            return None

        top_result = valid_results[0]
        top_result_props = top_result.get("properties", {})

        result = {
            "mapbox_id": top_result_props.get("mapbox_id"),
            "name": top_result_props.get("name") or top_result_props.get("name_preferred"),
            "full_address": top_result_props.get("full_address") or top_result_props.get("place_formatted"),
        }
        return result

    except requests.RequestException as e:
        print(f"Error searching for place '{place_name}' in mapbox searchbox: {e}")
        return None

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
