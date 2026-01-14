#!/usr/bin/env python3
"""
COD Oil Price Scraper for Home Assistant - Diagnostic Version
Searches for API endpoints and JavaScript that might fetch the price
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

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def analyze_page():
    """
    Analyze the page to find how the price is loaded
    """
    logger.info(f"Analyzing codoil.com for zipcode: {ZIPCODE}")
    
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        
        # Get main page
        logger.info("Fetching main page...")
        response = session.get("https://www.codoil.com", timeout=30, allow_redirects=True)
        response.raise_for_status()
        
        time.sleep(1)
        
        # Submit zipcode
        logger.info(f"Submitting zipcode: {ZIPCODE}")
        session.headers.update({
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://www.codoil.com',
            'Referer': 'https://www.codoil.com/',
        })
        
        response = session.post(
            "https://www.codoil.com",
            data={'number': ZIPCODE},
            timeout=30,
            allow_redirects=True
        )
        response.raise_for_status()
        
        html = response.text
        
        logger.info(f"Page loaded: {len(html)} characters")
        logger.info("=" * 60)
        
        # Search for API endpoints
        logger.info("Searching for API endpoints...")
        api_patterns = [
            r'https?://[^"\']+/api/[^"\']+',
            r'https?://[^"\']+price[^"\']*',
            r'ajax[^"\']*price[^"\']*',
            r'/rest/[^"\']+',
        ]
        
        for pattern in api_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            if matches:
                logger.info(f"  Pattern '{pattern[:30]}...' found:")
                for match in set(matches[:5]):
                    logger.info(f"    - {match}")
        
        # Search for price-related JavaScript variables
        logger.info("\nSearching for price variables in JavaScript...")
        js_patterns = [
            r'price["\']?\s*[:=]\s*["\']?(\d+\.?\d*)',
            r'amount["\']?\s*[:=]\s*["\']?(\d+\.?\d*)',
            r'cost["\']?\s*[:=]\s*["\']?(\d+\.?\d*)',
            r'var\s+price\s*=\s*(["\']?\d+\.?\d*["\']?)',
        ]
        
        for pattern in js_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            if matches:
                logger.info(f"  Pattern found {len(matches)} matches:")
                for match in matches[:10]:
                    logger.info(f"    - {match}")
        
        # Look for form actions that might submit to get price
        logger.info("\nSearching for forms...")
        form_actions = re.findall(r'<form[^>]+action=["\']([^"\']+)["\']', html, re.IGNORECASE)
        if form_actions:
            logger.info(f"  Found {len(form_actions)} forms:")
            for action in set(form_actions):
                logger.info(f"    - {action}")
        
        # Look for price display elements
        logger.info("\nSearching for price display elements...")
        price_elements = re.findall(r'<[^>]*(price|cost|amount)[^>]*>([^<]{0,100})</[^>]*>', html, re.IGNORECASE)
        if price_elements:
            logger.info(f"  Found {len(price_elements)} potential price elements:")
            for elem in price_elements[:10]:
                logger.info(f"    - {elem}")
        
        # Search for the word "price" or "$" in the HTML
        logger.info("\nSearching for dollar signs and 'price' text...")
        dollar_context = re.findall(r'.{0,50}\$\d+\.?\d*.{0,50}', html)
        if dollar_context:
            logger.info(f"  Found {len(dollar_context)} instances with $:")
            for ctx in dollar_context[:5]:
                logger.info(f"    - {ctx.strip()}")
        
        price_context = re.findall(r'.{0,50}price.{0,50}', html, re.IGNORECASE)
        if price_context:
            logger.info(f"  Found {len(price_context)} instances with 'price':")
            for ctx in set(list(price_context)[:10]):
                logger.info(f"    - {ctx.strip()}")
        
        # Save full HTML
        try:
            with open('/var/log/codoil_full_page.html', 'w', encoding='utf-8') as f:
                f.write(html)
            logger.info("\n✓ Full HTML saved to /var/log/codoil_full_page.html")
        except Exception as e:
            logger.error(f"Could not save HTML: {e}")
        
        logger.info("=" * 60)
        logger.info("Analysis complete!")
        
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        logger.exception("Full traceback:")


if __name__ == "__main__":
    analyze_page()
