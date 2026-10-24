
import json
import os
import sys
from pathlib import Path

import requests
import urllib3
from dotenv import load_dotenv


# --------------------------------------------------
# Configuration
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parents[3]
OUTPUT_DIR = PROJECT_DIR / "output" / "vmanage"

load_dotenv(PROJECT_DIR / ".env")

VMANAGE_HOST = os.getenv("VMANAGE_HOST", "10.0.200.10")
VMANAGE_PORT = os.getenv("VMANAGE_PORT", "8443")
VMANAGE_USERNAME = os.getenv("VMANAGE_USERNAME")
VMANAGE_PASSWORD = os.getenv("VMANAGE_PASSWORD")

BASE_URL = f"https://{VMANAGE_HOST}:{VMANAGE_PORT}"

TARGET_TEMPLATES = {
    "SITE_LAN_VPN1",
    "cEdge_LAN_interface",
}

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# --------------------------------------------------
# Authentication
# --------------------------------------------------

def authenticate():
    if not all(
        [VMANAGE_HOST, VMANAGE_USERNAME, VMANAGE_PASSWORD]
    ):
        raise ValueError(
            "Missing VMANAGE_HOST, VMANAGE_USERNAME, "
            "or VMANAGE_PASSWORD in .env"
        )

    session = requests.Session()
    session.verify = False

    login_url = f"{BASE_URL}/j_security_check"

    response = session.post(
        login_url,
        data={
            "j_username": VMANAGE_USERNAME,
            "j_password": VMANAGE_PASSWORD,
        },
        timeout=30,
    )
    response.raise_for_status()

    if "JSESSIONID" not in session.cookies:
        raise RuntimeError(
            "Authentication failed: JSESSIONID cookie not found."
        )

    print("Authenticated to vManage.")
    return session


# --------------------------------------------------
# Retrieve feature-template list
# --------------------------------------------------

def get_feature_templates(session):
    url = f"{BASE_URL}/dataservice/template/feature"

    response = session.get(
        url,
        params={"summary": "true"},
        timeout=30,
    )
    response.raise_for_status()

    data = response.json().get("data", [])

    print(f"Feature templates returned by vManage: {len(data)}")
    return data


# --------------------------------------------------
# Inspect custom feature templates
# --------------------------------------------------

def inspect_custom_feature_templates(session, templates):
    matches = {
        item.get("templateName"): item
        for item in templates
        if item.get("templateName") in TARGET_TEMPLATES
    }

    for name in sorted(TARGET_TEMPLATES):
        print(f"\n--- Inspecting: {name} ---")

        template = matches.get(name)

        if template is None:
            print("Template not found in the feature-template list.")
            continue

        template_id = template.get("templateId")

        print(f"Template ID: {template_id}")
        print(f"Template type: {template.get('templateType')}")
        print(f"Device type: {template.get('deviceType')}")

        # Retrieve the full feature-template definition.
        url = (
            f"{BASE_URL}/dataservice/template/feature/"
            f"definition/{template_id}"
        )

        response = session.get(url, timeout=30)

        print(f"Definition HTTP status: {response.status_code}")

        if not response.ok:
            print(f"Response body: {response.text}")
            continue

        definition = response.json()

        output_file = OUTPUT_DIR / f"{name}_definition.json"

        output_file.write_text(
            json.dumps(definition, indent=2),
            encoding="utf-8",
        )

        print(f"Definition saved to: {output_file}")
        print(json.dumps(definition, indent=2))


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        session = authenticate()
        templates = get_feature_templates(session)

        inspect_custom_feature_templates(session, templates)

    except (requests.RequestException, ValueError, RuntimeError) as error:
        print(f"Error: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
