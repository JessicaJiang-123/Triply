import time
import google.genai as genai
from google.genai import types
import configparser
import os
import json

from ..serializers import PlaceSerializer
from .place_service import create_place_for_day
from ..utils.map_utils import get_coordinate_from_address, search_place
from .trip_service import create_trip_with_days

# configure API key
config_path = os.path.join(os.path.dirname(__file__), '../../', 'config.ini')
config = configparser.ConfigParser()
config.read(config_path)

client = None
try:
    api_key = config.get('Gemini', 'API_KEY')
    if not api_key:
        raise ValueError("API_KEY value in config.ini is empty.")
    # Set the API key as an environment variable
    os.environ['GOOGLE_API_KEY'] = api_key
    client = genai.Client()
    print("Google GenAI Client initialized successfully.")

except (configparser.NoSectionError, configparser.NoOptionError) as e:
    print(
        f"Failed to load [Gemini] API_KEY from 'backend/config.ini'.\n"
        f"AI features will be disabled. Details: {e}"
    )


# function to generate prompt for Gemini using user input from AddTripPage
def generate_trip_recommendations(trip_name, city, country, preferences, num_days, max_retries=3):
    """
    Calls the Gemini API to generate a list of place recommendations.
    """
    
    if client is None:
        print("ERROR: AI Client is not initialized. Cannot generate recommendations.")
        return None
    
    google_map_supported = config.getboolean('Gemini', 'GOOGLE_MAP_SUPPORTED', fallback=False)
    google_map_tool_instruction = """
    You have access to Google Maps.
    - You MUST use the Google Maps tool to verify the real-world existence of every place.
    - You MUST fetch the EXACT "latitude" and "longitude" from Google Maps for each place.
    - Do NOT estimate or approximate coordinates; only use values returned by Google Maps.
    - If a place CANNOT be verified on Google Maps or does NOT have an exact match:
        - DISCARD that place immediately and choose another valid, verifiable place instead.
    - EVERY place in your final plan must be fully verified using Google Maps.
    """
    
    preference_descriptions = {
        "Eating and Drinking": 
            "Eating and Drinking: prioritize famous restaurants, cafes, food markets, and iconic local dishes.",
        "Shopping":
            "Shopping: prioritize popular malls, outlets, markets, shopping streets, and brand-name districts.",
        "City Walk":
            "City Walk: prioritize walkable neighborhoods, promenades, famous streets, scenic routes, and plazas.",
        "Nature & Outdoor":
            "Nature & Outdoor: prioritize parks, gardens, viewpoints, hikes, waterways, and natural attractions.",
        "Historical & Cultural":
            "Historical & Cultural: prioritize museums, monuments, temples, historic sites, architecture, galleries.",
        "Nightlife":
            "Nightlife: prioritize well-known bars, clubs, live music venues, night markets, and late-night districts.",
        "Relaxation & Wellness":
            "Relaxation & Wellness: prioritize spas, hot springs, beaches, saunas, wellness centers, tea houses.",
    }

    Japan_special_instructions = """
    SPECIAL RULE FOR JAPAN ADDRESSES:
    Format the address using canonical Japanese address structure:
    - Prefecture + City/Ward + District/Oaza + Chome + Block + House Number 
      (e.g., 東京都江東区有明1-6-7).
    - Use Kanji with numeric chome/block/house fields separated by hyphens.
    - Do NOT include building names, floors, entrances, or extra descriptors.
    - Kanji is preferred for highest Mapbox accuracy; Romaji is allowed but less reliable.
    - The address must be a specific, complete, real address that Mapbox can validate.
    """

    # Only include descriptions for preferences that the user selected
    selected_pref_text = "\n".join(
        f"• {preference_descriptions[p]}" 
        for p in preferences 
        if p in preference_descriptions
    )

    if not selected_pref_text:
        selected_pref_text = "• No specific preferences provided. Choose balanced, popular activities."

    output_format_instruction = """
    [
      {{
        "day": 1,
        "places": [
          {{
            "name": "Name of the place",
            "address": "Full address of the place (e.g., 123 Main St, City, State, Country)",
            "start_time": "HH:MM",
            "end_time": "HH:MM",
            "notes": "A brief note about this place (<= 200 characters)"
          }}
        ]
      }}
    ]
    """

    google_map_output_format_instruction = """
    [
      {{
        "day": 1,
        "places": [
          {{
            "name": "Name of the place",
            "address": "Full address of the place (e.g., 123 Main St, City, State, Country)",
            "latitude": 35.12345,
            "longitude": 139.12345,
            "start_time": "HH:MM",
            "end_time": "HH:MM",
            "notes": "A brief note about this place (<= 200 characters)"
          }}
        ]
      }}
    ]
    """

    # construct the prompt
    prompt_contents = f"""
    You are a travel planning expert.
    A user is planning a trip with the title: "{trip_name}".
    
    Based on the following request, generate a travel plan for {city} spanning {num_days} day(s).

    User Travel Preferences: {', '.join(preferences) if preferences else "None"}

    IMPORTANT:
    {google_map_tool_instruction if google_map_supported else ""}

    - Take the user's Travel Preferences into consideration **whenever they are provided**.
    - Preferences should meaningfully influence which places are selected.
    - Selected preference categories are:
    {selected_pref_text}

    - If multiple preferences are selected, try to balance them naturally across the day's activities.
    - All selected locations must still follow the strict rules below.

    STRICT RULES:
    1. Each place must have a valid "start_time" and "end_time".
    2. "start_time" and "end_time" must occur on the SAME day.
    3. "start_time" must be EARLIER THAN OR EQUAL TO "end_time".
    4. Times must be in 24-hour format "HH:MM".
    5. Times must be chronological in the day's schedule (each place must start at or after the previous place ends).
    6. EVERY place must have a SPECIFIC and REAL name (e.g., "Louvre Museum", NOT "Downtown Area" or "Beach District").
    7. PRIORITIZE FAMOUS, POPULAR, AND WIDELY KNOWN PLACES that are easy to find on real map services such as Mapbox.
        - Avoid obscure, niche, or difficult-to-query locations.
        - Use landmarks, major attractions, well-known museums, well-reviewed restaurants, etc.
    8. The "address" must be a SPECIFIC, PRECISE, REAL address. 
        - Do NOT give ranges or general zones (e.g., "5th Avenue Shops", "Central Park Area").
        - Provide full detailed addresses like "123 Main St, City, State, Country".
    9. Do NOT include descriptions inside the "name" field.
    10. Do NOT invent vague or fictional venues — use well-known or plausible real places.
    11. The "notes" field must be a short description with a MAXIMUM of 200 characters.

    {Japan_special_instructions if country.strip().lower() == "japan" else ""}

    ADDITIONAL PLANNING RULES:
    12. Consider **geographic distance** between consecutive places.
        - Prefer routes that minimize travel time.
        - Avoid jumping back and forth across the city unnecessarily.
        - Group nearby attractions together on the same day.
    13. Include **meal-friendly restaurant stops** when appropriate.
        - Add lunch stop around **11:30-13:30**.
        - Add dinner stop around **17:30-19:30**.
        - Restaurants must be well-known, popular, and easy to find on Mapbox.
        - Do NOT invent fictional restaurants.
    14. Restaurants must also follow all time rules (valid start/end, chronological ordering).

    Respond with ONLY a valid JSON array in the following format.
    Do not include any other text or markdown formatting (like ```json).
    OUTPUT FORMAT (your output must match this exactly):

    {google_map_output_format_instruction if google_map_supported else output_format_instruction}
    """

    tools = [types.Tool(google_maps=types.GoogleMaps())]

    delay = 1  # exponential backoff initial delay

    for attempt in range(1, max_retries + 1):
        print(f"[AI Planner] Attempt {attempt}/{max_retries} to generate trip recommendations...")

        # generate the AI response
        try:
            if google_map_supported:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt_contents,
                    config=types.GenerateContentConfig(
                        tools=tools
                    )
                )
            else:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt_contents
                )

            # empty response check
            raw_text = (response.text or "").strip()
            if not raw_text:
                raise ValueError("AI returned an empty response.")
            
            # parse the JSON from the response
            json_text = raw_text.replace("```json", "").replace("```", "").strip()
            recommendations = json.loads(json_text)

            # validate the structure
            if not isinstance(recommendations, list) or len(recommendations) != num_days:
                raise ValueError("AI response does not match expected format or number of days.")

            return recommendations
        
        except Exception as e:
            print(f"[AI Planner] Attempt {attempt} failed: {e}")

            if attempt == max_retries:
                print("[AI Planner] Max retries reached. Unable to generate recommendations.")
                return None
            
            time.sleep(delay)
            delay *= 2  # exponential backoff

    return None

