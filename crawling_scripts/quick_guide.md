### Overview

This project scrapes contact information from AWO regional websites.
During analysis of the AWO online landscape, three major patterns were identified:

1. Regional AWO websites that list their district / subdistrict / local associations and facilities on regular HTML pages with pagination.

2. Regional AWO websites that provide information through downloadable documents (PDF/JPEG) containing addresses and contacts.

3. AWO associations with sitemaps, where all facility links can be extracted from XML or HTML sitemap pages.
 
All known entry points are stored in [**AWO_central_regional_links**](https://github.com/dssg-berlin/awo-scraping-nlp-project/blob/scrape-awo-regional-sites/regions_urls/AWO_central_regional_links.xlsx).  Depending on how each AWO region structures its content, the project uses three types of crawlers.

### Crawlers

1. **Crawler for List Pages + PDF/JPEG Extraction**

Used when a regional website displays:

- lists of facilities with pagination
- or provides downloadable documents (PDF, JPEG) containing contact details

Each site has a defined tag/attribute indicating where contact information is stored.

2. **Crawler for Standard Web Pages + Sitemaps**

Used for:

- classical HTML pages containing contact details
- XML/HTML sitemaps listing all facility links

The crawler detects if a page contains contact info directly or if links need to be followed.

**Output of both crawlers:**
A JSON file containing:

- region name
- link
- extracted text

This JSON is the input for the LLM-based contact extractor.

3. Selenium / JavaScript Crawler

Used only for websites requiring:

- JavaScript execution
- dynamic content loading (XHR)

This crawler directly outputs contact data as CSV, with no further LLM processing required.

### Contact Extractor LLM

The Script `contact_extractor_app.py` Hugging Face LLM (Llama-3.1-8B-Instruct) to extract structured information from raw text:

- addresses
- phone numbers
- email addresses
- facility names
- additional metadata

Outputs are:

- JSON
- CSV
You can test other models easily (See Hugging Face docs)

### Quickstart

Besides creating venv and  installing libraries from requirements.txt (see steps in QUICKSTART), install  huggingface_hub. 

```bash 
pip  install huggingface_hub

```
then:
- Create an account on Hugging Face
- Go to **Setings -> Tokens**
- Create a token with read permissions
- Pass it into the inference client:

```python
from huggingface_hub import InferenceClient

client = InferenceClient(token="YOUR_API_KEY")
```
For learning more, start here: [Hugging Face first api call](https://huggingface.co/docs/inference-providers/en/guides/first-api-call).  

