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
import time
import json

# Configuration from environment variables
ZIPCODE = os.getenv("ZIPCODE")
LOG_LEVEL = os.getenv("LOG_LEVEL", "info").upper()
HA_TOKEN = os.getenv("HA_TOKEN")
HA_URL = os.getenv("HA_URL", "http://homeassistant:8123").rstrip("/")
APP_VERSION = os.getenv("APP_VERSION", "1.5.5")

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Entity ID based on zipcode
ENTITY_ID = f"sensor.heating_oil_price_{ZIPCODE}"


def int_env(name, default, minimum=0):
    """Read a non-negative integer from the environment."""
    try:
        return max(minimum, int(os.getenv(name, default)))
    except (TypeError, ValueError):
        logger.warning("Invalid %s value; using default %s", name, default)
        return default


HA_READY_TIMEOUT = int_env("HA_READY_TIMEOUT", 600)
HA_READY_INTERVAL = int_env("HA_READY_INTERVAL", 10, minimum=1)
HA_STARTUP_SETTLE_SECONDS = int_env("HA_STARTUP_SETTLE_SECONDS", 60)
HA_PUSH_ATTEMPTS = int_env("HA_PUSH_ATTEMPTS", 6, minimum=1)
HA_PUSH_RETRY_INTERVAL = int_env("HA_PUSH_RETRY_INTERVAL", 10, minimum=1)


def ha_headers():
    """Return authenticated Home Assistant API headers."""
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {HA_TOKEN}"
    }


def wait_for_homeassistant():
    """
    Wait until the Home Assistant REST API is ready to accept state updates.

    Home Assistant can expose the add-on network name before Core is fully
    ready during a system restart. Without this guard the startup scrape can
    succeed externally but fail to create/update the HA state.
    """
    url = f"{HA_URL}/api/config"
    deadline = time.monotonic() + HA_READY_TIMEOUT

    logger.info(f"Waiting for Home Assistant API at {HA_URL} (timeout: {HA_READY_TIMEOUT}s)")

    while True:
        try:
            response = requests.get(url, headers=ha_headers(), timeout=10)

            if response.status_code == 200:
                logger.info("✓ Home Assistant API is ready")
                if HA_STARTUP_SETTLE_SECONDS:
                    logger.info(f"Waiting {HA_STARTUP_SETTLE_SECONDS}s for startup state to settle")
                    time.sleep(HA_STARTUP_SETTLE_SECONDS)
                return True

            if response.status_code in (401, 403):
                logger.error(f"✗ Home Assistant rejected the configured token with status {response.status_code}")
                return False

            logger.info(f"Home Assistant API returned status {response.status_code}; retrying")

        except requests.exceptions.RequestException as e:
            logger.info(f"Home Assistant API is not ready yet: {e}")

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            logger.error(f"✗ Home Assistant API was not ready after {HA_READY_TIMEOUT}s")
            return False

        time.sleep(min(HA_READY_INTERVAL, remaining))


def push_to_ha(price):
    """
    Push price to Home Assistant using REST API

    Args:
        price (float): The oil price in $/gallon

    Returns:
        bool: True if successful, False otherwise
    """
    url = f"{HA_URL}/api/states/{ENTITY_ID}"

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

    for attempt in range(1, HA_PUSH_ATTEMPTS + 1):
        try:
            logger.debug(f"Pushing to URL: {url}")
            r = requests.post(url, headers=ha_headers(), json=payload, timeout=30)

            if r.status_code in [200, 201]:
                logger.info(f"✓ Updated {ENTITY_ID} = ${price}/gal")
                return True

            if r.status_code in [401, 403]:
                logger.error(f"✗ Home Assistant rejected the configured token with status {r.status_code}")
                logger.debug(f"Response: {r.text}")
                return False

            logger.warning(f"Push attempt {attempt}/{HA_PUSH_ATTEMPTS} failed with status {r.status_code}")
            logger.debug(f"Response: {r.text}")

        except requests.exceptions.RequestException as e:
            logger.warning(f"Push attempt {attempt}/{HA_PUSH_ATTEMPTS} failed: {e}")
        except Exception as e:
            logger.error(f"✗ Unexpected error pushing to HA: {e}")
            return False

        if attempt < HA_PUSH_ATTEMPTS:
            time.sleep(HA_PUSH_RETRY_INTERVAL)

    logger.error("✗ Failed to update Home Assistant after retries")
    return False


