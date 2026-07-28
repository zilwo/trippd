from ai.place_agent import get_place_chat_agent, get_place_info_agent


def generate_place_info(place_details):
    types = ", ".join(place_details.get("types", []))

    prompt = f"""
    Generate travel information for this place.

    Name: {place_details["name"]}
    Address: {place_details["address"]}
    Latitude: {place_details["latitude"]}
    Longitude: {place_details["longitude"]}
    Types: {types}
    If important facts are missing, don't guess.
    """

    result = get_place_info_agent().run_sync(prompt)
    print(len(result.all_messages()), "this")

    return result.output


def generate_place_chat_response(place, question):
    prompt = f"""
    Place: {place.name}
    Address:{place.address}
    Latitude: {place.latitude}
    Longitude: {place.longitude}
    Description:{place.description}
    Highlights:{place.highlights}
    Best for:{place.best_for}
    Best time to visit:{place.best_time_to_visit}
    User question:{question}
    """

    result = get_place_chat_agent().run_sync(prompt)
    return result.output
