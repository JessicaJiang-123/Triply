import requests
import random
import configparser
import os

# Load API key from config.ini
config_path = os.path.join(os.path.dirname(__file__), '../../', 'config.ini')
config = configparser.ConfigParser()
config.read(config_path)

def fetch_image_url(place_name, get_all=False):
    """
    Fetch a place image URL from Unsplash API based on the place name.
    If get_all is True, return a list of all image URLs found.
    If no images are found or an error occurs, return a default image URL.
    """
    default_image_url = "/login_bg.jpg"

    if not place_name:
        return default_image_url
    
    unsplash_api_key = config.get('Unsplash', 'API_KEY', fallback=None)
    if not unsplash_api_key:
        print("Unsplash API key not found in config.ini")
        return default_image_url
    
    url = "https://api.unsplash.com/search/photos"

    try:
        response = requests.get(
            url,
            params={
                "query": place_name,
                "client_id": unsplash_api_key,
                "orientation": "landscape",
                "per_page": 10,
            },
            timeout=5,
        )
        response.raise_for_status()

        data = response.json()
        results = data.get("results", [])

        if not results:
            return default_image_url if not get_all else [default_image_url]
        
        # If get_all is True, return a list of all image URLs
        if get_all:
            image_urls = [
                r.get("urls", {}).get("raw") for r in results if r.get("urls", {}).get("raw")
            ]
            return image_urls or [default_image_url]

        # Otherwise, return a single random image URL
        random_index = random.randint(0, len(results) - 1)
        image_url = (
            results[random_index].get("urls", {}).get("raw")
            or results[0].get("urls", {}).get("raw")
        )
        return image_url or default_image_url

    except Exception as e:
        print(f"Failed to fetch place image for '{place_name}': {e}")
        return default_image_url if not get_all else [default_image_url]
