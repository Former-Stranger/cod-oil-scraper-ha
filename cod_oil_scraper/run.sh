#!/usr/bin/env bash
set -e

CONFIG_PATH=/data/options.json

echo "================================================"
echo "COD Oil Price Scraper Starting (v1.4.3)"
echo "================================================"

# Read configuration from Home Assistant
ZIPCODE=$(jq --raw-output '.zipcode' $CONFIG_PATH)
HOUR_1=$(jq --raw-output '.schedule_hour_1' $CONFIG_PATH)
HOUR_2=$(jq --raw-output '.schedule_hour_2' $CONFIG_PATH)
LOG_LEVEL=$(jq --raw-output '.log_level // "info"' $CONFIG_PATH)

# Validate configuration
if [ -z "$ZIPCODE" ]; then
    echo "ERROR: Zipcode not configured!"
    exit 1
fi

# Export environment variables for Python script
export ZIPCODE
export LOG_LEVEL
export SUPERVISOR_TOKEN

echo "Configuration:"
echo "  Zipcode: $ZIPCODE"
echo "  Schedule: ${HOUR_1}:00 and ${HOUR_2}:00 daily"
echo "  Log Level: $LOG_LEVEL"
echo "  Supervisor Token: ${SUPERVISOR_TOKEN:+present}"
echo "================================================"

# Create log directory
mkdir -p /var/log

# Setup cron jobs
echo "Setting up cron schedule..."
cat > /etc/crontabs/root << EOF
0 ${HOUR_1} * * * cd /app && ZIPCODE="${ZIPCODE}" LOG_LEVEL="${LOG_LEVEL}" SUPERVISOR_TOKEN="${SUPERVISOR_TOKEN}" python3 /app/oil_scraper.py >> /var/log/oil_scraper.log 2>&1
0 ${HOUR_2} * * * cd /app && ZIPCODE="${ZIPCODE}" LOG_LEVEL="${LOG_LEVEL}" SUPERVISOR_TOKEN="${SUPERVISOR_TOKEN}" python3 /app/oil_scraper.py >> /var/log/oil_scraper.log 2>&1
EOF

# Run immediately on startup
echo "Running initial scrape..."
python3 /app/oil_scraper.py 2>&1 | tee -a /var/log/oil_scraper.log

echo "================================================"
echo "Initial scrape complete. Starting cron daemon..."
echo "Logs will be available in the add-on Log tab"
echo "================================================"

# Start cron in foreground
exec crond -f -l 2
