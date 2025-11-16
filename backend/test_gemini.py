import google.genai as genai
import configparser
import os
import json

config_path = os.path.join(os.path.dirname(__file__), 'config.ini') 
config = configparser.ConfigParser()
config.read(config_path)

client = None
try:
    api_key = config.get('Gemini', 'API_KEY')
    if not api_key:
        raise ValueError("API_KEY value in config.ini is empty.")
    
    os.environ['GOOGLE_API_KEY'] = api_key
    client = genai.Client()
    print("✅ Google GenAI Client  initialized successfully.")

except Exception as e:
    print(
        f"❌ Failed to load [Gemini] API_KEY from 'backend/config.ini'.\n"
        f"   Details: {e}"
    )
    exit()

if client:
    # Test different models: gemini-2.5-pro, gemini-2.5-flash, gemini-2.5-flash-preview-09-2025, gemini-2.5-flash-lite, gemini-2.5-flash-lite-preview-09-2025
    
    print("\nAttempting to call gemini-2.5-flash-preview-09-2025 with a simple prompt...")
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-09-2025",
            contents=
                f"""
                You are a travel planning expert.
                A user is planning a trip with the title: "New York Trip".
                
                Based on the following request, generate a travel plan for New York spanning 5 day(s).

                Travel Preferences: Shopping

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
        )
        
        print("\n--- API Response ---")
        print(response.text)
        print("--------------------\n")
        print("✅ SUCCESS: Google API is working correctly.")

    except Exception as e:
        print("\n--- API ERROR ---")
        print(f"❌ ERROR: The API call failed.\n   Details: {e}")
        print("-----------------\n")
        print("🤔 This error is coming directly from Google, not your Django app.")