#!/usr/bin/env bash
set -e

echo "================================================"
echo "COD Oil Price Scraper - Token Diagnostic"
echo "================================================"

echo "Environment variables containing 'TOKEN' or 'SUPERVISOR':"
env | grep -i 'token\|supervisor' || echo "  None found"

echo ""
echo "Checking common token locations:"
for path in /run/secrets/SUPERVISOR_TOKEN /var/run/secrets/SUPERVISOR_TOKEN /data/SUPERVISOR_TOKEN /etc/SUPERVISOR_TOKEN; do
    if [ -f "$path" ]; then
        echo "  ✓ Found: $path ($(wc -c < $path) bytes)"
    else
        echo "  ✗ Not found: $path"
    fi
done

echo ""
echo "Files in /run/secrets/:"
ls -la /run/secrets/ 2>/dev/null || echo "  Directory does not exist"

echo ""
echo "Files in /var/run/secrets/:"
ls -la /var/run/secrets/ 2>/dev/null || echo "  Directory does not exist"

echo ""
echo "Files in /data/:"
ls -la /data/ 2>/dev/null | head -20 || echo "  Directory does not exist"

echo ""
echo "All environment variables:"
env | sort

echo "================================================"
echo "Diagnostic complete - keeping container alive for 5 minutes"
echo "================================================"

# Keep container running so you can see the logs
sleep 300
