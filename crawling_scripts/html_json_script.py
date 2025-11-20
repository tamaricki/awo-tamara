
import re
import time
from pathlib import Path
from random import uniform
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse
import json
from datetime import datetime 
import pandas as pd
import requests
from bs4 import BeautifulSoup
from scraping_utils import fetch_webpage, extract_impressum_data

DEFAULT_CONFIG = {
    'user_agent': 'AWO-Research-Bot/1.0 (Research project; contact@awo.org)',
    'delay_min': 1.0,
    'delay_max': 3.0,
    'timeout': 10,
    'max_retries': 3,
}

HEADERS = {"User-Agent": "Mozilla/5.0 (AWO-Crawler/1.2)"}

PAGE_SITE_CONFIG = {
    'Brandenburg': {
        'target_url': ['https://www.awo-barnim.de/index.php/angebote/senioren/tagespflege', 
                        'https://www.awo-barnim.de/index.php/angebote/senioren/ambulante-pflege',
                        'https://awo-brandenburg-havel.de/unsere-angebote/kinder-und-jugendhilfe/kindertagesstaetten',
                        'https://awo-brandenburg-havel.de/unsere-angebote/seniorenhilfe/wohnen-mit-service', 'https://awo-uckermark.de/index.php/kreisverband/gesellschaften',
                        'https://awo-fuewa.de/ortsvereine/', 'https://awo-fuewa.de/angebote/', 'https://awo-fuewa.de/kita/'],
        'base_url': 'https://awo-lag-brandenburg.de/de/impressum/',
        'page_with_links': True,
        'page_with_contacts': False
    },
    'Brandenburg - contacts': {
        'target_url': ['https://www.awo-barnim.de/angebote/ortsvereine/arbeiterwohlfahrt-ortsverein-finow-e-v',
                        'https://www.awo-barnim.de/angebote/ortsvereine/arbeiterwohlfahrt-ortsverein-eberswalde-e-v',
                        'https://www.awo-barnim.de/angebote/ortsvereine/arbeiterwohlfahrt-ortsverein-bernau-e-v',
                        'https://www.awo-barnim.de/angebote/ortsvereine/arbeiterwohlfahrt-ortsverein-wandlitz-e-v',
                        'https://www.awo-barnim.de/angebote/ortsvereine/arbeiterwohlfahrt-ortsverein-basdorf-e-v',
                        'https://www.awo-barnim.de/angebote/ortsvereine/arbeiterwohlfahrt-ortsverein-zepernick-e-v',
                        'https://awo-brandenburg-havel.de/unsere-angebote/kinder-und-jugendhilfe/hilfen-zur-erziehung',
                        'https://awo-brandenburg-havel.de/unsere-angebote/seniorenhilfe/teilstationaere-pflege-tagespflege',
                        'https://awo-brandenburg-havel.de/unsere-angebote/seniorenhilfe/ambulante-pflege-sozialstation',
                        'https://awo-brandenburg-havel.de/unsere-angebote/seniorenhilfe/vollstationaere-pflege-am-wasserturm',
                        'https://awo-uckermark.de/index.php/kreisverband/ortsvereine', 'https://www.awomol.de/Gliederungen-738327.html',
                        'https://www.awomol.de/Einrichtungen-871712.html?src8717168=0#src8717168', 'https://www.awomol.de/Gliederungen-738327.html ',
                        'https://www.awo-opr.de/Einrichtungen-1014357.html','https://www.awomol.de/Altenhilfe-Pflege-und-Senioren-738370.html',
                        'https://www.awo-kv-ff.de/kreisverband','https://www.awo-strausberg.de/',
                        'https://www.awo-bb-sued.de/de/topic/56.einrichtung.html?id=25',
                    'https://www.awo-bb-sued.de/de/topic/56.einrichtung.html?id=26' ],
        'base_url': 'https://awo-lag-brandenburg.de/de/impressum/',
        'page_with_contacts': True,
        'page_with_links': False
    },
    'Brandenburg - Sued' : {
        'target_url': ['https://www.awo-bb-sued.de/de/topic/25.besondere-wohnformen.html','https://www.awo-bb-sued.de/de/topic/27.angebote-der-tagesstruktur.html',
                    'https://www.awo-bb-sued.de/de/topic/24.wohnen-mit-assistenz.html',
                    'https://www.awo-bb-sued.de/de/topic/28.beratungs-und-kontaktangebote.html',
                    'https://www.awo-bb-sued.de/de/topic/26.werkstatt-f%C3%BCr-menschen-mit-behinderungen.html',
                    'https://www.awo-bb-sued.de/de/topic/75.erziehungs-und-familienberatung.html',
                    'https://www.awo-bb-sued.de/de/topic/33.h%C3%B6rbehinderung.html',
                    'https://www.awo-bb-sued.de/de/topic/32.migration.html',
                    'https://www.awo-bb-sued.de/de/topic/30.schulden.html',
                    'https://www.awo-bb-sued.de/de/topic/7.schwangerenberatung.html',
                    'https://www.awo-bb-sued.de/de/topic/85.wohnungslosigkeit.html',
                    'https://www.awo-bb-sued.de/de/topic/35.begegnungsst%C3%A4tten.html',
                    'https://www.awo-bb-sued.de/de/topic/36.senioren.html'
                    ],
        'base_url': 'www.awo-bb-sued.de',
        'page_with_contacts': False,
        'page_with_links': True,
    },
    'Brandenburg - Potsdam':{
        'target_url': ['https://awo-potsdam.de/de/ortsvereine/', 'https://awo-potsdam.de/de/einrichtungen/'],
        'base_url': 'https://awo-potsdam.de',
        'page_with_contacts': False,
        'page_with_links': True
     },
    'Hessen - Sued': {
        'target_url' : ['https://www.awo-hs.org/sitemap'],
        'base_url': 'https://awo-hs.org',
        'page_with_contacts': False,
        'page_with_links': True
    },
    'Hessen - Nord' : {
        'target_url' : ['https://www.awo-nordhessen.de/sitemap'],
        'base_url' : 'https://www.awo-nordhessen.de',
        'page_with_contacts': False,
        'page_with_links': True
    },
    'Sachsen-Anhalt' : {
        'target_url':['https://www.awo-sachsenanhalt.de/awo-landesverband/mitglieder', 'https://www.awo-sachsenanhalt.de/landesverband/mitmachen/awo-ehrenamtsakademie/ehrenamtsdatenbank'],
        'base_url' : 'https://www:awo-sachsenanhalt.de',
        'page_with_contacts': True,
        'page_with_links': False
    },
    'Niedersachsen' : {
        'target_url': ['https://awo-bs.de/sitemap/',  
                        'https://awo-ol.de/meine-awo-karriere/awo-weser-ems/standorte-leistungen'],
        'base_url': 'https://awonds.de/index.php/awo-niedersachsen/ueber-uns',
        'page_with_contacts': False,
        'page_with_links': True
    },
    'Niedersachsen - Hannover' : {
        'target_url': ['https://www.awo-hannover.de/sitemap/'],
        'base_url' : 'https://www.awo-hannover.de/impressum/',
        'page_attribute': 'simple-sitemap-page main'
    },
    'Niedersachsen - contacts': {
        'target_url': ['https://awo-ol.de/meine-awo-karriere/awo-weser-ems/kreisverbaende',
                        'https://awo-ol.de/pflege-wohnen-teilhabe-begegnung/pflege-wohnen/junges-wohnen',
                        'https://awo-ol.de/pflege-wohnen-teilhabe-begegnung/pflege-wohnen/tagespflege-am-zwischenahner-meer',
                        'https://awo-ol.de/pflege-wohnen-teilhabe-begegnung/soziale-teilhabe-wohnen-assistenz/psychosoziale-assistenz-assistenz-beim-wohnen',
                        'https://jw-weser-ems.de/kontaktformular/impressum/',
                        'https://awo-ol.de/sprache-foerderung-betreuung-hilfe/kindertagesbetreuung/krippen/kinderkrippe-grashuepfer-ol',
                        'https://awo-ol.de/sprache-foerderung-betreuung-hilfe/jugendhilfe/awo-angebot-fuer-jugendliche-erststraftaeter-shift',
                        'https://awo-ol.de/sprache-foerderung-betreuung-hilfe/kur-reha-therapie/mutter-kind-klinik-lotte-lemke-haus',
                        'https://awo-ol.de/sprache-foerderung-betreuung-hilfe/kur-reha-therapie/rehaklinik-fuer-kinder-und-jugendliche-mit-kommunikationsstoerung-werscherberg',
                        'https://awo-ol.de/sprache-foerderung-betreuung-hilfe/kur-reha-therapie/suchttherapie/awo-suchtberatung-und-behandlung',
                        'https://awo-ol.de/beratung-service/beratung/beratungs-und-therapiezentrum-leer',
                        'https://awo-ol.de/beratung-service/beratung/sozialberatung-fuer-unternehmen-awo-lifebalance'],
        'base_url': 'https://awonds.de/index.php/awo-niedersachsen/ueber-uns',
        'page_with_contacts': True,
        'page_with_links': False
    },
    'Bremen':{
        'target_url' : ['https://awo-bremen.de/kinder-jugend-familie-frauen/jugend/jugendfreizeiteinrichtungen', 'https://awo-bremen.de/pflege-service-fuer-aeltere/pflegeeinrichtungen', 
                        'https://awo-bremen.de/sucht-psychiatrie-behindertenhilfe/menschen-mit-suchterkrankungen/wohneinrichtungen', 
                        'https://awo-bremen.de/sucht-psychiatrie-behindertenhilfe/menschen-mit-psychischen-erkrankungen/wohneinrichtungen',
                        'https://awo-bremen.de/sucht-psychiatrie-behindertenhilfe/menschen-mit-geistigen-beeintraechtigungen/wohneinrichtungen-fuer-menschen-mit-geistigen-beeintraechtigungen'],
        'base_url': 'https://awo-bremen.de/wir-ueber-uns/wer-wir-sind/awo-kreisverband-ortsvereine',
        'page_with_contacts': False,
        'page_with_links': True
    },
    'Schleswig-Holstein' : {
        'target_url' : ['https://www.awo-sh.de/awo-ortsvereine-kreisverbaende', 'https://awo-kreisverband-lauenburg.de/unsere-ortsvereine',
                        'https://awo-ostholstein.de/unsere-ortsvereine', 'https://www.awo-segeberg.de/','https://www.awo-kiel.de/angebote/kindertagesbetreuung/kindertagespflege.html',
                        'https://www.awo-neumuenster.de/', 'https://www.awo-sh.de/fachzentrum-fuer-suchtfragen-luebeck', 'https://www.awo-sh.de/fruehe-hilfen-kuecknitz'],
        'base_url': 'https://awo-sh.de/ueber-uns/impressum/',
        'page_with_contacts': True,
        'page_with_links': False
    },
    'Schleswig-Holstein - links': {
        'target_url' : ['https://www.awo-dithmarschen.de/ortsvereine', 'https://www.awo-kiel.de/angebote/kindertagesbetreuung/kinderhaeuser.html',
                        'https://awo-pflege-sh.de/einrichtungen', 'https://www.awo-bildungundarbeit.de/standorte', 'https://awo-kreisverband-pinneberg.de/kindertagesstaetten',
                        'https://awo-kreisverband-pinneberg.de/sozialkaufhaeuser', 'https://awo-kreisverband-pinneberg.de/pflege', 'https://awo-kreisverband-pinneberg.de/psychosoziale-dienste',
                        'https://awo-jugendwerk.com/kontaktform/','https://www.awo-stormarn.de/ortsvereine1', 'https://www.awo-segeberg.de/'],
        'base_url': 'https://awo-sh.de/ueber-uns/impressum/',
        'page_with_contacts': False,
        'page_with_links': True
    },
    'NRW': {
        'target_url' : ['https://www.awo-mittelrhein.de/de/awo/ueber-uns/awo-in-der-region/kreisverbaende-regionalverband-ortsvereine/',
                        'https://www.awo-hs.de/wir-sind-awo/ortsvereine/', 'https://www.awo-bm-eu.de/awo-direkt/ueber-uns/awo-in-der-region/ortsvereine' ],
        'base_url': 'https://awo-nrw.de/',
        'page_with_contacts': True,
        'page_with_links': False
        },
    'NRW - Links': {
        'target_url' : ['https://awo-dn.de/awo-ortsvereine/', 'https://awo-koeln.de/awo-ortsvereine-stuetzpunkte/', 'https://www.awo-rhein-oberberg.de/awo/awo-ortsvereine/'],
        'base_url': 'https://awo-nrw.de/',
        'page_with_contacts': False,
        'page_with_links': True
    },
    'Mecklenburg-Vorpommern': {
        'target_url' : ['https://www.awo-demmin.de/ortsvereine.html', 'https://www.awo-demmin.de/cafe-der-vielfalt.html', 'https://www.awo-spatzenschule-neukalen.de/',
                        'https://www.awo-demmin.de/beratung-betreuung.html', 'https://www.awo-mueritz.de/einrichtungen-angebote/einrichtungen-fuer-kinder-und-jugendliche/unsere-kindertagesstaetten/',
                        'https://www.awo-mueritz.de/einrichtungen-angebote/einrichtungen-fuer-kinder-und-jugendliche/peeneschule-gross-gievitz/', 'https://www.awo-mueritz.de/einrichtungen-angebote/einrichtungen-fuer-kinder-und-jugendliche/schullandheim/',
                        'https://www.awogue.de/index.php/kreisverband-2/awo-ortsverein-guestrow',
                        'https://www.awo-mst.de/altenpflegeheim/', 'https://www.awo-mst.de/ambulanter-pflegedienst/ambulanter-pflegedienst-neustrelitz/',
                        'https://www.awo-mst.de/ambulanter-pflegedienst/ambulanter-pflegedienst-woldegk/',
                        'https://www.awo-mst.de/wohngemeinschaft-neustrelitz/senioren-wohngemeinschaften-in-woldegk/',
                        'https://www.awo-mst.de/pc-werkstatt-chib/', 'https://www.awo-mst.de/eingliederungshilfe/',
                        'https://www.awo-mst.de/wohnheim-petersdorf/', 'https://www.awo-mst.de/mobile-fruehfoerderung/',
                        'https://www.awo-mst.de/kita/kita-schoenbeck/','https://www.awo-mst.de/kita/kita-woldegk/',
                        'https://www.awo-mst.de/neubau-der-awo-kita-in-woldegk/', 'https://www.awo-mst.de/wohngruppen-jugendliche/wohngruppe-neubrandenburg/',
                        ''],
        'base_url': 'https://awo-mv.de/impressum/',
        'page_with_contacts': True,
        'page_with_links': False
    },
    'Mecklenburg-Vorpommern - links': {
        'target_url' : ['https://www.awo-vorpommern.de/die-awo-vorpommern-wer-wir-sind/einrichtungen.html', 'https://awo-nbovp.de/index.php/bereiche/kindertageseinrichtungen/kindertagesstaetten',
                        'https://awo-nbovp.de/index.php/bereiche/kindertageseinrichtungen/hort', 'https://www.awo-demmin.de/kinder-jugendliche/kitas.html',
                        'https://www.awo-demmin.de/kinder-jugendliche/kinder-und-jugendfreizeitzentren.html', 'https://www.awo-demmin.de/kinder-jugendliche/schulsozialarbeit.html',
                        'https://www.awo-demmin.de/kinder-jugendliche/schulsozialarbeit.html', 'https://www.awo-demmin.de/pflege/tagespflege.html',
                        'https://www.awo-demmin.de/pflege/pflegedienst.html', 'https://www.awo-demmin.de/pflege/wohngemeinschaft.html', 'https://www.awo-demmin.de/pflege/betreutes-wohnen.html',
                        'https://www.awo-demmin.de/integration/inklusionsbetriebe-kopie.html', 'https://www.awo-demmin.de/integration/zentrum-fuer-eingliederungshilfe-kopie.html',
                        'https://awo-vg.de/wp-sitemap-posts-page-1.xml', 'https://www.awo-mst.de/page-sitemap.xml', 'https://www.awo-mueritz.de/wp-sitemap-posts-page-1.xml',
                        'https://www.awo-mst.de/wohngemeinschaft-neustrelitz/','https://www.awo-mst.de/begegnungsstatten/'],
        'base_url': 'https://awo-mv.de/impressum/',
        'page_with_contacts': False,
        'page_with_links': True
    },
    'Rheinland-Pfalz': {
        'target_url': ['https://awo-rheinland.de/page-sitemap.xml'],
        'base_url': 'https://awo-rheinland.de/impressum/',   
        'page_with_contacts': False,
        'page_with_links': True
    },
    'Berlin': {
        'target_url' : ['https://www.awoberlin.de/wer-wir-sind/awo-in-berlin/'],
        'base_url': 'https://www.awoberlin.de/impressum/',
        'page_with_contacts': True,
        'page_with_links': False
    }
} 

