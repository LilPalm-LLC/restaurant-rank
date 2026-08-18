from utils.distance import haversine_miles, miles_to_km

def test_distance_zero(): assert haversine_miles(0,0,0,0)==0

def test_km(): assert round(miles_to_km(1),3)==1.609
