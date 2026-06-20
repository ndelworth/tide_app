#!/bin/bash
# update_tide.sh
# Run by cron every 10 minutes.
# Fetches fresh tide data, saves a new plot, then pushes it to the e-ink display.

set -e

cd "$(dirname "$0")"

echo "[$(date)] Updating tide plot..."
uv run python3 tide_plot.py

echo "[$(date)] Sending to display..."
uv run python3 epaper_display.py

echo "[$(date)] Done."
