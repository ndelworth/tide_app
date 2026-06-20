"""
epaper_display.py
-----------------
Loads the latest tide plot PNG and pushes it to the Waveshare 10.85" e-Paper display.

Display specs: 1360 x 480, black/white only.

Requires the Waveshare e-Paper library (lib/waveshare_epd/epd10in85.py).
Install it once on the Pi:
    git clone https://github.com/waveshare/e-Paper.git /tmp/e-Paper
    cp -r /tmp/e-Paper/RaspberryPi_JetsonNano/python/lib/waveshare_epd ./lib/

Usage:
    python3 epaper_display.py           # show latest saved plot
    python3 epaper_display.py --clear   # clear the screen to white
"""

import sys
import glob
import os
import logging
from PIL import Image

# The Waveshare library lives in ./lib/waveshare_epd/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from waveshare_epd import epd10in85

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DISPLAY_WIDTH  = 1360
DISPLAY_HEIGHT = 480


def load_latest_plot(plots_dir="plots"):
    files = glob.glob(os.path.join(plots_dir, "*.png"))
    if not files:
        raise FileNotFoundError(f"No PNG files found in '{plots_dir}/'")
    latest_file = max(files, key=os.path.getmtime)
    return Image.open(latest_file).convert("L")


def show_image(img):
    # Scale to fit the display, preserving aspect ratio, padding with white
    img.thumbnail((DISPLAY_WIDTH, DISPLAY_HEIGHT), Image.LANCZOS)
    canvas = Image.new("1", (DISPLAY_WIDTH, DISPLAY_HEIGHT), 255)  # white background
    x_offset = (DISPLAY_WIDTH  - img.width)  // 2
    y_offset = (DISPLAY_HEIGHT - img.height) // 2
    canvas.paste(img.convert("1"), (x_offset, y_offset))

    logger.info("Initialising display...")
    epd = epd10in85.EPD()
    epd.init()

    logger.info("Sending image to display...")
    epd.display(epd.getbuffer(canvas))

    logger.info("Putting display to sleep...")
    epd.sleep()
    logger.info("Done.")


def clear_screen():
    logger.info("Clearing display to white...")
    epd = epd10in85.EPD()
    epd.init()
    epd.Clear()
    epd.sleep()
    logger.info("Screen cleared.")


if __name__ == "__main__":
    if "--clear" in sys.argv:
        clear_screen()
    else:
        show_image(load_latest_plot())
