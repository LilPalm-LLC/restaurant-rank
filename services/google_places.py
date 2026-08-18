import os, requests
import streamlit as st
from models.restaurant import Restaurant
from utils.cuisine import normalize_many
from utils.distance import haversine_miles

BASE="https://places.googleapis.com/v1/places:searchText"
DETAILS="https://places.googleapis.com/v1/places/{}"

def api_key():
    try:return st.secrets.get("GOOGLE_MAPS_API_KEY") or os.environ.get("GOOGLE_MAPS_API_KEY")
    except Exception:return os.environ.get("GOOGLE_MAPS_API_KEY")

def require_key():
    key=api_key()
    if not key: raise RuntimeError("GOOGLE_MAPS_API_KEY is not configured.")
    return key

def _headers(key,mask): return {"Content-Type":"application/json","X-Goog-Api-Key":key,"X-Goog-FieldMask":mask}

@st.cache_data(ttl=900, show_spinner=False)
def text_search(text:str,lat:float|None=None,lon:float|None=None,radius_m:float=8046.72,max_results:int=20):
    key=require_key()
    body={"textQuery":text,"pageSize":min(max_results,20),"languageCode":"en"}
    if lat is not None and lon is not None:
        body["locationBias"]={"circle":{"center":{"latitude":lat,"longitude":lon},"radius":float(radius_m)}}
    mask="places.id,places.displayName,places.formattedAddress,places.location,places.rating,places.userRatingCount,places.priceLevel,places.primaryType,places.types,places.googleMapsUri,places.nationalPhoneNumber,places.websiteUri,places.currentOpeningHours,places.photos,places.shortFormattedAddress"
    r=requests.post(BASE,headers=_headers(key,mask),json=body,timeout=18)
    if r.status_code>=400: raise RuntimeError(f"Google Places request failed ({r.status_code}).")
    out=[]
    for p in r.json().get("places",[]): out.append(place_to_restaurant(p,lat,lon))
    return out

def place_to_restaurant(p,lat0=None,lon0=None):
    loc=p.get("location") or {}; lat=loc.get("latitude"); lon=loc.get("longitude")
    types=p.get("types") or []
    cats=[t.replace("_"," ").title() for t in types]
    price_map={"PRICE_LEVEL_FREE":"$0","PRICE_LEVEL_INEXPENSIVE":"$","PRICE_LEVEL_MODERATE":"$$","PRICE_LEVEL_EXPENSIVE":"$$$","PRICE_LEVEL_VERY_EXPENSIVE":"$$$$"}
    ph=None
    photos=p.get("photos") or []
    if photos:
        ref=photos[0].get("name")
        # Photo endpoint construction is handled lazily in get_photo_url.
        ph=ref
    hours=p.get("currentOpeningHours") or {}
    opening_status=("Open now" if hours.get("openNow") is True else "Closed" if "openNow" in hours else None)
    r=Restaurant(place_id=p.get("id",""),name=(p.get("displayName") or {}).get("text","Unknown restaurant"),rating=p.get("rating"),review_count=p.get("userRatingCount",0),address=p.get("formattedAddress", ""),latitude=lat,longitude=lon,phone=p.get("nationalPhoneNumber"),website=p.get("websiteUri"),maps_url=p.get("googleMapsUri"),price_level=price_map.get(p.get("priceLevel")),categories=cats,opening_status=opening_status,opening_hours=hours.get("weekdayDescriptions") or [],photo_url=ph)
    if lat0 is not None and lon0 is not None and lat is not None and lon is not None:r.distance_miles=haversine_miles(lat0,lon0,lat,lon)
    return r

@st.cache_data(ttl=1800, show_spinner=False)
def get_place_details(place_id:str):
    key=require_key(); mask="id,displayName,formattedAddress,location,rating,userRatingCount,priceLevel,types,googleMapsUri,nationalPhoneNumber,websiteUri,currentOpeningHours,photos"
    r=requests.get(DETAILS.format(place_id),headers=_headers(key,mask),timeout=18)
    if r.status_code>=400: raise RuntimeError(f"Google Place details failed ({r.status_code}).")
    return place_to_restaurant(r.json())

@st.cache_data(ttl=3600, show_spinner=False)
def photo_bytes(photo_name:str, max_width:int=700):
    key=require_key()
    if not photo_name:return None
    url=f"https://places.googleapis.com/v1/{photo_name}/media"
    r=requests.get(url,headers={"X-Goog-Api-Key":key},params={"maxWidthPx":max_width},timeout=18)
    if r.status_code>=400:return None
    return r.content
