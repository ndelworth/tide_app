import requests
from datetime import datetime, timedelta, timezone
import matplotlib.pyplot as plt
import os
import numpy as np
from scipy.signal import savgol_filter
from zoneinfo import ZoneInfo
from astral import LocationInfo
from astral.sun import sun

# --- Station config ---
STATION_ID   = "64b6e5ec8027cb190816a0c0"
STATION_NAME = "Point-du-Chêne"
TIMEZONE     = "America/Halifax"
LATITUDE     = 46.236
LONGITUDE    = -64.539

# --- Y-axis range (metres) — specific to this station's tidal range ---
Y_MIN   = 0.3
Y_MAX   = 2.0
Y_TICKS = [0.6, 1.0, 1.4, 1.8]

# --- Plot styling — tuned for the Waveshare 10.85" display (1360×480, 259.76×91.68mm) ---
FIGURE_SIZE        = (14.17, 5)
PLOT_DPI           = 150
TIDE_LINE_WIDTH    = 10
NOW_LINE_WIDTH     = 5
EXTREMA_MARKER_SIZE  = 5
EXTREMA_LABEL_OFFSET = 0.07
EXTREMA_FONT_SIZE    = 14
TICK_FONT_SIZE       = 20

# --- Banner message (for displaying fun secret messages, like "Happy Father's Day!") ---
# BANNER_URL is loaded from config.py (not committed to git).
# Edit the gist content to change the message; set it to empty to disable.
try:
    from config import BANNER_URL
except ImportError:
    BANNER_URL = None


def fetch_banner():
    if not BANNER_URL:
        return ""
    try:
        response = requests.get(BANNER_URL, timeout=5)
        response.raise_for_status()
        return response.text.strip()
    except Exception:
        return ""  # if the fetch fails, just show no banner

def get_tide_data(now):
    start = now - timedelta(hours=24)
    end   = now + timedelta(hours=48)

    url = f"https://api.iwls-sine.azure.cloud-nuage.dfo-mpo.gc.ca/api/v1/stations/{STATION_ID}/data"
    params = {
        "time-series-code": "wlp",  # predicted water level
        "from": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "to":   end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "resolution": "ONE_MINUTE",
        "station-id": STATION_ID,
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


# TODO: extrema times don't always match official tide forecasts
def label_extrema(ax, local_times, levels):
    levels_np = np.array(levels)
    smoothed = savgol_filter(levels_np, window_length=121, polyorder=3)
    d1 = np.gradient(smoothed)
    extrema_indices = np.where(np.diff(np.sign(d1)) != 0)[0]

    for i in extrema_indices:
        window = slice(max(i - 30, 0), min(i + 30, len(levels_np)))
        local_extreme_idx = window.start + np.argmax(
            np.abs(levels_np[window] - np.mean(levels_np[window]))
        )

        t = local_times[local_extreme_idx]
        v = levels[local_extreme_idx]
        is_high = d1[i] > 0  # slope goes + → − = high tide

        ax.plot(t, v, 'ko', markersize=EXTREMA_MARKER_SIZE, zorder=4)
        ax.text(
            t,
            v + (EXTREMA_LABEL_OFFSET if is_high else -EXTREMA_LABEL_OFFSET),
            t.strftime("%I:%M %p").lstrip('0'),
            ha='center',
            va='bottom' if is_high else 'top',
            fontsize=EXTREMA_FONT_SIZE,
            fontweight='bold'
        )


def shade_day_night(ax, local_times, local_tz):
    location = LocationInfo(
        name=STATION_NAME,
        region="Canada",
        timezone=TIMEZONE,
        latitude=LATITUDE,
        longitude=LONGITUDE,
    )

    start_time = min(local_times)
    end_time   = max(local_times)

    current_day = start_time.date()
    while datetime.combine(current_day, datetime.min.time(), tzinfo=local_tz) < end_time:
        s       = sun(location.observer, date=current_day, tzinfo=local_tz)
        sunrise = s["sunrise"]
        sunset  = s["sunset"]

        day_start = datetime.combine(current_day, datetime.min.time(), tzinfo=local_tz)
        day_end   = day_start + timedelta(days=1)

        # Night: midnight → sunrise
        night_start_1 = max(day_start, start_time)
        night_end_1   = min(sunrise, end_time)
        if night_start_1 < night_end_1:
            ax.axvspan(night_start_1, night_end_1, color="black", alpha=0.15, zorder=0)

        # Night: sunset → midnight
        night_start_2 = max(sunset, start_time)
        night_end_2   = min(day_end, end_time)
        if night_start_2 < night_end_2:
            ax.axvspan(night_start_2, night_end_2, color="black", alpha=0.15, zorder=0)

        current_day += timedelta(days=1)


def get_tide_plot():
    now      = datetime.now(timezone.utc)
    tide_data = get_tide_data(now)

    local_tz = ZoneInfo(TIMEZONE)

    parsed = [
        (
            datetime.fromisoformat(d["eventDate"].replace("Z", "+00:00")).astimezone(local_tz),
            d["value"]
        )
        for d in tide_data
    ]
    parsed.sort(key=lambda x: x[0])

    local_times = [p[0] for p in parsed]
    levels      = [p[1] for p in parsed]
    now_local   = now.astimezone(local_tz)

    fig, ax = plt.subplots(figsize=FIGURE_SIZE)

    shade_day_night(ax, local_times, local_tz)

    ax.plot(local_times, levels, color='black', linewidth=TIDE_LINE_WIDTH, zorder=2)

    label_extrema(ax, local_times, levels)

    ax.axvline(now_local, color="black", linestyle="--", linewidth=NOW_LINE_WIDTH, alpha=0.8, zorder=4)

    ax.set_title(f"{STATION_NAME} Tides", fontsize=14, fontweight='bold')

    current_time_str = f"Updated: {now_local.strftime('%Y-%m-%d %I:%M %p').lstrip('0')}"
    fig.text(0.98, 0.97, current_time_str, ha='right', va='top', fontsize=10, fontweight='bold')

    banner = fetch_banner()
    if banner:
        print(f"Displaying message: {banner!r}")
        fig.text(0.02, 0.97, banner, ha='left', va='top', fontsize=12, fontweight='bold')

    ax.spines['bottom'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    ax.set_ylim(Y_MIN, Y_MAX)
    ax.set_xlim(local_times[0], local_times[-1])
    ax.set_yticks(Y_TICKS)
    ax.tick_params(axis='y', labelsize=TICK_FONT_SIZE)
    for label in ax.get_yticklabels():
        label.set_fontweight('bold')

    ax.yaxis.grid(True, linestyle=':', linewidth=0.8, color='black', alpha=0.7)
    ax.set_xticks([])
    ax.set_ylabel("Water Level (m)")
    fig.subplots_adjust(left=0.055, right=0.995, top=0.88, bottom=0.02)

    os.makedirs('plots', exist_ok=True)
    filename = f'plots/{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.png'
    plt.savefig(filename, dpi=PLOT_DPI)
    plt.close(fig)
    print(f"Saved: {filename}")
    return filename


if __name__ == "__main__":
    get_tide_plot()
