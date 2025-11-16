from datetime import timedelta
from ..models import Trip, Day
from ..utils.image_utils import fetch_image_url
from ..utils.map_utils import get_coordinate_from_address

def create_trip_with_days(user, validated_data):
    """
    Service that:
    - Creates a Trip with correct image and coordinates
    - Generates all Day objects based on date range
    Returns: trip instance
    """
    destination_city = validated_data.get("destination_city", "").strip()
    main_city_name = destination_city.split(",")[0].strip() if destination_city else ""

    # Fetch city image
    image_url = fetch_image_url(main_city_name)

    # Fetch coordinates
    longitude, latitude = get_coordinate_from_address(destination_city)

    # Save Trip object
    trip = Trip.objects.create(
        user=user,
        name=validated_data["name"],
        destination_city=destination_city,
        start_date=validated_data["start_date"],
        end_date=validated_data["end_date"],
        image_url=image_url,
        latitude=latitude,
        longitude=longitude,
    )

    # Create Day objects
    current_date = trip.start_date
    order = 1
    while current_date <= trip.end_date:
        Day.objects.create(
            trip=trip,
            date=current_date,
            order=order,
        )
        current_date += timedelta(days=1)
        order += 1

    return trip
