from pydantic import BaseModel


class PlaceDetails(BaseModel):
    summary: str
    highlight: str
    best_time_to_visit: str
    best_for: list[str]
