from dataclasses import dataclass
from typing import Optional

@dataclass
class Location:
    query: str
    formatted_address: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    country: Optional[str] = None
    region: Optional[str] = None
    county: Optional[str] = None
    municipality: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    neighborhood: Optional[str] = None
    postal_code: Optional[str] = None
    ambiguous: bool = False
