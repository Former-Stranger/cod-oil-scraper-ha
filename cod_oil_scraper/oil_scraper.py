#!/usr/bin/env python3
"""
COD Oil Price Scraper for Home Assistant
Scrapes heating oil prices from codoil.com and pushes to Home Assistant
"""

import os
import sys
import logging
from playwright.sync_api import sync_playwright
import requests
import re
from datetime import datetime

# Configuration from environment variables
HA_URL = os.getenv("HA_URL", "http://supervisor/core")
SUPERVISOR_TOKEN = os.getenv("SUPERVISOR_TOKEN")
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
    Push price to Home Assistant using Supervisor API
    
    Args:
        price (float): The oil price in $/gallon
        
    Returns:
        bool: True if successful, False otherwise
    """
    url = f"{HA_URL}/api/states/{ENTITY_ID}"
    headers = {
        "Authorization": f"Bearer {SUPERVISOR_TOKEN}",
        "Content-Type": "application/json"
    }
    
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
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        logger.info(f"✓ Successfully pushed price ${price}/gal to Home Assistant")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"✗ Failed to push to Home Assistant: {e}")
        if hasattr(e.response, 'text'):
            logger.debug(f"Response: {e.response.text}")
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
        with sync_playwright() as p:
            # Launch browser in headless mode
            logger.debug("Launching Chromium browser...")
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            page = browser.new_page()
            
            # Navigate to COD Oil website
            logger.debug("Navigating to codoil.com...")
            page.goto("https://www.codoil.com", timeout=60000)
            
            # Wait for and fill zipcode input
            logger.debug("Waiting for zip code input field...")
            page.wait_for_selector("input#number", timeout=30000)
            
            logger.debug(f"Entering zipcode: {ZIPCODE}")
            page.fill("input#number", ZIPCODE, force=True)
            page.keyboard.press("Enter")
            
            # Wait for results to load
            logger.debug("Waiting for results to load...")
            page.wait_for_timeout(10000)
            
            # Get page content
            html = page.content()
            browser.close()
            logger.debug("Browser closed")
            
        # Extract price using regex
        logger.debug("Parsing price from page content...")
        match = re.search(r"\$([0-9]+\.[0-9]{2})", html)
        
        if not match:
            logger.error("✗ Price not found in page content")
            logger.debug(f"Page content length: {len(html)} characters")
            return None
            
        price = float(match.group(1))
        logger.info(f"✓ Found price: ${price}/gal")
        return price
        
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
        
    if not SUPERVISOR_TOKEN:
        logger.error("✗ SUPERVISOR_TOKEN not available!")
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
