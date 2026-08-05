import requests

client = requests.Session()

WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Freezing drizzle",
    57: "Heavy freezing drizzle",
    61: "Light rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Freezing rain",
    67: "Heavy freezing rain",
    71: "Light snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Light rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Light snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Severe thunderstorm with hail",
}

WEATHER_ICONS = {
    0: {"day": "sun", "night": "moon"},
    1: {"day": "cloud-sun", "night": "cloud-moon"},
    2: {"day": "cloud-sun", "night": "cloud-moon"},
    3: {"day": "cloud", "night": "cloud"},
    45: {"day": "cloud-fog", "night": "cloud-fog"},
    48: {"day": "cloud-fog", "night": "cloud-fog"},
    51: {"day": "cloud-drizzle", "night": "cloud-drizzle"},
    53: {"day": "cloud-drizzle", "night": "cloud-drizzle"},
    55: {"day": "cloud-drizzle", "night": "cloud-drizzle"},
    56: {"day": "cloud-drizzle", "night": "cloud-drizzle"},
    57: {"day": "cloud-drizzle", "night": "cloud-drizzle"},
    61: {"day": "cloud-rain", "night": "cloud-rain"},
    63: {"day": "cloud-rain", "night": "cloud-rain"},
    65: {"day": "cloud-rain-wind", "night": "cloud-rain-wind"},
    66: {"day": "cloud-hail", "night": "cloud-hail"},
    67: {"day": "cloud-hail", "night": "cloud-hail"},
    71: {"day": "cloud-snow", "night": "cloud-snow"},
    73: {"day": "cloud-snow", "night": "cloud-snow"},
    75: {"day": "cloud-snow", "night": "cloud-snow"},
    77: {"day": "cloud-snow", "night": "cloud-snow"},
    80: {"day": "cloud-rain", "night": "cloud-rain"},
    81: {"day": "cloud-rain-wind", "night": "cloud-rain-wind"},
    82: {"day": "cloud-rain-wind", "night": "cloud-rain-wind"},
    85: {"day": "cloud-snow", "night": "cloud-snow"},
    86: {"day": "cloud-snow", "night": "cloud-snow"},
    95: {"day": "cloud-lightning", "night": "cloud-lightning"},
    96: {"day": "cloud-lightning", "night": "cloud-lightning"},
    99: {"day": "cloud-lightning", "night": "cloud-lightning"},
}


def get_weather_icon(weather_code, is_day):
    variant = "day" if is_day else "night"
    icons = WEATHER_ICONS.get(weather_code, {"day": "cloud-off", "night": "cloud-off"})
    return icons[variant]


def generate_travel_advisory(current, forecast):
    advisory = {
        "level": "Good",
        "message": "Weather conditions are generally favorable for travel and outdoor activities.",
    }

    severe_conditions = {
        "Heavy rain",
        "Violent rain showers",
        "Thunderstorm",
        "Thunderstorm with hail",
        "Severe thunderstorm with hail",
        "Heavy snow",
        "Heavy snow showers",
    }

    if any(day["condition"] in severe_conditions for day in forecast):
        return {
            "level": "High",
            "message": (
                "Severe weather is forecast over the next few days. Outdoor activities "
                "may be unsafe and travel disruptions are possible."
            ),
        }

    if any(day["rain_probability"] >= 80 for day in forecast):
        advisory = {
            "level": "Moderate",
            "message": (
                "Rain is likely during the next few days. Plan indoor alternatives and "
                "carry rain protection."
            ),
        }

    elif current["wind_speed"] >= 40:
        advisory = {
            "level": "Moderate",
            "message": (
                "Strong winds may affect outdoor activities and some transport services."
            ),
        }

    elif any(day["max_temperature"] >= 35 for day in forecast):
        advisory = {
            "level": "Moderate",
            "message": (
                "Hot weather is expected. Stay hydrated, wear sunscreen, and avoid "
                "prolonged afternoon exposure."
            ),
        }

    elif any(day["uv_index"] >= 8 for day in forecast):
        advisory = {
            "level": "Low",
            "message": (
                "UV levels will be high. Use sunscreen and wear protective clothing if "
                "you'll be outdoors."
            ),
        }

    print("Travel advisory generated:", advisory)
    return advisory


def get_current_weather(latitude, longitude):
    response = client.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": latitude,
            "longitude": longitude,
            "timezone": "auto",
            "forecast_days": 4,
            "current": (
                "temperature_2m,"
                "apparent_temperature,"
                "relative_humidity_2m,"
                "precipitation,"
                "weather_code,"
                "wind_speed_10m,"
                "wind_direction_10m,"
                "is_day"
            ),
            "daily": (
                "weather_code,"
                "temperature_2m_max,"
                "temperature_2m_min,"
                "precipitation_probability_max,"
                "uv_index_max,"
                "sunrise,"
                "sunset"
            ),
        },
        timeout=10,
    )

    response.raise_for_status()

    data = response.json()

    current = data["current"]
    daily = data["daily"]
    icon_name = get_weather_icon(current["weather_code"], bool(current["is_day"]))

    current_weather = {
        "temperature": current["temperature_2m"],
        "feels_like": current["apparent_temperature"],
        "condition": WEATHER_CODES.get(
            current["weather_code"],
            "Unknown",
        ),
        "icon_path": f"icons/weather/{icon_name}.svg",
        "humidity": current["relative_humidity_2m"],
        "precipitation": current["precipitation"],
        "wind_speed": current["wind_speed_10m"],
        "wind_direction": current["wind_direction_10m"],
        "is_day": bool(current["is_day"]),
    }

    forecast = [
        {
            "date": daily["time"][i],
            "condition": WEATHER_CODES.get(
                daily["weather_code"][i],
                "Unknown",
            ),
            "icon_path": f"icons/weather/{get_weather_icon(daily['weather_code'][i], True)}.svg",
            "max_temperature": daily["temperature_2m_max"][i],
            "min_temperature": daily["temperature_2m_min"][i],
            "rain_probability": daily["precipitation_probability_max"][i],
            "uv_index": daily["uv_index_max"][i],
            "sunrise": daily["sunrise"][i],
            "sunset": daily["sunset"][i],
        }
        for i in range(1, len(daily["time"]))
    ]

    return {
        "current": current_weather,
        "forecast": forecast,
        "advisory": generate_travel_advisory(current_weather, forecast),
    }
