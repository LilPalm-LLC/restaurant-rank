from math import asin, cos, radians, sin, sqrt

def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 3958.7613
    dlat = radians(lat2-lat1); dlon = radians(lon2-lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    return 2*r*asin(sqrt(a))

def miles_to_km(miles: float) -> float:
    return miles * 1.609344

def format_distance(miles: float | None, unit: str = "miles") -> str:
    if miles is None: return ""
    if unit == "kilometers": return f"{miles_to_km(miles):.1f} km"
    return f"{miles:.1f} mi"
