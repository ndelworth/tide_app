# Tide Clock

Displays tide height predictions for Point-du-Chêne, NB on a Waveshare 10.85" e-ink display connected to a Raspberry Pi.

Every 10 minutes a cron job fetches data from the Canadian Hydrographic Service API, renders a 72-hour tide plot with matplotlib, and pushes it to the display.

## Files

- `tide_plot.py` — fetches tide data and saves a PNG to `plots/`
- `epaper_display.py` — loads the latest PNG and sends it to the e-ink screen
- `update_tide.sh` — runs both in sequence

## Setup on the Pi

**1. Clone and install Python deps**
```bash
git clone https://github.com/ndelworth/tide-clock.git ~/tide_app
cd ~/tide_app
uv sync
```

**2. Install the Waveshare e-Paper library**
```bash
git clone --depth 1 https://github.com/waveshare/e-Paper.git /tmp/e-paper-lib
mkdir -p lib
# Note: "RaspberryPi_JetsonNano" is just the name of the directory in Waveshare's repo —
# this works on any Raspberry Pi model.
cp -r /tmp/e-paper-lib/RaspberryPi_JetsonNano/python/lib/waveshare_epd lib/
```

**3. Enable SPI on the Pi**
```bash
sudo raspi-config  # Interface Options → SPI → Enable
```

**4. Start it running in a tmux session**
```bash
tmux new -s tide
cd ~/tide_app
while true; do bash update_tide.sh; sleep 600; done
```
Detach with `Ctrl-B D`. To check on it later: `tmux attach -t tide`.

**6. Powering off**

Before shutting the Pi down, clear the screen to avoid ghosting:
```bash
uv run python3 epaper_display.py --clear
sudo shutdown -h now
```

## Tide data source

Canadian Hydrographic Service IWLS API — station `64b6e5ec8027cb190816a0c0` (Point-du-Chêne, NB).
