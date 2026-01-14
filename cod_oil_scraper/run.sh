#!/usr/bin/env bashio
set -e

echo "================================================"
echo "COD Oil Price Scraper Starting (v1.4.6)"
echo "================================================"

# Read configuration using bashio
ZIPCODE=$(bashio::config 'zipcode')
HOUR_1=$(bashio::config 'schedule_hour_1')
HOUR_2=$(bashio::config 'schedule_hour_2')
LOG_LEVEL=$(bashio::config 'log_level')

# Validate configuration
if [ -z "$ZIPCODE" ]; then
    bashio::log.error "Zipcode not configured!"
    exit 1
fi

# Get the supervisor token using bashio
SUPERVISOR_TOKEN="${__BASHIO_SUPERVISOR_TOKEN:-}"

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
