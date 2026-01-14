#!/usr/bin/with-contab bash
set -e

CONFIG_PATH=/data/options.json

echo "================================================"
echo "COD Oil Price Scraper Starting"
echo "================================================"

# Read configuration from Home Assistant
ZIPCODE=$(jq --raw-output '.zipcode' $CONFIG_PATH)
HOUR_1=$(jq --raw-output '.schedule_hour_1' $CONFIG_PATH)
HOUR_2=$(jq --raw-output '.schedule_hour_2' $CONFIG_PATH)
LOG_LEVEL=$(jq --raw-output '.log_level // "info"' $CONFIG_PATH)

# Home Assistant Supervisor provides these automatically
SUPERVISOR_TOKEN="${SUPERVISOR_TOKEN}"
HA_URL="http://supervisor/core"

# Validate configuration
if [ -z "$ZIPCODE" ]; then
    echo "ERROR: Zipcode not configured!"
    exit 1
fi

if [ -z "$SUPERVISOR_TOKEN" ]; then
    echo "ERROR: SUPERVISOR_TOKEN not available!"
    exit 1
fi

# Export environment variables for Python script
export HA_URL
export SUPERVISOR_TOKEN
export ZIPCODE
export LOG_LEVEL

echo "Configuration:"
echo "  Zipcode: $ZIPCODE"
echo "  Schedule: ${HOUR_1}:00 and ${HOUR_2}:00 daily"
echo "  Log Level: $LOG_LEVEL"
echo "  Home Assistant URL: $HA_URL"
echo "================================================"

# Create log directory
mkdir -p /var/log

# Setup cron jobs
echo "Setting up cron schedule..."
echo "0 ${HOUR_1} * * * cd /app && python3 /app/oil_scraper.py >> /var/log/oil_scraper.log 2>&1" > /etc/crontabs/root
echo "0 ${HOUR_2} * * * cd /app && python3 /app/oil_scraper.py >> /var/log/oil_scraper.log 2>&1" >> /etc/crontabs/root

# Run immediately on startup
echo "Running initial scrape..."
python3 /app/oil_scraper.py 2>&1 | tee -a /var/log/oil_scraper.log

echo "================================================"
echo "Initial scrape complete. Starting cron daemon..."
echo "Logs will be available in the add-on Log tab"
echo "================================================"

# Start cron in foreground
exec crond -f -l 2
