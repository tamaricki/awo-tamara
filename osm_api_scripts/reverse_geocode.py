
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

#This code uses Nominatim (geocoder behind OSM) to reverse-geocode latitute/longitude into street,city, postcode, etc
#it should be applied on dataframe having only lat/long values



def geocode_lat_lon(lat, lon):
    geolocator = Nominatim(user_agent="awo_extractor")
    geocode = RateLimiter(geolocator.reverse, min_delay_seconds=1)
    try:
        location=geocode((lat,lon), language='de', addressdetails=True)
        if location and location.raw.get("address"):
            addr=location.raw["address"]
            return {
                "postcode": addr.get("postcode", ""),
                "city": addr.get("town") or addr.get("city") or addr.get("village") or "",
                "street": addr.get("road", ""),
                "housenumber": addr.get("house_number", "")
            }
    except Exception as e:
        print("Error:", e)
        return {"postcode": "", "city": "", "street": "", "housenumber": ""}


