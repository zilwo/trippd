from django.conf import settings
import requests


def autocomplete_location(query):
    """Fetches location suggestions based on a query string using the Geoapify API."""

    response = requests.get(
        "https://api.geoapify.com/v1/geocode/autocomplete",
        params={
            "apiKey": settings.GEOAPIFY_API_KEY,
            "text": query,
            "limit": 5,
            "format": "json",
            "filter": ["in"],
        },
    )

    return [
        {
            "addr": result.get("formatted"),
            "city": result.get("city"),
            "lat": result.get("lat"),
            "lon": result.get("lon"),
        }
        for result in response.json().get("results", [])
    ]
