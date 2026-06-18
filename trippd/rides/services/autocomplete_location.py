import os
from django.conf import settings
import requests
from dotenv import load_dotenv

load_dotenv()


def autocomplete_location(query):
    """Fetches location suggestions based on a query string using the Geoapify API."""
    api_key = os.getenv("GEOAPIFY_API_KEY")

    response = requests.get(
        "https://api.geoapify.com/v1/geocode/autocomplete",
        params={
            "apiKey": api_key,
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
