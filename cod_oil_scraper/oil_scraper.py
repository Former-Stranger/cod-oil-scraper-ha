#!/usr/bin/env python3
"""
COD Oil Price Scraper for Home Assistant
Scrapes heating oil prices from codoil.com and pushes to Home Assistant
Uses ingress token automatically provided by Home Assistant
"""

import os
import sys
import logging
import requests
import re
from datetime import datetime
import time

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


def push_to_ha(price):
    """
    Push price to Home Assistant using internal API
    Home Assistant OS automatically provides access via homeassistant_api: true
    
    Args:
        price (float): The oil price in $/gallon
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Try the internal API endpoint that should be available with homeassistant_api: true
    url = f"http://supervisor/core/api/states/{ENTITY_ID}"
    
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
    
    try:
        logger.debug(f"Pushing to URL: {url}")
        # No authorization header needed - supervisor handles it internally
        headers = {
            "Content-Type": "application/json"
        }
        
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if r.status_code in [200, 201]:
            logger.info(f"✓ Successfully pushed price ${price}/gal to Home Assistant")
            return True
        else:
            logger.error(f"✗ Failed with status {r.status_code}")
            logger.debug(f"Response: {r.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"✗ Failed to push to Home Assistant: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error pushing to HA: {e}")
        return False


def scrape_price():
    """
    Scrape heating oil price from COD Oil website
    
    Returns:
        float or None: The price in $/gallon, or None if scraping failed
    """
    logger.info(f"Starting price scrape for zipcode: {ZIPCODE}")
    
    try:
        # Create a session with more realistic browser headers
        session = requests.Session()
        
        # More complete browser headers to avoid bot detection
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        })
        
        # First, get the main page to establish session and get cookies
        logger.debug("Fetching main page...")
        response = session.get("https://www.codoil.com", timeout=30, allow_redirects=True)
        response.raise_for_status()
        
        logger.debug(f"Initial response status: {response.status_code}")
        logger.debug(f"Cookies received: {len(session.cookies)}")
        
        # Small delay to appear more human-like
        time.sleep(1)
        
        # Now submit the zipcode with the established session
        logger.debug(f"Submitting zipcode: {ZIPCODE}")
        
        # Update headers for the POST request
        session.headers.update({
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://www.codoil.com',
            'Referer': 'https://www.codoil.com/',
        })
        
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
        
        logger.debug(f"POST response status: {response.status_code}")
        
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
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            logger.error(f"✗ Access forbidden (403) - website may be blocking automated access")
            logger.error("This could be due to bot detection. The website may require a real browser.")
        else:
            logger.error(f"✗ HTTP error during scraping: {e}")
        return None
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
    logger.info("COD Oil Price Scraper - Starting (v1.2.0)")
    logger.info("=" * 50)
    
    # Validate configuration
    if not ZIPCODE:
        logger.error("✗ ZIPCODE not configured!")
        sys.exit(1)
    
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
