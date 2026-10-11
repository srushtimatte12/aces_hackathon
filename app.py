import math
import os

import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request

app = Flask(__name__)

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

NASA_FIRMS_MAP_KEY = (
    os.getenv("NASA_FIRMS_MAP_KEY", "").strip().strip('"').strip("'")
)

DEFAULT_BOUNDS = {
    "west": 73.5,
    "east": 74.5,
    "south": 18.0,
    "north": 19.0,
    "days": 1,
}


def parse_float(value, fallback):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return fallback
    if not math.isfinite(number):
        return fallback
    return number


def build_map_svg(bounds, fire_count):
    west = float(bounds["west"])
    south = float(bounds["south"])
    east = float(bounds["east"])
    north = float(bounds["north"])

    left = 80
    top = 60
    width = 520
    height = 280

    x1 = left + ((west - west) / max(east - west, 1e-6)) * width
    x2 = left + ((east - west) / max(east - west, 1e-6)) * width
    y1 = top + ((north - north) / max(north - south, 1e-6)) * height
    y2 = top + ((north - south) / max(north - south, 1e-6)) * height

    box_x = left + 12
    box_y = top + 18
    box_w = width - 24
    box_h = height - 36

    return f"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 400" role="img" aria-label="Fire analysis map preview">
      <rect width="100%" height="100%" fill="#edf3ff"/>
      <rect x="{box_x}" y="{box_y}" width="{box_w}" height="{box_h}" rx="12" fill="#dfeaf9" stroke="#2b3a52" stroke-width="2"/>
      <rect x="{left}" y="{top}" width="{width}" height="{height}" fill="none" stroke="#56d6b0" stroke-width="2" opacity="0.9"/>
      <circle cx="{left + 160}" cy="{top + 120}" r="18" fill="#ff7777" opacity="0.82"/>
      <circle cx="{left + 260}" cy="{top + 180}" r="14" fill="#ff7777" opacity="0.8"/>
      <circle cx="{left + 430}" cy="{top + 140}" r="20" fill="#ff7777" opacity="0.8"/>
      <text x="40" y="36" font-size="18" fill="#0b1120" font-family="Arial, sans-serif">Area preview</text>
      <text x="40" y="377" font-size="15" fill="#0b1120" font-family="Arial, sans-serif">Detected fires: {fire_count}</text>
      <text x="420" y="377" font-size="15" fill="#0b1120" font-family="Arial, sans-serif">{bounds['west']}, {bounds['south']} to {bounds['east']}, {bounds['north']}</text>
    </svg>
    """.strip()


def fetch_analysis(bounds):
    bounds = {
        "west": parse_float(bounds.get("west"), DEFAULT_BOUNDS["west"]),
        "east": parse_float(bounds.get("east"), DEFAULT_BOUNDS["east"]),
        "south": parse_float(bounds.get("south"), DEFAULT_BOUNDS["south"]),
        "north": parse_float(bounds.get("north"), DEFAULT_BOUNDS["north"]),
        "days": int(bounds.get("days", DEFAULT_BOUNDS["days"])) if str(bounds.get("days", DEFAULT_BOUNDS["days"])) else DEFAULT_BOUNDS["days"],
    }

    if bounds["west"] >= bounds["east"]:
        raise ValueError("Western longitude must be less than eastern longitude.")
    if bounds["south"] >= bounds["north"]:
        raise ValueError("Southern latitude must be less than northern latitude.")
    if bounds["days"] not in {1, 2, 3, 5, 7, 10}:
        raise ValueError("Days must be one of 1, 2, 3, 5, 7, or 10.")

    if not NASA_FIRMS_MAP_KEY:
        raise ValueError(
            "NASA_FIRMS_MAP_KEY is missing. Add it to the .env file before running the fire analysis."
        )

    url = (
        "https://firms.modaps.eosdis.nasa.gov/api/area/csv/"
        f"{NASA_FIRMS_MAP_KEY}/VIIRS_SNPP_NRT/"
        f"{bounds['west']},{bounds['south']},{bounds['east']},{bounds['north']}/"
        f"{bounds['days']}"
    )

    response = requests.get(url, timeout=30)
    text = response.text.strip()

    if response.status_code != 200:
        raise RuntimeError(f"NASA FIRMS request failed with status {response.status_code}: {text[:200]}")

    lines = [line for line in text.splitlines() if line.strip()]
    if not lines or not lines[0].lower().startswith("latitude"):
        raise RuntimeError(f"Unexpected NASA FIRMS response: {text[:200]}")

    fire_count = max(0, len(lines) - 1)
    return {
        "fire_count": fire_count,
        "weather": {
            "temperature": None,
            "wind_speed": None,
            "humidity": None,
            "wind_direction": None,
        },
    }


@app.route("/", methods=["GET", "POST"])
def index():
    defaults = DEFAULT_BOUNDS.copy()
    result = None
    error = None
    map_html = None

    if request.method == "POST":
        defaults = {
            "west": request.form.get("west", DEFAULT_BOUNDS["west"]),
            "east": request.form.get("east", DEFAULT_BOUNDS["east"]),
            "south": request.form.get("south", DEFAULT_BOUNDS["south"]),
            "north": request.form.get("north", DEFAULT_BOUNDS["north"]),
            "days": request.form.get("days", DEFAULT_BOUNDS["days"]),
        }

        try:
            result = fetch_analysis(defaults)
            map_html = build_map_svg(defaults, result["fire_count"])
        except ValueError as exc:
            error = str(exc)
        except RuntimeError as exc:
            error = str(exc)

    return render_template("index.html", defaults=defaults, result=result, error=error, map_html=map_html)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
