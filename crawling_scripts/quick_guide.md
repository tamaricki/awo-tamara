### Idea 

Basis for scraping AWO regional comes as result of investigating AWO websites links and identifying pages which have contact information, like for instance :
 - AWO Regional websites having listed contacts and links of their district, subdistrict, local, associations and facilities
 - AWO regional websites having pdf/jpeg documents about services they offer and contacts of related associations and facilities
 - AWO regional associations having sitemaps with links to their facilities and associations. 
 
All those pages are listed in  **AWO_central_regional_links**.  Depending on type how is needed information stored, 3 scripts are developed:

1. Crawler for getting info from sites having list with pagination and out of pdf/jpeg documents on site. Each site has defined tag and attribute for extracting the info
2. Crawler for extracting links and contacts from standard web pages and sitemaps. Each page is either having links for text is extraction or it is page having contact(s). 

Output of both crawlers is .json document having region name, link and extracted text. This json file is input for contact_extractor_app, LLM which takes text and extracts out of it contact information in .json and .csv format.  

Besides two crawlers there is 3rd one for pages which require selenium or for extracting js. This one extracts contact information in .csv format and no further processing is needed. 

## Quickstart

Besides creating venv and  installing libraries from requirements.txt (steps in QUICKSTART), you need to install huggingface_hub. 
```bash 
pip  install huggingface_hub
```
For using Hugging Face you need to open an account and  before using the Hugging Face API, you must authenticate with your API key. You can obtain your API key by following these steps:

 - Go to your Hugging Face account.
 - Navigate to Settings > Tokens, create a new token with read access and copy the token.

Inference Client is initialised by passing the API token: 

```python
from huggingface_hub import InferenceClient

client = InferenceClient(token="YOUR_API_KEY")
```
Script `contact_extractor_app.py` uses Llama-3.1-8B-Instruct model but it is possible to try different models. For more info, start with following guide: [Hugging Face first api call](https://huggingface.co/docs/inference-providers/en/guides/first-api-call).  