def create_trip_plan_from_ai(user, trip_data):
    """
    Create Trip, Days and create Place objects from AI-generated recommendations.
    """
    # Calculate number of days
    num_days = (trip_data['end_date'] - trip_data['start_date']).days + 1

    # if num_days is larger than 5, return None
    if num_days > 5:
        print("Trip with more than 5 days is not supported for AI planning.")
        return None, "Trip with more than 5 days is not supported for AI planning."

    # Create the Trip and Day objects
    trip = create_trip_with_days(user, trip_data)

    destination_parts = trip.destination_city.strip().split(",")
    city = destination_parts[0].strip()
    country = destination_parts[-1].strip() if len(destination_parts) > 1 else ""
    preferences = trip_data.get('preferences', [])

    days = list(trip.days.order_by('order')) # type: ignore

    # Generate AI recommendations
    recommendations = generate_trip_recommendations(
        trip_name=trip.name,
        city=trip.destination_city,
        country=country,
        preferences=preferences,
        num_days=num_days,
    )

    if not recommendations:
        trip.delete()
        print("Failed to generate trip recommendations from AI.")
        return None, "AI planner is busy or not available now, please try again later."
    
    print("AI Recommendations:", json.dumps(recommendations, indent=2))
    
    # Create Place objects based on AI recommendations
    for day_plan in recommendations:
        day_number = day_plan.get("day", None)
        if not day_number:
            continue

        day_index = day_number - 1
        if not (0 <= day_index < len(days)):
            continue

        print(f"\nProcessing day {day_number} with day_id={days[day_index].id}")

        day_obj = days[day_index]

        day_plan_places = day_plan.get('places', [])
        print(f" Number of places to add: {len(day_plan_places)}")

        for idx, place_data in enumerate(day_plan_places, start=1):
            print(f"  Processing place {idx}/{len(day_plan_places)}:")

            latitude = place_data.get("latitude", None)
            longitude = place_data.get("longitude", None)
            search_place_name = place_data.get("name", "")
            search_place_address = place_data.get("address", "")

            search_result = None

            # First, try to search the place using google coordinates if available
            if latitude is not None and longitude is not None:
                print(f"    Searching for place '{search_place_name}' using Google coordinates '{longitude}, {latitude}'...")
                search_result = search_place(
                    place_name=search_place_name,
                    place_address=search_place_address,
                    city=city,
                    country=country,
                    coordinates=(longitude, latitude)
                )
            else:
                print(f"    Searching for place '{search_place_name}' using place name...")
                search_result = search_place(place_name=search_place_name, place_address=search_place_address, city=city, country=country)
                if search_result:
                    longitude = search_result.get("longitude", None)
                    latitude = search_result.get("latitude", None)
                else:
                    # Place not found in Mapbox, validate address
                    print(f"    Converting address '{search_place_address}' to get coordinates...")
                    longitude, latitude = get_coordinate_from_address(search_place_address)
                    if not longitude or not latitude:
                        print(f"    [Skipped] place '{search_place_name}': not found in Mapbox.")
                        continue
                    else:
                        # search again using coordinates
                        print(f"    Searching for place '{search_place_name}' again using coordinates '{longitude}, {latitude}'...")
                        search_result = search_place(place_name=search_place_name, place_address=search_place_address, city=city, country=country, coordinates=(longitude, latitude))

            if not search_result:
                # fallback: leave mapbox_id empty
                search_result = {
                    "name": search_place_name,
                    "full_address": search_place_address,
                    "mapbox_supported": False,
                }
                print(f"    [Fallback] Using provided address info for place '{search_place_name}'.")
            else:
                print(f"    [Found] place: {search_result['name']} at {search_result['full_address']})")

            # Prepare data for Place creation
            place_input_data = {
                "name": search_result['name'],
                "address": search_result['full_address'],
                "longitude": longitude,
                "latitude": latitude,
                "raw_mapbox_id": search_result.get('mapbox_id', None),
                "mapbox_supported": search_result.get("mapbox_supported", False),
                "start_time": place_data.get("start_time", ""),
                "end_time": place_data.get("end_time", ""),
                "notes": place_data.get("notes", ""),
            }

            # validate place input data
            place_serializer = PlaceSerializer(data=place_input_data)
            if not place_serializer.is_valid():
                print(f"    [Skipped] place '{search_place_name}': invalid data - {place_serializer.errors}")
                continue

            create_place_for_day(place_input_data, day_obj)
            print(f"    [Added] place '{search_result['name']}' to day {day_number}.")

    return trip, None
