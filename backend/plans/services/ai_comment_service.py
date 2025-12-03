import time
import google.genai as genai
import configparser
import os
import json

from ..models import Trip, Place

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


def generate_trip_comments(place_list, max_retries=3):
    """
    Calls the Gemini API to generate a list of comments.
    """
    
    if client is None:
        print("ERROR: AI Client is not initialized. Cannot generate comments.")
        return None
    
    place_list_json = json.dumps(place_list, ensure_ascii=False)

    # construct the prompt
    prompt_contents = f"""
    You are a traveler who has just visited several places. Your task is to generate a short, natural, tourist-style comment for each place, along with an appropriate image search keyword.

    INPUT:
    You will receive a list of places in the following format:

    [
        {{
            "mapbox_id": "<string>",
            "name": "<place name>",
            "address": "<place address>",
            "notes": "<brief place description>"
        }},
        ...
    ]

    YOUR TASK:
    For each place, write a brief tourist-style comment consisting of **2-3 sentences**, based on the place's name, address, and notes. The comment should:
    - Be relevant to the *exact* place.
    - Feel natural, like a traveler sharing their experience.
    - Optionally include emojis if they enhance the tone.
    - Reflect the vibe of the location (e.g., peaceful park, vibrant attraction, scenic location).

    Then produce an **image search keyword** for each comment:
    - If the place is a well-known landmark or attraction, the keyword can simply be the place name.
    - If the place is more generic (e.g., parks, neighborhoods, lakes), choose a thematic keyword such as “flowers”, “bird”, “nature trail”, “city skyline”, etc.
    - The keyword must be **directly connected** to the content of the comment.

    STRICT RULES:
    1. For each place in the input, the output must include the **exact same `mapbox_id`** value.
    2. Do **not** modify, truncate, change, or alter the `mapbox_id` in any way.
    3. Do **not** add any extra fields besides:  
        - `mapbox_id`  
        - `image_key_word`  
        - `comment`
    4. Do **not** include additional metadata, explanations, or commentary outside of the specified JSON array format.
    5. The output array must have the **same number of items** as the input list.

    OUTPUT FORMAT:
    Do NOT include any other text or markdown formatting (like ```json).
    Return an array in the following exact structure:

    [
        {{
            "mapbox_id": "<same mapbox_id as input>",
            "image_key_word": "<your chosen keyword>",
            "comment": "<your generated 2-3 sentence comment>"
        }},
        ...
    ]

    Now here is the actual input list of places. Start generating the output:

    {place_list_json}
    """

    delay = 1  # exponential backoff initial delay

    for attempt in range(1, max_retries + 1):
        print(f"[AI Commenter] Attempt {attempt}/{max_retries} to generate comments...")

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
            comments = json.loads(json_text)

            return comments
        
        except Exception as e:
            print(f"[AI Commenter] Attempt {attempt} failed: {e}")

            if attempt == max_retries:
                print("[AI Commenter] Max retries reached. Unable to generate comments.")
                return None
            
            time.sleep(delay)
            delay *= 2  # exponential backoff

    return None


def ai_auto_generate_comments(trip_id, max_retries=3):
    """
    Wrapper function to generate AI comments for a list of places.
    """
    if not trip_id:
        return None, "trip_id query parameter is required"

    # Get trip
    try:
        trip = Trip.objects.get(id=trip_id)
    except Trip.DoesNotExist:
        return None, f"Trip with id {trip_id} does not exist"

    # Fetch all places for this trip.
    places = Place.objects.filter(day__trip=trip).order_by("day__order", "order")

    if not places.exists():
        return None, "This trip has no places"

    # Prepare place_list for AI agent
    place_list = []
    for p in places:
        place_list.append({
            "mapbox_id": p.mapbox_id,
            "name": p.name,
            "address": p.address,
            "notes": p.notes or "",
        })

    validated_comments = []

    for attempt in range(1, max_retries + 1):
        print(f"[AI Commenter] Comment Validation Attempt {attempt}/{max_retries}:")
        # Call AI comment generator
        comment_results = generate_trip_comments(place_list)
        if comment_results is None:
            if attempt == max_retries:
                return None, "Failed to generate comments from AI"
            continue
        
        print("AI-generated comments: ", json.dumps(comment_results, indent=2))
        print(f"[AI Commenter] Generated {len(comment_results)}/{len(place_list)} comments")

        current_validated = []
        # Validate each comment has valid mapbox_id
        for comment in comment_results:
            if "mapbox_id" in comment:
                # check if mapbox_id exists in place_list
                if any(p["mapbox_id"] == comment["mapbox_id"] for p in place_list):
                    current_validated.append(comment)

        validated_comments = current_validated
        print(f"[AI Commenter] Validated {len(validated_comments)}/{len(place_list)} comments after mapbox_id check")

        if len(validated_comments) == len(place_list):
            break

    return validated_comments, None
