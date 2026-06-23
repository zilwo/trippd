def format_delta(delta, trip_type=None):
    days = delta.days
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60

    if trip_type == "trip":
        parts = []

        if days:
            parts.append(f"{days} day{'s' if days != 1 else ''}")

        if hours:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")

        return " ".join(parts)

    if days:
        return f"{days} day{'s' if days != 1 else ''}"

    if hours:
        return f"{hours}h {minutes}m"

    return f"{minutes}m"
