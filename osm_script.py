
import requests
import csv
import time
import pandas as pd

#AWO associations are fetched with help of OSM overpass API. Since API gets easily overloaded (504 Gateway Timeout) , 
# search is done on region level, and not for whole country. Smaller regions are grouped together
# script contains delays between requests and retry loops due to frequest time-out errors. 
# in query are given filters on node way level to narrow the results down. 



BUNDES_GROUPS = [
    ["Baden-Württemberg"],
    ["Bayern"],
    ["Berlin", "Bremen"],
    ["Brandenburg","Hamburg"],
    ["Hessen","Mecklenburg-Vorpommern","Rheinland-Pfalz"],
    ["Niedersachsen"],
    ["Nordrhein-Westfalen"],
    ["Saarland","Sachsen","Sachsen-Anhalt", "Schleswig-Holstein","Thüringen"]
]

def fetch_osm_region(region_name:str) -> list: 
    """Fetch AWO/Arbeiterwohlfahrt entries from Overpass for a single region."""
    query = f"""[out:json][timeout:180];
            area["name"="{region_name}"]->.searchArea;
            (
            node["name"~"(AWO|Arbeiterwohlfahrt)",i](area.searchArea);
            way["name"~"(AWO|Arbeiterwohlfahrt)",i](area.searchArea);
            relation["name"~"(AWO|Arbeiterwohlfahrt)",i](area.searchArea);

                node(area.searchArea)["operator"~"(AWO|Arbeiterwohlfahrt)",i];
                way(area.searchArea)["operator"~"(AWO|Arbeiterwohlfahrt)",i];
                relation(area.searchArea)["operator"~"(AWO|Arbeiterwohlfahrt)",i];

                node(area.searchArea)["brand"~"(AWO|Arbeiterwohlfahrt)",i];
                way(area.searchArea)["brand"~"(AWO|Arbeiterwohlfahrt)",i];
                relation(area.searchArea)["brand"~"(AWO|Arbeiterwohlfahrt)",i];

                );
                out center;
             """
    main_overpass_api = "https://overpass-api.de/api/interpreter"
    for attempt in range(3):
        try:
            response=requests.get(main_overpass_api, params={'data':query}, timeout=100) 
            response.raise_for_status()
            result = response.json()
        except Exception as e:
            print(f"Error for {region_name}, {e}. Retry {attempt+1}")
            return []  
        time.sleep(10)   
    r=[]
    for el in result.get("elements", []):
        tags=el.get("tags", {})
        r.append({
                "osm_id": el.get("id"),
                "region": region_name,
                "type": el.get("type"),
                "name": tags.get("name", ""),
                "street": tags.get("addr:street", ""),
                "housenumber": tags.get("addr:housenumber", ""),
                "postcode": tags.get("addr:postcode", ""),
                "city": tags.get("addr:city", ""),
                "lat": el.get("lat") or el.get("center", {}).get("lat"),
                "lon": el.get("lon") or el.get("center", {}).get("lon"),
                "phone": tags.get("contact:phone", tags.get("phone", "")),
                "email": tags.get("contact:email", tags.get("email", "")),
                "website": tags.get("contact:website", tags.get("website", "")),
                "amenity": tags.get("amenity", "")
                })
    return r

def osm_extractor_groups(nested_list: list, delay: int=10) ->pd.DataFrame:
    """Loop over groups of regions and fetch results into one DataFrame."""
    all_results=[] 
    for group in nested_list:
        for region in group:
            rows = fetch_osm_region(region)
            all_results.extend(rows)
            time.sleep(delay)
    return pd.DataFrame(all_results)



# for running it standalone  : 
if __name__=="__main__":
    name_datetime = time.strftime("%Y%m%d-%H%M%S")
    df=osm_extractor_groups(BUNDES_GROUPS)
    df.to_csv(f"awo_{name_datetime}_osmscript.csv", index=False, encoding='utf-8')
    print(f'Saved {len(df)} results total')
