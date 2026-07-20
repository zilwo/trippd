from .models import Activity

GOOGLE_PRIMARY_TYPES = {
    Activity.Category.FOOD: [
        "restaurant",
        "cafe",
        "bakery",
        "ice_cream_shop",
        "fast_food_restaurant",
    ],
    Activity.Category.SIGHTSEEING: [
        "tourist_attraction",
        "museum",
        "art_gallery",
        "historical_place",
        "monument",
    ],
    Activity.Category.NATURE: [
        "park",
        "beach",
        "botanical_garden",
        "nature_preserve",
    ],
    Activity.Category.SHOPPING: [
        "shopping_mall",
        "department_store",
        "supermarket",
        "clothing_store",
    ],
    Activity.Category.ENTERTAINMENT: [
        "movie_theater",
        "amusement_park",
        "bowling_alley",
        "aquarium",
        "zoo",
    ],
    Activity.Category.SPORTS: [
        "gym",
        "sports_complex",
        "stadium",
        "swimming_pool",
    ],
    Activity.Category.NIGHTLIFE: [
        "bar",
        "night_club",
    ],
    Activity.Category.RELAXATION: [
        "spa",
    ],
    Activity.Category.STAY: [
        "hotel",
        "resort_hotel",
        "hostel",
    ],
}
