import os
import sys
import base64
import gzip
from pathlib import Path

import requests
from dotenv import load_dotenv
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Locate the project root from this script's location.
PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

HOST = "https://10.0.200.10:8443"
DEVICE_ID = "10.255.1.1"  # BR_IN
OUTPUT_FILE = PROJECT_ROOT / "output" / "vmanage" / "BR_IN_running_config.txt"

username = os.getenv("VMANAGE_USERNAME")
password = os.getenv("VMANAGE_PASSWORD")

if not username or not password:
    sys.exit("ERROR: VMANAGE_USERNAME or VMANAGE_PASSWORD is missing from .env")

session = requests.Session()
session.verify = False

try:
    # Authenticate to vManage.
    login_response = session.post(
        f"{HOST}/j_security_check",
        data={
            "j_username": username,
            "j_password": password,
        },
        timeout=30,
    )
    login_response.raise_for_status()

    if "JSESSIONID" not in session.cookies:
        sys.exit("ERROR: Login failed; no JSESSIONID cookie received.")

    # Retrieve BR_IN configuration.
    response = session.get(
        f"{HOST}/dataservice/device/config",
        params={"deviceId": DEVICE_ID},
        timeout=60,
    )
    response.raise_for_status()

    # vManage may return a Base64-encoded gzip payload.
    try:
        decoded = base64.b64decode(response.content, validate=True)
        config_bytes = gzip.decompress(decoded)
    except (ValueError, OSError):
        sys.exit(
            "ERROR: Response was not valid Base64-encoded gzip data. "
            f"Content-Type: {response.headers.get('Content-Type')}; "
            f"HTTP status: {response.status_code}. "
            "Configuration was not saved."
        )

    config = config_bytes.decode("utf-8")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(config, encoding="utf-8")

    print(f"Configuration retrieved successfully for device {DEVICE_ID}.")
    print(f"Saved to: {OUTPUT_FILE}")
    print(f"Size: {len(config_bytes)} bytes")

except requests.RequestException as exc:
    sys.exit(f"ERROR: vManage API request failed: {exc}")

    