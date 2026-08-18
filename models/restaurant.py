from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class Restaurant:
    place_id: str
    name: str
    rating: Optional[float] = None
    review_count: int = 0
    address: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    maps_url: Optional[str] = None
    price_level: Optional[str] = None
    categories: List[str] = field(default_factory=list)
    opening_status: Optional[str] = None
    opening_hours: List[str] = field(default_factory=list)
    photo_url: Optional[str] = None
    distance_miles: Optional[float] = None
    rank_score: Optional[float] = None
    cuisine_labels: List[str] = field(default_factory=list)
