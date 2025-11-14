from datetime import datetime
from django.shortcuts import get_object_or_404
from django.db import models as dj_models
from django.db.models import F
from rest_framework.exceptions import PermissionDenied
from ..models import Day, Place, Trip, RouteSegment, SharedPlace
from ..serializers import PlaceSerializer
from ..utils.fetch_image import fetch_image_url
from ..utils.convert_coordinate import get_coordinate_from_address
from ..utils.fetch_route_between_points import fetch_route_between_points

def get_trip_and_day_for_user(trip_id, day_id, user):
    """
    Fetch Trip and Day objects.
    Raises:
        Http404 if trip/day does not exist
        PermissionDenied if the trip does not belong to the user
    Returns (trip, day_obj)
    """
    trip = get_object_or_404(Trip, pk=trip_id)
    if trip.user != user:
        raise PermissionDenied("Not allowed to access this trip.")

    day_obj = get_object_or_404(Day, pk=day_id, trip=trip)
    return trip, day_obj

def create_place_for_day(data, day_obj):
    """
    Create a new Place for the given Day, adjusting orders and route segments as needed.
    """
    # validate input data
    input_serializer = PlaceSerializer(data=data)
    input_serializer.is_valid(raise_exception=True)

    # check if mapbox_id is provided
    mapbox_id = data.get('mapbox_id', None)
    if not mapbox_id:
        raise ValueError("mapbox_id is required for a place.")

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
    serializer.is_valid(raise_exception=True)
    
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

    # link (or create) the SharedPlace if mapbox_id is provided
    shared_place, _ = SharedPlace.objects.get_or_create(
        mapbox_id=mapbox_id,
        defaults={
            'name': place.name or '' # type: ignore
        }
    )
    place.shared_place = shared_place # type: ignore
    place.mapbox_id = mapbox_id # type: ignore
    place.save() # type: ignore
    place.refresh_from_db() # type: ignore

    return place

def update_place_for_day(data, day_obj, place_id):
    """
    Update an existing Place for the given Day, adjusting orders and route segments as needed.
    """
    # validate input data
    serializer = PlaceSerializer(data=data)
    serializer.is_valid(raise_exception=True)

    # check if mapbox_id is provided
    new_mapbox_id = data.get('mapbox_id', None)
    if not new_mapbox_id:
        raise ValueError("mapbox_id is required for a place.")

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
        reorder_places_for_day(day_obj)
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

    # If mapbox_id provided and changed, update shared_place accordingly
    if place.mapbox_id != new_mapbox_id:
        # Rebind to the new SharedPlace
        shared_place, _ = SharedPlace.objects.get_or_create(
            mapbox_id=new_mapbox_id,
            defaults={
                'name': data.get('name', place.name) or ''
            }
        )
        place.shared_place = shared_place # type: ignore
        place.mapbox_id = new_mapbox_id
        place.save() # type: ignore
        place.refresh_from_db() # type: ignore

    return place

def reorder_places_for_day(day_obj):
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

def delete_place_for_day(day_obj, place_id):
    """
    Delete a place inside a given day, clean up related route segments,
    and maintain route continuity + reorder all remaining places.
    Returns: list of remaining places ordered by updated order.
    """
    place = get_object_or_404(Place, pk=place_id, day=day_obj)

    deleted_order = place.order

    prev_place = (
        Place.objects.filter(day=day_obj, order=deleted_order - 1).first()
    )
    next_place = (
        Place.objects.filter(day=day_obj, order=deleted_order + 1).first()
    )

    # if deleting from the middle, remove old route segments involving this place
    if prev_place:
        RouteSegment.objects.filter(
            from_place=prev_place,
            to_place=place
        ).delete()

    if next_place:
        RouteSegment.objects.filter(
            from_place=place,
            to_place=next_place
        ).delete()

    # if prev and next exist, create new route segment between them
    if prev_place and next_place:
        route_data = fetch_route_between_points(
            [prev_place.longitude, prev_place.latitude],
            [next_place.longitude, next_place.latitude]
        )
        if route_data:
            RouteSegment.objects.create(
                route_id=f"route-{prev_place.id}-{next_place.id}", # type: ignore
                from_place=prev_place,
                to_place=next_place,
                distance_km=route_data['distance'] / 1000.0,
                travel_time_min=route_data['duration'] / 60.0,
                coordinates=route_data['coordinates']
            )

    place.delete()

    # reorder remaining places
    Place.objects.filter(day=day_obj, order__gt=deleted_order).update(
        order=F('order') - 1)

    # Return ordered list of remaining places
    return Place.objects.filter(day=day_obj).order_by('order')
