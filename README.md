# Tide Clock

Displays tide height predictions for Point-du-Chêne, NB on a Waveshare 10.85" e-ink display connected to a Raspberry Pi.

Every 10 minutes a tmux loop fetches data from the Canadian Hydrographic Service API, renders a 72-hour tide plot with matplotlib, and pushes it to the display.

## Files

- `tide_plot.py` — fetches tide data and saves a PNG to `plots/`
- `epaper_display.py` — loads the latest PNG and sends it to the e-ink screen
- `update_tide.sh` — runs both in sequence

## Setup on the Pi

**1. Clone the repo**
```bash
git clone https://github.com/ndelworth/tide-clock.git ~/tide_app
```

**2. Install the Waveshare e-Paper library**
```bash
git clone --depth 1 https://github.com/waveshare/e-Paper.git /tmp/e-paper-lib
mkdir -p lib
# Note: "RaspberryPi_JetsonNano" is just the name of the directory in Waveshare's repo —
# this works on any Raspberry Pi model.
cp -r /tmp/e-paper-lib/RaspberryPi_JetsonNano/python/lib/waveshare_epd lib/

# The 10.85" driver and a compatible epdconfig aren't in the main repo yet — grab them separately:
wget https://raw.githubusercontent.com/czuryk/Waveshare-ePaper-10.85-demo/main/lib/waveshare_epd/epd10in85.py -P lib/waveshare_epd/
wget https://raw.githubusercontent.com/czuryk/Waveshare-ePaper-10.85-demo/main/lib/waveshare_epd/epdconfig.py -O lib/waveshare_epd/epdconfig.py
```

**3. Enable SPI on the Pi**
```bash
sudo raspi-config  # Interface Options → SPI → Enable
```

**4. Set up config.py**

```bash
cp config.py.example ~/tide_app/config.py
```
Then edit `config.py` and fill in your `BANNER_URL`. If you don't want a banner, leave `BANNER_URL = None`.

**5. Start it running in a tmux session**
```bash
tmux new -s tide
cd ~/tide_app
while true; do bash update_tide.sh; sleep 600; done
```
Detach with `Ctrl-B D`. To check on it later: `tmux attach -t tide`.

**6. Powering off**

Before shutting the Pi down, clear the screen to avoid ghosting:
```bash
python3 epaper_display.py --clear
sudo shutdown -h now
```

## Troubleshooting

**`ModuleNotFoundError: No module named 'waveshare_epd'`**
The Waveshare library isn't installed. Follow step 2 above.

**`cannot import name 'epd10in85' from 'waveshare_epd'`**
The `epd10in85` driver isn't included in the main Waveshare repo. Grab it from the community fork:
```bash
wget https://raw.githubusercontent.com/czuryk/Waveshare-ePaper-10.85-demo/main/lib/waveshare_epd/epd10in85.py -P ~/tide_app/lib/waveshare_epd/
```

**`AttributeError: module 'waveshare_epd.epdconfig' has no attribute 'RST_PIN'`**
The `epdconfig.py` from the main Waveshare repo isn't compatible with the 10.85" driver. Replace it:
```bash
wget https://raw.githubusercontent.com/czuryk/Waveshare-ePaper-10.85-demo/main/lib/waveshare_epd/epdconfig.py -O ~/tide_app/lib/waveshare_epd/epdconfig.py
```

## Tide data source

Canadian Hydrographic Service IWLS API — station `64b6e5ec8027cb190816a0c0` (Point-du-Chêne, NB).
