import time
import google.genai as genai
import configparser
import os
import json

from ..serializers import PlaceSerializer
from .place_service import create_place_for_day
from ..utils.map_utils import search_place
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
def generate_trip_recommendations(trip_name, city, preferences, num_days, max_retries=3):
    """
    Calls the Gemini API to generate a list of place recommendations.
    """
    
    if client is None:
        print("ERROR: AI Client is not initialized. Cannot generate recommendations.")
        return None
    
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

    # Only include descriptions for preferences that the user selected
    selected_pref_text = "\n".join(
        f"• {preference_descriptions[p]}" 
        for p in preferences 
        if p in preference_descriptions
    )

    if not selected_pref_text:
        selected_pref_text = "• No specific preferences provided. Choose balanced, popular activities."

    # construct the prompt
    prompt_contents = f"""
    You are a travel planning expert.
    A user is planning a trip with the title: "{trip_name}".
    
    Based on the following request, generate a travel plan for {city} spanning {num_days} day(s).

    User Travel Preferences: {', '.join(preferences) if preferences else "None"}

    IMPORTANT:
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
    8. Do NOT include descriptions inside the "name" field.
    9. Do NOT invent vague or fictional venues — use well-known or plausible real places.
    10. The "notes" field must be a short description with a MAXIMUM of 200 characters.

    ADDITIONAL PLANNING RULES:
    11. Consider **geographic distance** between consecutive places.
        - Prefer routes that minimize travel time.
        - Avoid jumping back and forth across the city unnecessarily.
        - Group nearby attractions together on the same day.
    12. Include **meal-friendly restaurant stops** when appropriate.
        - Add lunch stop around **11:30-13:30**.
        - Add dinner stop around **17:30-19:30**.
        - Restaurants must be well-known, popular, and easy to find on Mapbox.
        - Do NOT invent fictional restaurants.
    13. Restaurants must also follow all time rules (valid start/end, chronological ordering).

    Respond with ONLY a valid JSON array in the following format.
    Do not include any other text or markdown formatting (like ```json).
    OUTPUT FORMAT (your output must match this exactly):

    [
      {{
        "day": 1,
        "places": [
          {{
            "name": "Name of the place",
            "start_time": "HH:MM",
            "end_time": "HH:MM",
            "notes": "A brief note about this place (<= 200 characters)"
          }}
        ]
      }}
    ]
    """

    delay = 1  # exponential backoff initial delay

    for attempt in range(1, max_retries + 1):
        print(f"[AI Planner] Attempt {attempt}/{max_retries} to generate trip recommendations...")

        # generate the AI response
        try:
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
        preferences=preferences,
        num_days=num_days,
    )

    if not recommendations:
        trip.delete()
        print("Failed to generate trip recommendations from AI.")
        return None, "Failed to generate trip recommendations from AI."
    
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

            search_place_name = place_data.get("name", "")
            print(f"    Searching for place '{search_place_name}'...")
            search_result = search_place(search_place_name, city, country)
            if not search_result:
                print(f"    [Skipped] place '{search_place_name}': not found in mapbox search.")
                continue

            print(f"    Found place: {search_result['name']} at {search_result['full_address']} (mapbox_id={search_result['mapbox_id']})")

            # Prepare data for Place creation
            place_input_data = {
                "name": search_result['name'],
                "address": search_result['full_address'],
                "mapbox_id": search_result['mapbox_id'],
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
