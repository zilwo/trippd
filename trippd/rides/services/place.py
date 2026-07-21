from django.conf import settings
import requests
from rides.models import Place
import time

client_session = requests.Session()


def autocomplete_places(query, session_token=None):
    url = "https://places.googleapis.com/v1/places:autocomplete"
    headers = {
        "X-Goog-Api-Key": settings.GOOGLE_SECRET_KEY,
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
    }

    response = client_session.post(
        url,
        headers=headers,
        json=payload,
        timeout=10,
    )
    response.raise_for_status()

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
        "X-Goog-Api-Key": settings.GOOGLE_SECRET_KEY,
        "X-Goog-FieldMask": (
            "id,"
            "displayName,"
            "formattedAddress,"
            "location,"
            "types,"
            "primaryType,"
            "photos,"
            "googleMapsLinks"
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

    photos = [photo["name"] for photo in data.get("photos", [])[:5]]

    return {
        "name": data["displayName"]["text"],
        "place_id": data["id"],
        "address": data["formattedAddress"],
        "latitude": data["location"]["latitude"],
        "longitude": data["location"]["longitude"],
        "types": data.get("types", []),
        "primary_type": data.get("primaryType", None),
        "photos": photos,
        "map_url": data.get("googleMapsLinks", {}).get("photosUri", None),
    }


def get_place_photo_url(photo_name, max_width=1200):
    return (
        f"https://places.googleapis.com/v1/{photo_name}/media"
        f"?maxWidthPx={max_width}"
        f"&key={settings.GOOGLE_SECRET_KEY}"
    )


def get_nearby_places(latitude, longitude, radius=1000, type_filter=None):
    url = "https://places.googleapis.com/v1/places:searchNearby"

    headers = {
        "X-Goog-Api-Key": settings.GOOGLE_SECRET_KEY,
        "Content-Type": "application/json",
        "X-Goog-FieldMask": (
            "places.id,"
            "places.displayName,"
            "places.shortFormattedAddress,"
            "places.location,"
            "places.types,"
            "places.primaryType,"
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
        "maxResultCount": 5,
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

    return [
        {
            "place_id": p["id"],
            "name": p["displayName"]["text"],
            "address": p["shortFormattedAddress"],
            "latitude": p["location"]["latitude"],
            "longitude": p["location"]["longitude"],
            "types": p.get("types", []),
            "primary_type": p.get("primaryType"),
            "rating": p.get("rating"),
            "user_rating_count": p.get("userRatingCount"),
            "photo": p.get("photos", [{}])[0].get("name"),
            "maps_url": p.get("googleMapsUri"),
        }
        for p in data.get("places", [])[:5]
    ]


def get_description(place):
    url = "https://generativelanguage.googleapis.com/v1beta/interactions"

    headers = {
        "x-goog-api-key": settings.GEMINI_API_KEY,
        "Content-Type": "application/json",
    }

    place_type = place.get("primary_type") or (
        place["types"][0] if place.get("types") else "place"
    )

    prompt = (
        f"Write a natural travel guide description for {place['name']}, "
        f"a {place_type} in {place['address']}. "
        f"Keep it to 2-3 sentences (40-70 words). "
        f"Focus on what visitors can expect or enjoy, mentioning notable features if appropriate. "
        f"Write in a warm, human style that feels like a travel website, not AI-generated text. "
        f"Do not invent facts, avoid generic phrases, and use plain text only."
    )

    payload = {
        "model": "gemini-3.1-flash-lite",
        "input": prompt,
        "generation_config": {"thinking_level": "minimal"},
    }

    response = client_session.post(url, headers=headers, json=payload, timeout=10)
    print(response.text)
    if response.status_code != 200:
        print("Error generating description:", response.text)
    response.raise_for_status()

    data = response.json()

    try:
        return data["steps"][-1]["content"][0]["text"].strip()
    except (KeyError, IndexError):
        return None


def get_or_create_place(place_id, session_token=None):
    start = time.perf_counter()

    place_details = get_place_details(place_id, session_token)
    print("Place details:", time.perf_counter() - start)

    if not place_details:
        return None

    place, created = Place.objects.get_or_create(
        place_id=place_id,
        defaults={
            "name": place_details["name"],
            "address": place_details["address"],
            "latitude": place_details["latitude"],
            "longitude": place_details["longitude"],
            "primary_type": place_details.get("primary_type", ""),
            "photos": place_details.get("photos", []),
            "map_url": place_details.get("map_url", ""),
        },
    )

    if created:
        start = time.perf_counter()
        place.description = get_description(place_details)
        print("Gemini:", time.perf_counter() - start)
        place.save(update_fields=["description"])

    return place
