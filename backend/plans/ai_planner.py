import time
import google.genai as genai
import configparser
import os
import json

# configure API key
config_path = os.path.join(os.path.dirname(__file__), '..', 'config.ini') # /backend/plans/ai_planner.py -> /backend/config.ini
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

    # construct the prompt
    prompt_contents = f"""
    You are a travel planning expert.
    A user is planning a trip with the title: "{trip_name}".
    
    Based on the following request, generate a travel plan for {city} spanning {num_days} day(s).

    Travel Preferences: {', '.join(preferences)}

    Respond with ONLY a valid JSON array in the following format.
    Do not include any other text or markdown formatting (like ```json).

    [
      {{
        "day": 1,
        "places": [
          {{
            "name": "Name of the place",
            "address": "Full address of the place (e.g., 123 Main St, City, State, Country)",
            "start_time": "HH:MM",
            "end_time": "HH:MM",
            "notes": "A brief note about this place."
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
