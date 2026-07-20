from django.conf import settings
import requests


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

    response = requests.post(
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

    response = requests.get(
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
        f"Write a natural-sounding description (2-4 sentences) "
        f"for a travel activity at '{place['name']}', "
        f"a {place_type} located at {place['address']}. "
        f"Mention what makes this place worth visiting. "
        f"No quotation marks, no markdown, no exclamation marks."
    )

    payload = {
        "model": "gemini-3.1-flash-lite",
        "input": prompt,
        "generation_config": {"thinking_level": "minimal"},
    }

    response = requests.post(url, headers=headers, json=payload, timeout=10)
    print(response.text)
    if response.status_code != 200:
        print("Error generating description:", response.text)
    response.raise_for_status()

    data = response.json()

    try:
        return data["steps"][-1]["content"][0]["text"].strip()
    except (KeyError, IndexError):
        return None
