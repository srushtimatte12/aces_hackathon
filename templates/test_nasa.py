
import os
import requests
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("NASA_FIRMS_MAP_KEY", "").strip()

if not key:
    print("ERROR: NASA key was not found in .env")
else:
    print("NASA key found. Testing connection...")

    url = (
        "https://firms.modaps.eosdis.nasa.gov/api/area/csv/"
        f"{key}/VIIRS_SNPP_NRT/73.5,18.0,74.5,19.0/1"
    )

    try:
        response = requests.get(url, timeout=30)
        print("HTTP status:", response.status_code)
        print("Response preview:", response.text[:500])

        response.raise_for_status()
        print("NASA request completed.")

    except requests.RequestException as exc:
        print("NASA REQUEST FAILED:", repr(exc))