def scrape_price():
    """
    Scrape heating oil price from COD Oil website

    Returns:
        float or None: The price in $/gallon, or None if scraping failed
    """
    logger.info(f"Starting price scrape for zipcode: {ZIPCODE}")

    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        })

        # Step 1: Get main page to establish session/cookies
        logger.debug("Fetching main page to establish session...")
        response = session.get("https://www.codoil.com", timeout=30, allow_redirects=True)
        response.raise_for_status()

        time.sleep(1)

        # Step 2: Submit zipcode via AJAX endpoint
        logger.debug(f"Submitting zipcode via AJAX: {ZIPCODE}")
        ajax_url = "https://codoil.com/zipcodebasedprice/index/zipcodecheck/"
        session.headers.update({
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://codoil.com',
            'Referer': 'https://codoil.com/',
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
        })

        response = session.post(
            ajax_url,
            data={'zipvalue': ZIPCODE},
            timeout=30,
            allow_redirects=True
        )
        response.raise_for_status()

        # Parse the AJAX response to get the redirect URL
        try:
            ajax_data = response.json()
            logger.debug(f"AJAX response: {ajax_data}")
        except json.JSONDecodeError as e:
            logger.error(f"✗ Failed to parse AJAX response: {e}")
            return None

        if not ajax_data.get('zipcode_status'):
            logger.error(f"✗ Invalid zipcode: {ZIPCODE}")
            return None

        redirect_url = ajax_data.get('redirect_url')
        if not redirect_url:
            logger.error("✗ No redirect URL in AJAX response")
            return None

        # Step 3: Follow redirect to get the pricing page
        logger.debug(f"Following redirect to: {redirect_url}")
        session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
        session.headers.pop('X-Requested-With', None)
        session.headers.pop('Content-Type', None)

        time.sleep(1)

        response = session.get(redirect_url, timeout=30, allow_redirects=True)
        response.raise_for_status()

        html = response.text
        logger.debug(f"Price page loaded: {len(html)} characters")

        # Step 4: Extract the zipcodePrices JavaScript variable
        # Pattern: window.zipcodePrices = {"zipcodeprices":[...]}
        pattern = r'window\.zipcodePrices\s*=\s*({[^;]+});'
        match = re.search(pattern, html)

        if not match:
            logger.error("✗ Could not find zipcodePrices in HTML")
            return None

        try:
            prices_json = json.loads(match.group(1))
            logger.debug(f"Found zipcodePrices data: {prices_json}")

            # Get the first price from the array
            if 'zipcodeprices' in prices_json and len(prices_json['zipcodeprices']) > 0:
                first_price_obj = prices_json['zipcodeprices'][0]
                price_str = first_price_obj['price']

                logger.debug(f"Raw price string: {price_str}")

                # Extract price from string like "$2.89<sup>9</sup>"
                # This means $2.899 per gallon
                price_match = re.search(r'\$(\d+\.\d+)(?:<sup>(\d+)</sup>)?', price_str)

                if price_match:
                    dollars = price_match.group(1)
                    decimal = price_match.group(2) if price_match.group(2) else ''

                    # Combine: "2.89" + "9" = "2.899"
                    if decimal:
                        price = float(dollars + decimal)
                    else:
                        price = float(dollars)

                    logger.info(f"✓ Found price: ${price}/gal for {first_price_obj['gallon']}")
                    return price
                else:
                    logger.error(f"✗ Could not parse price from: {price_str}")
                    return None
            else:
                logger.error("✗ No prices found in zipcodeprices array")
                return None

        except json.JSONDecodeError as e:
            logger.error(f"✗ Failed to parse JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"✗ Error extracting price: {e}")
            logger.exception("Full traceback:")
            return None

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            logger.error(f"✗ Access forbidden (403) - website may be blocking automated access")
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
    logger.info(f"COD Oil Price Scraper - Starting (v{APP_VERSION})")
    logger.info(f"Entity: {ENTITY_ID}")
    logger.info("=" * 50)

    # Validate configuration
    if not ZIPCODE:
        logger.error("✗ ZIPCODE not configured!")
        sys.exit(1)

    if not HA_TOKEN:
        logger.error("✗ HA_TOKEN not configured!")
        sys.exit(1)

    if not wait_for_homeassistant():
        logger.error("✗ Home Assistant was not ready for updates")
        logger.info("=" * 50)
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
