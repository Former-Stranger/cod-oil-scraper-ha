#!/usr/bin/env python3
"""
COD Oil Price Scraper for Home Assistant
Scrapes heating oil prices from codoil.com and pushes to Home Assistant
"""

import os
import sys
import logging
import requests
import re
from datetime import datetime

# Configuration from environment variables
ZIPCODE = os.getenv("ZIPCODE")
LOG_LEVEL = os.getenv("LOG_LEVEL", "info").upper()

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Entity ID based on zipcode
ENTITY_ID = f"sensor.heating_oil_price_{ZIPCODE}"

# Try multiple HA URLs and token sources
HA_URLS = [
    "http://supervisor/core",
    "http://homeassistant:8123", 
    "http://localhost:8123",
    "http://127.0.0.1:8123"
]

TOKEN_SOURCES = [
    os.getenv("SUPERVISOR_TOKEN"),
    os.getenv("HA_TOKEN"),
]

# Try to read token from files
token_files = [
    "/var/run/secrets/SUPERVISOR_TOKEN",
    "/run/secrets/SUPERVISOR_TOKEN",
]

for tf in token_files:
    try:
        with open(tf, 'r') as f:
            TOKEN_SOURCES.append(f.read().strip())
    except:
        pass


def push_to_ha(price):
    """
    Push price to Home Assistant - try multiple methods
    
    Args:
        price (float): The oil price in $/gallon
        
    Returns:
        bool: True if successful, False otherwise
    """
    payload = {
        "state": str(price),
        "attributes": {
            "unit_of_measurement": "$/gal",
            "friendly_name": f"Heating Oil Price ({ZIPCODE})",
            "zipcode": ZIPCODE,
            "device_class": "monetary",
            "last_updated": datetime.now().isoformat(),
            "source": "codoil.com"
        }
    }
    
    # Try each URL with each token
    for ha_url in HA_URLS:
        for token in TOKEN_SOURCES:
            if not token:
                continue
                
            url = f"{ha_url}/api/states/{ENTITY_ID}"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            try:
                logger.debug(f"Trying URL: {ha_url} with token length: {len(token)}")
                r = requests.post(url, headers=headers, json=payload, timeout=10)
                
                if r.status_code == 200 or r.status_code == 201:
                    logger.info(f"✓ Successfully pushed price ${price}/gal to Home Assistant")
                    logger.info(f"✓ Used URL: {ha_url}")
                    return True
                else:
                    logger.debug(f"Failed with status {r.status_code}: {r.text[:100]}")
                    
            except requests.exceptions.RequestException as e:
                logger.debug(f"Connection failed to {ha_url}: {e}")
                continue
            except Exception as e:
                logger.debug(f"Unexpected error with {ha_url}: {e}")
                continue
    
    logger.error("✗ Failed to push to Home Assistant after trying all methods")
    logger.error(f"Tried {len(HA_URLS)} URLs with {len([t for t in TOKEN_SOURCES if t])} tokens")
    return False


def scrape_price():
    """
    Scrape heating oil price from COD Oil website
    
    Returns:
        float or None: The price in $/gallon, or None if scraping failed
    """
    logger.info(f"Starting price scrape for zipcode: {ZIPCODE}")
    
    try:
        # Create a session
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # First, get the main page to establish session
        logger.debug("Fetching main page...")
        response = session.get("https://www.codoil.com", timeout=30)
        response.raise_for_status()
        
        # Now submit the zipcode
        logger.debug(f"Submitting zipcode: {ZIPCODE}")
        
        # Try the form submission
        form_data = {
            'number': ZIPCODE
        }
        
        response = session.post(
            "https://www.codoil.com",
            data=form_data,
            timeout=30,
            allow_redirects=True
        )
        response.raise_for_status()
        
        # Parse the HTML
        logger.debug("Parsing HTML response...")
        html = response.text
        
        # Extract price using regex - look for price patterns
        price_patterns = [
            r'\$(\d+\.\d{2})',  # $3.45
            r'(\d+\.\d{2})\s*(?:per\s*gal|\/\s*gal)',  # 3.45 per gal or 3.45/gal
        ]
        
        price = None
        for pattern in price_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            if matches:
                # Get the first reasonable price (between $1 and $10)
                for match in matches:
                    try:
                        potential_price = float(match)
                        if 1.0 <= potential_price <= 10.0:
                            price = potential_price
                            break
                    except ValueError:
                        continue
                if price:
                    break
        
        if not price:
            logger.error("✗ Price not found in page content")
            logger.debug(f"Page content length: {len(html)} characters")
            logger.debug(f"HTML sample: {html[:500]}")
            return None
            
        logger.info(f"✓ Found price: ${price}/gal")
        return price
        
    except requests.exceptions.RequestException as e:
        logger.error(f"✗ Network error during scraping: {e}")
        return None
    except Exception as e:
        logger.error(f"✗ Error during scraping: {e}")
        logger.exception("Full traceback:")
        return None


def main():
    """Main execution function"""
    logger.info("=" * 50)
    logger.info("COD Oil Price Scraper - Starting")
    logger.info("=" * 50)
    
    # Validate configuration
    if not ZIPCODE:
        logger.error("✗ ZIPCODE not configured!")
        sys.exit(1)
    
    # Check if we have any tokens
    valid_tokens = [t for t in TOKEN_SOURCES if t]
    logger.info(f"Found {len(valid_tokens)} potential authentication tokens")
    
    # Scrape the price
    price = scrape_price()
    
    if price is None:
        logger.error("✗ Failed to scrape price")
        logger.info("=" * 50)
        sys.exit(1)
    
    # Push to Home Assistant
    success = push_to_ha(price)
    
    if success:
        logger.info("=" * 50)
        logger.info("✓ Scrape completed successfully")
        logger.info("=" * 50)
        sys.exit(0)
    else:
        logger.error("✗ Failed to update Home Assistant")
        logger.info("=" * 50)
        sys.exit(1)


if __name__ == "__main__":
    main()
