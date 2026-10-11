import os
import sys
import requests
from dotenv import load_dotenv

# Load the .env file from this project's folder
load_dotenv(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
)

# Strip whitespace and any accidental quotes around the key
key = os.getenv("NASA_FIRMS_MAP_KEY", "").strip().strip('"').strip("'")

if not key:
    print("ERROR: NASA_FIRMS_MAP_KEY was not found in .env")
    sys.exit(1)

# A real FIRMS MAP_KEY is a 32-character alphanumeric string
if len(key) != 32 or not key.isalnum():
    print(
        f"WARNING: your key is {len(key)} characters long. "
        "A valid NASA FIRMS MAP_KEY has 32 letters/digits."
    )
    print("Request one at: https://firms.modaps.eosdis.nasa.gov/api/map_key/")

print("NASA key found. Testing connection...")

# Bounding box: west,south,east,north (Pune region), last 1 day
url = (
    "https://firms.modaps.eosdis.nasa.gov/api/area/csv/"
    f"{key}/VIIRS_SNPP_NRT/73.5,18.0,74.5,19.0/1"
)

try:
    response = requests.get(url, timeout=30)
    text = response.text.strip()

    if response.status_code == 200 and text.lower().startswith("latitude"):
        rows = text.splitlines()
        fire_count = len(rows) - 1  # first line is the CSV header

        print("SUCCESS: NASA FIRMS connection works!")
        if fire_count == 0:
            print("No fire detections in this area in the last 1 day.")
        else:
            print(f"Fire detections found: {fire_count}")
            print("Data preview:")
            print("\n".join(rows[:6]))

    elif "invalid" in text.lower():
        print("ERROR: NASA rejected the key.")
        print("Get a valid key from the official NASA FIRMS page.")

    else:
        print("NASA returned status:", response.status_code)
        print("Response:", text[:300])

except requests.RequestException as error:
    # Avoid printing the URL because it contains the key.
    print("Connection error:", type(error).__name__)
    print("Check your internet connection and try again.")