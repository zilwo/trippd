from django.conf import settings
import requests
from rides.models import Place
import time
from ai.service import generate_place_info

client_session = requests.Session()


def autocomplete_places(query, session_token=None):
    url = "https://places.googleapis.com/v1/places:autocomplete"
    headers = {
        "X-Goog-Api-Key": settings.GOOGLE_PLACES_SECRET_KEY,
        "Content-Type": "application/json",
        "X-Goog-FieldMask": (
            "suggestions.placePrediction.placeId,"
            "suggestions.placePrediction.text,"
            "suggestions.placePrediction.types"
        ),
    }

    payload = {
        "input": query,
        "sessionToken": session_token or "",
        "includedRegionCodes": ["IN"],
        "includedPrimaryTypes": ["(regions)"],
    }

    response = client_session.post(
        url,
        headers=headers,
        json=payload,
        timeout=10,
    )
    print(response.status_code)
    print(response.text)

    data = response.json()

    return [
        {
            "place_id": p["placePrediction"]["placeId"],
            "text": p["placePrediction"]["text"]["text"],
            "type": (
                p["placePrediction"]["types"][0]
                if p["placePrediction"].get("types")
                else None
            ),
        }
        for p in data.get("suggestions", [])
        if "placePrediction" in p
    ]


def get_place_details(place_id, session_token=None):
    url = f"https://places.googleapis.com/v1/places/{place_id}"

    headers = {
        "X-Goog-Api-Key": settings.GOOGLE_PLACES_SECRET_KEY,
        "X-Goog-FieldMask": (
            "id,displayName,formattedAddress,location,types,googleMapsLinks"
        ),
    }
    params = {}
    if session_token:
        params["sessionToken"] = session_token

    response = client_session.get(
        url,
        headers=headers,
        params=params,
        timeout=10,
    )

    response.raise_for_status()

    data = response.json()
    return {
        "name": data["displayName"]["text"],
        "place_id": data["id"],
        "address": data["formattedAddress"],
        "latitude": data["location"]["latitude"],
        "longitude": data["location"]["longitude"],
        "types": data.get("types", []),
        "map_url": data.get("googleMapsLinks", {}).get("photosUri", None),
    }


def get_place_photos(place_id, session_token=None):
    print("Fetching photos for place_id:", place_id)
    url = f"https://places.googleapis.com/v1/places/{place_id}"
    headers = {
        "X-Goog-Api-Key": settings.GOOGLE_PLACES_SECRET_KEY,
        "X-Goog-FieldMask": "photos.name,photos.widthPx,photos.heightPx",
    }
    params = {"sessionToken": session_token} if session_token else {}

    response = client_session.get(url, headers=headers, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    photos = data.get("photos", [])

    photos.sort(
        key=lambda p: (
            p.get("widthPx", 0) >= p.get("heightPx", 0),  # Landscape first
            p.get("widthPx", 0) * p.get("heightPx", 0),  # Then largest resolution
        ),
        reverse=True,
    )

    return [photo.get("name") for photo in photos[:5]]


def get_place_photo_response(place_id, max_width=2400):
    photos = get_place_photos(place_id)
    if not photos:
        return None

    photo_name = photos[0]
    url = (
        f"https://places.googleapis.com/v1/{photo_name}/media"
        f"?maxWidthPx={max_width}"
        f"&key={settings.GOOGLE_PLACES_SECRET_KEY}"
    )

    response = client_session.get(url, timeout=10)
    response.raise_for_status()
    return response


def get_nearby_places(latitude, longitude, radius=10000, type_filter=None):
    url = "https://places.googleapis.com/v1/places:searchNearby"

    headers = {
        "X-Goog-Api-Key": settings.GOOGLE_PLACES_SECRET_KEY,
        "Content-Type": "application/json",
        "X-Goog-FieldMask": (
            "places.id,"
            "places.displayName,"
            "places.shortFormattedAddress,"
            "places.location,"
            "places.types,"
            "places.photos,"
            "places.rating,"
            "places.userRatingCount,"
            "places.googleMapsUri"
        ),
    }

    payload = {
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": latitude,
                    "longitude": longitude,
                },
                "radius": radius,
            }
        },
        "maxResultCount": 20,
    }

    if type_filter:
        payload["includedTypes"] = [type_filter]

    response = client_session.post(
        url,
        headers=headers,
        json=payload,
        timeout=10,
    )

    response.raise_for_status()

    data = response.json()

    places = []

    for p in data.get("places", []):
        # Skip places without photos
        if not p.get("photos"):
            continue

        rating = p.get("rating") or 0
        reviews = p.get("userRatingCount") or 0

        places.append(
            {
                "place_id": p["id"],
                "name": p["displayName"]["text"],
                "address": p.get("shortFormattedAddress", ""),
                "latitude": p["location"]["latitude"],
                "longitude": p["location"]["longitude"],
                "types": p.get("types", []),
                "rating": rating,
                "user_rating_count": reviews,
                "photo": p["photos"][0]["name"],
                "maps_url": p.get("googleMapsUri"),
            }
        )
    places.sort(
        key=lambda p: (
            p["user_rating_count"],
            p["rating"],
        ),
        reverse=True,
    )

    return places[:2]


def enrich_place_with_ai_info(place):
    """Enrich a Place object with AI-generated information."""
    place_details = {
        "name": place.name,
        "address": place.address,
        "latitude": place.latitude,
        "longitude": place.longitude,
        "types": place.types.split(",") if place.types else [],
    }

    ai_info = generate_place_info(place_details)
    place.description = ai_info.summary
    place.highlights = ai_info.highlight
    place.best_time_to_visit = ai_info.best_time_to_visit
    place.best_for = ai_info.best_for
    place.save()


def get_or_create_place(place_id, session_token=None):
    start = time.perf_counter()

    try:
        place = Place.objects.get(place_id=place_id)
    except Place.DoesNotExist:
        place_details = get_place_details(place_id, session_token)
        print("Place details:", time.perf_counter() - start)

        if not place_details:
            return None

        place = Place.objects.create(
            place_id=place_id,
            name=place_details["name"],
            address=place_details["address"],
            latitude=place_details["latitude"],
            longitude=place_details["longitude"],
            types=",".join(place_details.get("types", [])),
            map_url=place_details.get("map_url", ""),
        )
        print("place created:", time.perf_counter() - start)

        start = time.perf_counter()
        enrich_place_with_ai_info(place)
        print("AI:", time.perf_counter() - start)

    return place
