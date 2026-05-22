#!/usr/bin/env bash
set -e
set -o pipefail

CONFIG_PATH=/data/options.json

echo "================================================"
echo "COD Oil Price Scraper Starting (v1.5.4)"
echo "================================================"

# Read configuration from options.json
ZIPCODE=$(jq --raw-output '.zipcode' $CONFIG_PATH)
HA_TOKEN=$(jq --raw-output '.ha_token' $CONFIG_PATH)
SCHEDULE_HOUR=$(jq --raw-output '.schedule_hour' $CONFIG_PATH)
SCHEDULE_MINUTE=$(jq --raw-output '.schedule_minute' $CONFIG_PATH)
LOG_LEVEL=$(jq --raw-output '.log_level // "info"' $CONFIG_PATH)
HA_URL="http://homeassistant:8123"
HA_READY_TIMEOUT="${HA_READY_TIMEOUT:-600}"
HA_READY_INTERVAL="${HA_READY_INTERVAL:-10}"
HA_STARTUP_SETTLE_SECONDS="${HA_STARTUP_SETTLE_SECONDS:-60}"

# Validate configuration
if [ -z "$ZIPCODE" ] || [ "$ZIPCODE" = "null" ]; then
    echo "ERROR: Zipcode not configured!"
    exit 1
fi

if [ -z "$HA_TOKEN" ] || [ "$HA_TOKEN" = "null" ]; then
    echo "ERROR: ha_token not configured!"
    echo "Please create a Long-Lived Access Token in Home Assistant:"
    echo "  1. Go to your Profile (bottom left)"
    echo "  2. Scroll to Long-Lived Access Tokens"
    echo "  3. Create a token and paste it in the add-on configuration"
    exit 1
fi

# Export environment variables for Python script
export ZIPCODE
export HA_TOKEN
export LOG_LEVEL
export HA_URL
export HA_READY_TIMEOUT
export HA_READY_INTERVAL
export HA_STARTUP_SETTLE_SECONDS

# Format time for display
printf -v FORMATTED_TIME "%02d:%02d" "$SCHEDULE_HOUR" "$SCHEDULE_MINUTE"

echo "Configuration:"
echo "  Zipcode: $ZIPCODE"
echo "  Daily Schedule: $FORMATTED_TIME"
echo "  Log Level: $LOG_LEVEL"
echo "  HA Token: ${HA_TOKEN:+configured}"
echo "  HA URL: $HA_URL"
echo "  HA readiness timeout: ${HA_READY_TIMEOUT}s"
echo "  HA startup settle delay: ${HA_STARTUP_SETTLE_SECONDS}s"
echo "================================================"

# Create log directory
mkdir -p /var/log

# Setup cron job (once daily)
echo "Setting up cron schedule..."
cat > /etc/crontabs/root << EOF
${SCHEDULE_MINUTE} ${SCHEDULE_HOUR} * * * cd /app && ZIPCODE="${ZIPCODE}" HA_TOKEN="${HA_TOKEN}" LOG_LEVEL="${LOG_LEVEL}" HA_URL="${HA_URL}" HA_READY_TIMEOUT="${HA_READY_TIMEOUT}" HA_READY_INTERVAL="${HA_READY_INTERVAL}" HA_STARTUP_SETTLE_SECONDS="0" python3 /app/oil_scraper.py >> /var/log/oil_scraper.log 2>&1
EOF

# Run immediately on startup, but do not keep the add-on from reaching cron if
# Home Assistant or COD Oil is temporarily unavailable during boot.
echo "Running initial scrape with Home Assistant readiness checks..."
if python3 /app/oil_scraper.py 2>&1 | tee -a /var/log/oil_scraper.log; then
    echo "Initial scrape completed successfully."
else
    echo "WARNING: Initial scrape failed. The cron schedule remains active and will retry at $FORMATTED_TIME."
fi

echo "================================================"
echo "Initial scrape complete. Starting cron daemon..."
echo "Next scheduled run: $FORMATTED_TIME daily"
echo "================================================"

# Start cron in foreground
exec crond -f -l 2