def get_urls_by_config(config_key) -> list:
    """
    Retrieves URLs from PAGE_SITE_CONFIG based on a specific configuration key.
    """
    urls = []
    for bundesland, config in PAGE_SITE_CONFIG.items():
        if config.get(config_key, False):
            urls.extend(config.get('target_url', []))
    return urls

def get_page_attribute_by_url(url):
    for region, data in PAGE_SITE_CONFIG.items():
        for t in data['target_url']:
            if t==url:
                #url.startswith(t.rstrip("/")):
                return  data['page_attribute']    
    return None



sites_with_links = get_urls_by_config('page_with_links') 
sites_with_contacts = get_urls_by_config('page_with_contacts')
sites_with_page_attribute = get_urls_by_config('page_attribute')



html_text_data = []
for l in sites_with_links:
    html_text_data.append(fetch_webpage(l))
for s in sites_with_contacts:
    html_text_data.append(fetch_webpage(s))
for p in sites_with_page_attribute:
    html_text_data.append(fetch_webpage(p))

OUT_DIR = Path("./raw_html_text")
OUT_DIR.mkdir(parents=True, exist_ok=True)

output_file = OUT_DIR / f"results_html_text_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
print(len(html_text_data))

try:
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(html_text_data, f, ensure_ascii=False, indent=2)
        print(f"\n Extraction complete. Saved {len(html_text_data)} entries to {output_file.name}")
except Exception as e:
    print(f" Failed to write JSON: {e}") 