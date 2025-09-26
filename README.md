## Different Approaches of Getting Publicly Awavilable Data

**osm_ script** uses OSM overpass API to get locations information like region, name, address, zip code, phone, email, website from OSM. 
Since API gets easily overloaded (504 Gateway Timeout) , search is done on region level, and not for whole country. Smaller regions are grouped together. Also script contains delays between requests and retry loops due to frequest time-out errors. 

### References: 

Good examples how to create query: https://wiki.openstreetmap.org/wiki/Overpass_API/Overpass_API_by_Example 
Guide: https://wiki.openstreetmap.org/wiki/Overpass_API/Language_Guide
quick Start: https://wiki.openstreetmap.org/wiki/Overpass_API 




