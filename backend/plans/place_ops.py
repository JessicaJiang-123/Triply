from datetime import datetime
from django.shortcuts import get_object_or_404
from django.db import models as dj_models
from django.db.models import F
from rest_framework import status
from rest_framework.response import Response
from .models import Place, RouteSegment
from .serializers import PlaceSerializer
from .utils.fetch_image import fetch_image_url
from .utils.convert_coordinate import get_coordinate_from_address
from .utils.fetch_route_between_points import fetch_route_between_points

def create_place_for_day(data, day_obj):
    """
    Create a new Place for the given Day, adjusting orders and route segments as needed.
    """
    start_time_str = data.get('start_time') or None
    new_start = None
    if start_time_str:
        try:
            new_start = datetime.fromisoformat(start_time_str).time()
        except Exception:
            try:
                new_start = datetime.strptime(start_time_str, '%H:%M').time()
            except Exception:
                new_start = None

    max_order = (Place.objects.filter(day=day_obj)
                    .aggregate(dj_models.Max('order'))['order__max'] or 0)

    if new_start is None:
        assign_order = max_order + 1
    else:
        # find insertion order
        insertion_order = max_order + 1
        for p in Place.objects.filter(day=day_obj).order_by('order'):
            if p.start_time and new_start and p.start_time > new_start:
                insertion_order = p.order
                break

        # shift later places to make room for the new place
        if insertion_order <= max_order:
            Place.objects.filter(day=day_obj, order__gte=insertion_order).update(
                order=F('order') + 1)
        assign_order = insertion_order

    # fetch image
    image_url = fetch_image_url(data.get("name", ""))
    data["image_url"] = image_url

    # Convert address to coordinates
    longitude, latitude = get_coordinate_from_address(data.get("address", ""))
    data["longitude"] = longitude
    data["latitude"] = latitude
    
    serializer = PlaceSerializer(data=data)
    if not serializer.is_valid():
        print(f"ERROR: PlaceSerializer validation failed. Details: {serializer.errors}")
        return Response({"detail": "Invalid place data."}, status=status.HTTP_400_BAD_REQUEST)
        
    place = serializer.save(day=day_obj, order=assign_order)

    prev_place = (
        Place.objects.filter(day=day_obj, order=assign_order - 1).first()
    )
    next_place = (
        Place.objects.filter(day=day_obj, order=assign_order + 1).first()
    )

    # if inserting in the middle, remove old route segment between prev and next
    if prev_place and next_place:
        RouteSegment.objects.filter(
            from_place=prev_place,
            to_place=next_place
        ).delete()

    # create new route segments involving the new place
    if prev_place:
        route_data = fetch_route_between_points(
            [prev_place.longitude, prev_place.latitude],
            [place.longitude, place.latitude] # type: ignore
        )
        if route_data:
            RouteSegment.objects.create(
                route_id=f"route-{prev_place.id}-{place.id}", # type: ignore
                from_place=prev_place,
                to_place=place,
                distance_km=route_data['distance'] / 1000.0,
                travel_time_min=route_data['duration'] / 60.0,
                coordinates=route_data['coordinates']
            )

    if next_place:
        route_data = fetch_route_between_points(
            [place.longitude, place.latitude], # type: ignore
            [next_place.longitude, next_place.latitude]
        )
        if route_data:
            RouteSegment.objects.create(
                route_id=f"route-{place.id}-{next_place.id}", # type: ignore
                from_place=place,
                to_place=next_place,
                distance_km=route_data['distance'] / 1000.0,
                travel_time_min=route_data['duration'] / 60.0,
                coordinates=route_data['coordinates']
            )

    return Response(PlaceSerializer(place).data, status=status.HTTP_201_CREATED)

