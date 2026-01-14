#!/usr/bin/env bash
set -e

CONFIG_PATH=/data/options.json

echo "================================================"
echo "COD Oil Price Scraper Starting (v1.5.3)"
echo "================================================"

# Read configuration from options.json
ZIPCODE=$(jq --raw-output '.zipcode' $CONFIG_PATH)
HA_TOKEN=$(jq --raw-output '.ha_token' $CONFIG_PATH)
SCHEDULE_HOUR=$(jq --raw-output '.schedule_hour' $CONFIG_PATH)
SCHEDULE_MINUTE=$(jq --raw-output '.schedule_minute' $CONFIG_PATH)
LOG_LEVEL=$(jq --raw-output '.log_level // "info"' $CONFIG_PATH)

# Validate configuration
if [ -z "$ZIPCODE" ]; then
    echo "ERROR: Zipcode not configured!"
    exit 1
fi

if [ -z "$HA_TOKEN" ]; then
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

# Format time for display
printf -v FORMATTED_TIME "%02d:%02d" "$SCHEDULE_HOUR" "$SCHEDULE_MINUTE"

echo "Configuration:"
echo "  Zipcode: $ZIPCODE"
echo "  Daily Schedule: $FORMATTED_TIME"
echo "  Log Level: $LOG_LEVEL"
echo "  HA Token: ${HA_TOKEN:+configured}"
echo "================================================"

# Create log directory
mkdir -p /var/log

# Setup cron job (once daily)
echo "Setting up cron schedule..."
cat > /etc/crontabs/root << EOF
${SCHEDULE_MINUTE} ${SCHEDULE_HOUR} * * * cd /app && ZIPCODE="${ZIPCODE}" HA_TOKEN="${HA_TOKEN}" LOG_LEVEL="${LOG_LEVEL}" python3 /app/oil_scraper.py >> /var/log/oil_scraper.log 2>&1
EOF

# Run immediately on startup
echo "Running initial scrape..."
python3 /app/oil_scraper.py 2>&1 | tee -a /var/log/oil_scraper.log

echo "================================================"
echo "Initial scrape complete. Starting cron daemon..."
echo "Next scheduled run: $FORMATTED_TIME daily"
echo "================================================"

# Start cron in foreground
exec crond -f -l 2
