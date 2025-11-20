"""
Web Scraping Utilities Module

This module provides reusable functions for web scraping and data enrichment
for the AWO Einrichtungsdatenbank project.

Author: DSSG Berlin Volunteers
"""

import re
import time
from pathlib import Path
from random import uniform
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup

# Default scraping configuration
DEFAULT_CONFIG = {
    'user_agent': 'AWO-Research-Bot/1.0 (Research project; contact@awo.org)',
    'delay_min': 1.0,
    'delay_max': 3.0,
    'timeout': 10,
    'max_retries': 3,
}


def fetch_webpage(url: str, config: Dict = None) -> Tuple[bool, str, Optional[str], Optional[str]]:
    """
    Fetch a webpage with proper error handling and rate limiting.

    Args:
        url: URL to fetch
        config: Scraping configuration dictionary

    Returns:
        Tuple of (success: bool, url: str, content: str or None, error: str or None)
    """
    if config is None:
        config = DEFAULT_CONFIG

    headers = {'User-Agent': config['user_agent']}

    for attempt in range(config['max_retries']):
        try:
            # Rate limiting
            time.sleep(uniform(config['delay_min'], config['delay_max']))

            response = requests.get(url, headers=headers, timeout=config['timeout'])
            response.raise_for_status()

            return True, url, response.text, None

        except requests.exceptions.RequestException as e:
            error_msg = f"Attempt {attempt + 1}/{config['max_retries']} failed: {str(e)}"
            if attempt == config['max_retries'] - 1:
                return False, None, error_msg
            # Exponential backoff
            time.sleep(2 ** attempt)

    return False, url, None, "Max retries exceeded"


def extract_contact_info(html_content: str) -> Dict[str, List[str]]:
    """
    Extract contact information from HTML content.

    Args:
        html_content: HTML content as string

    Returns:
        Dictionary with extracted contact information
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    contact_info = {
        'emails': [],
        'phones': [],
        'addresses': [],
        'social_media': []
    }

    text = soup.get_text()

    # Extract emails
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, text)
    contact_info['emails'] = list(set(emails))

    # Extract German phone numbers
    phone_pattern = r'(?:\+49|0)[\s\-]?\d{2,5}[\s\-]?\d{2,10}'
    phones = re.findall(phone_pattern, text)
    contact_info['phones'] = list(set(phones))

    # Extract social media links
    social_patterns = {
        'facebook': r'(?:https?://)?(?:www\.)?facebook\.com/[\w\-\.]+',
        'twitter': r'(?:https?://)?(?:www\.)?twitter\.com/[\w\-\.]+',
        'instagram': r'(?:https?://)?(?:www\.)?instagram\.com/[\w\-\.]+',
        'linkedin': r'(?:https?://)?(?:www\.)?linkedin\.com/(?:company|in)/[\w\-\.]+',
    }

    for platform, pattern in social_patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            contact_info['social_media'].extend(matches)

    return contact_info


def extract_opening_hours(html_content: str) -> List[str]:
    """
    Extract opening hours from HTML content.

    Args:
        html_content: HTML content as string

    Returns:
        List of opening hours strings
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    opening_hours = []

    # Common German patterns for opening hours
    patterns = [
        r'(?:Öffnungszeiten|Sprechzeiten|Öffnungs-zeiten)[\s:]*(.{0,200})',
        r'(?:Mo|Di|Mi|Do|Fr|Sa|So)(?:\.|\s)*(?:\-|bis)(?:\s)*(?:Mo|Di|Mi|Do|Fr|Sa|So)(?:\.|\s)*\d{1,2}:\d{2}',
    ]

    text = soup.get_text()

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        opening_hours.extend(matches)

    return opening_hours


def extract_services(html_content: str) -> List[str]:
    """
    Extract service descriptions from HTML content.

    Args:
        html_content: HTML content as string

    Returns:
        List of service descriptions
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    services = []

    # Look for common service-related keywords
    service_keywords = [
        'Beratung', 'Pflege', 'Betreuung', 'Kindergarten', 'Kita',
        'Seniorenheim', 'Tagespflege', 'Ambulant', 'Stationär',
        'Jugend', 'Familie', 'Migration', 'Integration'
    ]

    # Search in headings and list items
    for tag in soup.find_all(['h2', 'h3', 'h4', 'li', 'p']):
        text = tag.get_text().strip()
        if any(keyword.lower() in text.lower() for keyword in service_keywords):
            services.append(text)

    return services[:10]  # Limit to top 10


def check_robots_txt(domain: str) -> Tuple[bool, str]:
    """
    Check if scraping is allowed according to robots.txt.

    Args:
        domain: Domain to check

    Returns:
        Tuple of (allowed: bool, message: str)
    """
    robots_url = f"https://{domain}/robots.txt"

    try:
        response = requests.get(robots_url, timeout=5)
        if response.status_code == 200:
            # Basic check - you might want to use robotparser for more thorough checking
            if 'Disallow: /' in response.text:
                return False, "Scraping disallowed by robots.txt"
            return True, "Scraping allowed"
        else:
            return True, "No robots.txt found (allowed by default)"
    except:
        return True, "Could not check robots.txt (proceeding with caution)"


def extract_impressum_data(html_content: str) -> Dict[str, str]:
    """
    Extract data from Impressum (legal notice) page.

    Args:
        html_content: HTML content of impressum page

    Returns:
        Dictionary with extracted impressum data
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    impressum_data = {
        'organization': None,
        'legal_form': None,
        'address': None,
        'registration': None
    }

    text = soup.get_text()

    # Extract legal form
    legal_forms = ['e.V.', 'gGmbH', 'GmbH', 'gemeinnützige GmbH', 'Verein']
    for form in legal_forms:
        if form in text:
            impressum_data['legal_form'] = form
            break

    # Extract registration number
    reg_pattern = r'(?:Registernummer|Vereinsregister|Handelsregister)[\s:]*([A-Z0-9\s]+)'
    reg_match = re.search(reg_pattern, text, re.IGNORECASE)
    if reg_match:
        impressum_data['registration'] = reg_match.group(1).strip()

    return impressum_data


