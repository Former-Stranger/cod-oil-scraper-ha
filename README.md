# COD Oil Price Scraper - Home Assistant Add-on

Automatically scrape heating oil prices from COD Oil and push them to Home Assistant as a sensor.

## About

This Home Assistant add-on automatically fetches current heating oil prices from [codoil.com](https://www.codoil.com) for your zip code and creates a sensor entity in Home Assistant that you can use in automations, dashboards, and more.

## Features

- 🔄 Automatic price updates on a configurable schedule
- 📊 Creates a sensor entity automatically (no manual configuration needed)
- 🕐 Configurable update times (default: 9 AM and 3 PM)
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

Configure in the add-on's **Configuration** tab:

```yaml
zipcode: "06810"
schedule_hour_1: 9
schedule_hour_2: 15
log_level: "info"
```

### Configuration Options

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `zipcode` | **Yes** | `"06810"` | Your zip code for price lookup |
| `schedule_hour_1` | No | `9` | First daily update hour (0-23) |
| `schedule_hour_2` | No | `15` | Second daily update hour (0-23) |
| `log_level` | No | `"info"` | Logging level: `debug`, `info`, `warning`, `error` |

## Usage

After installation:

1. Configure your zip code in the **Configuration** tab
2. Click **Start**
3. Enable **Start on boot** (recommended)
4. Check the **Log** tab to verify it's working

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
