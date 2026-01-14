# COD Oil Price Scraper

Automatically scrape heating oil prices from COD Oil and push them to Home Assistant as a sensor.

## Installation

1. Navigate to **Settings** → **Add-ons** → **Add-on Store**
2. Click the **⋮** menu (top right) → **Repositories**
3. Add this repository URL:
   ```
   https://github.com/Former-Stranger/cod_oil_scraper
   ```
4. Find "COD Oil Price Scraper" in the add-on store
5. Click **Install**

## Configuration

### Step 1: Create a Long-Lived Access Token

Before starting the add-on, you need to create a Home Assistant access token:

1. Click your **profile icon** (bottom left in Home Assistant sidebar)
2. Scroll down to **Long-Lived Access Tokens**
3. Click **Create Token**
4. Give it a name like "COD Oil Scraper"
5. **Copy the token** (you won't be able to see it again!)

### Step 2: Configure the Add-on

In the add-on's **Configuration** tab, enter:

```yaml
zipcode: "06810"
ha_url: "http://homeassistant:8123"
ha_token: "YOUR_LONG_LIVED_ACCESS_TOKEN_HERE"
schedule_hour_1: 9
schedule_hour_2: 15
log_level: "info"
```

### Configuration Options

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `zipcode` | **Yes** | `"06810"` | Your zip code for price lookup |
| `ha_url` | **Yes** | `"http://homeassistant:8123"` | Home Assistant URL (usually don't change) |
| `ha_token` | **Yes** | `""` | Your Long-Lived Access Token |
| `schedule_hour_1` | No | `9` | First daily update hour (0-23) |
| `schedule_hour_2` | No | `15` | Second daily update hour (0-23) |
| `log_level` | No | `"info"` | Logging level: `debug`, `info`, `warning`, `error` |

### Step 3: Start the Add-on

1. Click **Start**
2. Enable **Start on boot** (recommended)
3. Check the **Log** tab to verify it's working

## Sensor Entity

The add-on automatically creates: `sensor.heating_oil_price_[ZIPCODE]`

Example: `sensor.heating_oil_price_06810`

## Dashboard Example

```yaml
type: gauge
entity: sensor.heating_oil_price_06810
min: 2
max: 6
name: Heating Oil
unit: $/gal
severity:
  green: 0
  yellow: 3.5
  red: 4.5
```

## Troubleshooting

### Token Error

If you see "HA_TOKEN not configured":
1. Make sure you created a Long-Lived Access Token
2. Copy the full token (usually starts with `eyJ...`)
3. Paste it in the `ha_token` field in configuration
4. Save and restart the add-on

### Price Not Found

If the scraper can't find the price:
1. Verify your zip code is correct
2. Check that COD Oil serves your area
3. Set `log_level: "debug"` to see more details

## Support

- **Issues**: [Report a Bug](https://github.com/Former-Stranger/cod_oil_scraper/issues)

## License

MIT License
