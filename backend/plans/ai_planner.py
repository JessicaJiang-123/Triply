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
def generate_trip_recommendations(trip_name, city, preferences, num_days):
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
            "category": "e.g., Museum, Restaurant",
            "start_time": "HH:MM",
            "end_time": "HH:MM",
            "notes": "A brief note about this place."
          }}
        ]
      }}
    ]
    """

# generate the AI response
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt_contents
        )
        # empty response check
        if not response.text:
            raise ValueError("AI returned an empty response.")
        # parse the JSON from the response
        json_text = response.text.strip().replace("```json", "").replace("```", "")
        recommendations = json.loads(json_text)
        return recommendations

    except Exception as e:
        print(f"ERROR: Failed to generate or parse AI response.\n   Details: {e}")
        return None