# COD Oil Price Scraper

Automatically scrape heating oil prices from COD Oil and push them to Home Assistant as a sensor.

## Installation

Add this repository to your Home Assistant:

```
https://github.com/Former-Stranger/cod_oil_scraper
```

## Configuration

```yaml
zipcode: "06810"
schedule_hour_1: 9
schedule_hour_2: 15
log_level: "info"
```

### Options

- **zipcode** (required): Your zip code for price lookup
- **schedule_hour_1** (optional, default: 9): First daily update hour (0-23)
- **schedule_hour_2** (optional, default: 15): Second daily update hour (0-23)
- **log_level** (optional, default: "info"): Logging level (debug, info, warning, error)

## Sensor

Creates: `sensor.heating_oil_price_[ZIPCODE]`

Attributes:
- **State**: Current price (e.g., 3.45)
- **Unit**: $/gal
- **Device Class**: monetary
- **Last Updated**: ISO timestamp
- **Source**: codoil.com
- **Zipcode**: Your configured zip code

## Troubleshooting

### Price not updating
- Verify your zip code is correct and served by COD Oil
- Check add-on logs for errors
- Ensure internet connectivity

### Entity not appearing
- Wait 2-3 minutes after starting
- Check Developer Tools → States
- Restart Home Assistant if needed

### High resource usage
- Normal during scraping (~200-300 MB RAM)
- Resources released after completion
- Runs twice daily by default