def scrape_domain_batch(domains: List[str],
                       config: Dict = None,
                       max_domains: int = None) -> pd.DataFrame:
    """
    Scrape a batch of domains and return results as DataFrame.

    Args:
        domains: List of domain names
        config: Scraping configuration
        max_domains: Maximum number of domains to scrape (for testing)

    Returns:
        DataFrame with scraping results
    """
    if config is None:
        config = DEFAULT_CONFIG

    if max_domains:
        domains = domains[:max_domains]

    results = []
    total = len(domains)

    for idx, domain in enumerate(domains, 1):
        print(f"[{idx}/{total}] Scraping {domain}...")

        url = f"https://{domain}"
        success, content, error = fetch_webpage(url, config)

        result = {
            'domain': domain,
            'url': url,
            'scrape_success': success,
            'scrape_timestamp': pd.Timestamp.now().isoformat(),
            'error': error
        }

        if success and content:
            contact_info = extract_contact_info(content)
            result.update({
                'extracted_emails': ','.join(contact_info['emails']),
                'extracted_phones': ','.join(contact_info['phones']),
                'social_media': ','.join(contact_info['social_media']),
                'content_length': len(content)
            })

        results.append(result)

    return pd.DataFrame(results)


def find_impressum_link(html_content: str, base_url: str) -> Optional[str]:
    """
    Find the link to the Impressum page.

    Args:
        html_content: HTML content of the page
        base_url: Base URL of the website

    Returns:
        URL to impressum page or None
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Common patterns for impressum links
    impressum_patterns = [
        'impressum', 'imprint', 'legal notice', 'rechtliches'
    ]

    for link in soup.find_all('a', href=True):
        link_text = link.get_text().lower()
        link_href = link['href'].lower()

        if any(pattern in link_text or pattern in link_href for pattern in impressum_patterns):
            # Make absolute URL
            full_url = urljoin(base_url, link['href'])
            return full_url

    return None


def validate_extracted_data(data: Dict) -> Dict[str, bool]:
    """
    Validate extracted data quality.

    Args:
        data: Dictionary of extracted data

    Returns:
        Dictionary of validation results
    """
    validation = {
        'has_email': bool(data.get('extracted_emails')),
        'has_phone': bool(data.get('extracted_phones')),
        'has_social_media': bool(data.get('social_media')),
        'has_content': data.get('content_length', 0) > 0
    }

    validation['quality_score'] = sum(validation.values()) / len(validation)

    return validation


def export_scraping_report(results_df: pd.DataFrame, output_path: Path):
    """
    Export a comprehensive scraping report.

    Args:
        results_df: DataFrame with scraping results
        output_path: Path to save the report
    """
    report = {
        'total_domains': len(results_df),
        'successful_scrapes': results_df['scrape_success'].sum() if 'scrape_success' in results_df else 0,
        'failed_scrapes': (~results_df['scrape_success']).sum() if 'scrape_success' in results_df else 0,
        'success_rate': f"{results_df['scrape_success'].mean():.1%}" if 'scrape_success' in results_df else 'N/A',
        'domains_with_email': results_df['extracted_emails'].str.len().gt(0).sum() if 'extracted_emails' in results_df else 0,
        'domains_with_phone': results_df['extracted_phones'].str.len().gt(0).sum() if 'extracted_phones' in results_df else 0,
    }

    report_df = pd.DataFrame([report])
    report_df.to_csv(output_path, index=False)
    print(f"✓ Scraping report exported to {output_path}")


if __name__ == "__main__":
    # Example usage
    print("Web Scraping Utilities Module - AWO Project")
    print("=" * 60)
    print("\nAvailable functions:")
    print("  - fetch_webpage()")
    print("  - extract_contact_info()")
    print("  - extract_opening_hours()")
    print("  - extract_services()")
    print("  - check_robots_txt()")
    print("  - extract_impressum_data()")
    print("  - scrape_domain_batch()")
    print("  - find_impressum_link()")
    print("  - validate_extracted_data()")
    print("  - export_scraping_report()")