def update_place_for_day(data, day_obj, place_id):
    """
    Update an existing Place for the given Day, adjusting orders and route segments as needed.
    """
    place = get_object_or_404(Place, pk=place_id, day=day_obj)

    # Track whether name or image is updated
    name_changed = "name" in data and data["name"] != place.name
    address_changed = "address" in data and data["address"] != place.address
    image_requested = "image_url" in data  # explicitly indicated by frontend
    start_time_changed = (
        "start_time" in data and str(data["start_time"]) != str(place.start_time)
    )

    # if user requested new image or place name changed, fetch new image
    if image_requested or name_changed:
        place.image_url = fetch_image_url(data.get("name", ""))

    # if place name changed, update the coordinates
    if name_changed or address_changed:
        longitude, latitude = get_coordinate_from_address(data.get("address", ""))
        place.longitude = longitude
        place.latitude = latitude

    # update mutable fields
    for field in [
        "name",
        "address",
        "start_time",
        "end_time",
        "notes",
        "category",
    ]:
        if field in data:
            setattr(place, field, data[field])

    place.save()
    
    # If start_time changed, we may need to reorder places
    if start_time_changed:
        reorder_places_for_day(day_obj, place.id) # type: ignore
        place.refresh_from_db() # refresh to get updated order if changed

    # If name or address changed, we may need to recompute route segments
    if name_changed or address_changed:
        prev_place = (
            Place.objects.filter(day=day_obj, order=place.order - 1).first()
        )
        next_place = (
            Place.objects.filter(day=day_obj, order=place.order + 1).first()
        )

        # update route segment from prev_place to this place
        if prev_place:
            route_data = fetch_route_between_points(
                [prev_place.longitude, prev_place.latitude],
                [place.longitude, place.latitude]
            )
            if route_data:
                RouteSegment.objects.update_or_create(
                    from_place=prev_place,
                    to_place=place,
                    defaults={
                        'route_id': f"route-{prev_place.id}-{place.id}", # type: ignore
                        'distance_km': route_data['distance'] / 1000.0,
                        'travel_time_min': route_data['duration'] / 60.0,
                        'coordinates': route_data['coordinates']
                    }
                )

        # update route segment from this place to next_place
        if next_place:
            route_data = fetch_route_between_points(
                [place.longitude, place.latitude],
                [next_place.longitude, next_place.latitude]
            )
            if route_data:
                RouteSegment.objects.update_or_create(
                    from_place=place,
                    to_place=next_place,
                    defaults={
                        'route_id': f"route-{place.id}-{next_place.id}", # type: ignore
                        'distance_km': route_data['distance'] / 1000.0,
                        'travel_time_min': route_data['duration'] / 60.0,
                        'coordinates': route_data['coordinates']
                    }
                )

    serializer = PlaceSerializer(place)
    return Response(serializer.data, status=status.HTTP_200_OK)

def reorder_places_for_day(day_obj, place_id):
    """
    Reorder places by start_time/order, then only update RouteSegments
    for newly changed adjacency pairs (based on place.id).
    """
    # first get the snapshot of current order
    old_places = list(Place.objects.filter(day=day_obj).order_by('order'))
    old_pairs = {
        (old_places[i].id, old_places[i + 1].id) # type: ignore
        for i in range(len(old_places) - 1)
    }

    # then reorder based on start_time/order
    new_places = list(Place.objects.filter(day=day_obj).order_by('start_time', 'order'))
    for index, place in enumerate(new_places, start=1):
        if place.order != index:
            place.order = index
            place.save(update_fields=['order'])

    # compute new adjacency pairs
    new_pairs = {
        (new_places[i].id, new_places[i + 1].id) # type: ignore
        for i in range(len(new_places) - 1)
    }

    # compute differences
    removed_pairs = old_pairs - new_pairs
    added_pairs = new_pairs - old_pairs

    # delete RouteSegments for removed pairs
    for from_id, to_id in removed_pairs:
        RouteSegment.objects.filter(
            from_place_id=from_id,
            to_place_id=to_id
        ).delete()

    # create RouteSegments for added pairs
    for from_id, to_id in added_pairs:
        from_place = Place.objects.get(id=from_id)
        to_place = Place.objects.get(id=to_id)

        if not (from_place and to_place):
            continue

        route_data = fetch_route_between_points(
            [from_place.longitude, from_place.latitude],
            [to_place.longitude, to_place.latitude]
        )
        if route_data:
            RouteSegment.objects.create(
                route_id=f"route-{from_id}-{to_id}",
                from_place_id=from_id,
                to_place_id=to_id,
                distance_km=route_data['distance'] / 1000.0,
                travel_time_min=route_data['duration'] / 60.0,
                coordinates=route_data['coordinates']
            )
