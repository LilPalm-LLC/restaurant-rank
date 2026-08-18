import requests
import streamlit as st
from models.location import Location
from services.google_places import require_key

ENDPOINT="https://maps.googleapis.com/maps/api/geocode/json"

@st.cache_data(ttl=3600, show_spinner=False)
def geocode(query:str):
    key=require_key(); r=requests.get(ENDPOINT,params={"address":query,"key":key},timeout=15)
    if r.status_code>=400: raise RuntimeError(f"Geocoding request failed ({r.status_code}).")
    data=r.json()
    if data.get("status") not in ("OK","ZERO_RESULTS"): raise RuntimeError("Geocoding service returned an error.")
    results=data.get("results",[])
    if not results:return []
    locations=[to_location(x,query) for x in results[:5]]
    return locations

def to_location(x,query):
    comps={}
    for c in x.get("address_components",[]):
        for t in c.get("types",[]): comps.setdefault(t,c.get("long_name"))
    loc=x.get("geometry",{}).get("location",{})
    return Location(query=query,formatted_address=x.get("formatted_address",query),latitude=loc.get("lat"),longitude=loc.get("lng"),country=comps.get("country"),region=comps.get("administrative_area_level_1"),county=comps.get("administrative_area_level_2"),municipality=comps.get("administrative_area_level_3"),district=comps.get("administrative_area_level_4"),city=comps.get("locality") or comps.get("postal_town"),neighborhood=comps.get("neighborhood") or comps.get("sublocality"),postal_code=comps.get("postal_code"))
