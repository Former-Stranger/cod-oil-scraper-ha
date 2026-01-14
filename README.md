# COD Oil Price Scraper - Home Assistant Add-on

Automatically scrape heating oil prices from COD Oil and push them to Home Assistant as a sensor.

## About

This Home Assistant add-on automatically fetches current heating oil prices from [codoil.com](https://www.codoil.com) for your zip code and creates a sensor entity in Home Assistant that you can use in automations, dashboards, and more.

## Features

- 🔄 Automatic daily price updates on a configurable schedule
- 📊 Creates a sensor entity automatically (no manual configuration needed)
- 🕐 Configurable update time (default: midnight)
- 📝 Detailed logging with configurable log levels
- 🚀 Runs immediately on startup
- 💾 Stores price history in Home Assistant

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

1. Click your **profile icon** (bottom left in Home Assistant sidebar)
2. Scroll down to **Long-Lived Access Tokens**
3. Click **Create Token**
4. Give it a name like "COD Oil Scraper"
5. **Copy the token** (you won't be able to see it again!)

### Step 2: Configure the Add-on

Configure in the add-on's **Configuration** tab:

```yaml
zipcode: "06810"
ha_token: "YOUR_LONG_LIVED_ACCESS_TOKEN_HERE"
schedule_hour: 0
schedule_minute: 0
log_level: "info"
```

### Configuration Options

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `zipcode` | **Yes** | `"06810"` | Your zip code for price lookup |
| `ha_token` | **Yes** | `""` | Your Long-Lived Access Token |
| `schedule_hour` | No | `0` | Hour to check price daily (0-23) |
| `schedule_minute` | No | `0` | Minute to check price daily (0-59) |
| `log_level` | No | `"info"` | Logging level: `debug`, `info`, `warning`, `error` |

## Usage

After installation:

1. Create a Long-Lived Access Token (see above)
2. Configure your zip code and token in the **Configuration** tab
3. Click **Start**
4. Enable **Start on boot** (recommended)
5. Check the **Log** tab to verify it's working

### Sensor Entity

The add-on automatically creates: `sensor.heating_oil_price_[ZIPCODE]`

Example: `sensor.heating_oil_price_06810`

### Dashboard Example

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

## Support

- **Issues**: [Report a Bug](https://github.com/Former-Stranger/cod_oil_scraper/issues)
- **Documentation**: See `cod_oil_scraper/README.md` for detailed docs

## License

MIT License - see LICENSE file for details
