
import json
import os
from pathlib import Path

import requests
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

VMANAGE_HOST = os.getenv("VMANAGE_HOST", "10.0.200.10")
VMANAGE_PORT = os.getenv("VMANAGE_PORT", "8443")
VMANAGE_USERNAME = os.getenv("VMANAGE_USERNAME")
VMANAGE_PASSWORD = os.getenv("VMANAGE_PASSWORD")

BASE_URL = f"https://{VMANAGE_HOST}:{VMANAGE_PORT}"

COOKIE_FILE = Path("vmanage-cookies.txt")
OUTPUT_DIR = Path("output/vmanage")
LIST_OUTPUT_FILE = OUTPUT_DIR / "device_templates.txt"

TARGET_TEMPLATES = {
    "Default_SDBranch_C8000V_Template_V01":
        "4fabafe3-243d-4160-ac3a-57a1d54c360b",
    "Factory_Default_C8000V_V01":
        "04192977-b568-45ab-aad4-8b35b72d29e2",
}


def authenticate():
    if not VMANAGE_USERNAME or not VMANAGE_PASSWORD:
        raise ValueError(
            "VMANAGE_USERNAME or VMANAGE_PASSWORD is missing from .env"
        )

    session = requests.Session()
    session.verify = False

    response = session.post(
        f"{BASE_URL}/j_security_check",
        data={
            "j_username": VMANAGE_USERNAME,
            "j_password": VMANAGE_PASSWORD,
        },
        timeout=30,
    )
    response.raise_for_status()

    if "JSESSIONID" not in session.cookies:
        raise RuntimeError(
            "Authentication may have failed. Check credentials "
            "and the vManage login response."
        )

    COOKIE_FILE.write_text(
        "\n".join(
            f"{cookie.name}={cookie.value}"
            for cookie in session.cookies
        ),
        encoding="utf-8",
    )

    return session


def get_templates(session):
    response = session.get(
        f"{BASE_URL}/dataservice/template/device",
        timeout=30,
    )
    response.raise_for_status()

    return response.json().get("data", [])


def save_template_details(session, template_name, template_id):
    url = (
        f"{BASE_URL}/dataservice/template/device/object/"
        f"{template_id}"
    )
    output_file = OUTPUT_DIR / f"{template_name}.json"

    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
        details = response.json()

        output_file.write_text(
            json.dumps(details, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        print(f"Saved details: {output_file}")
        return True

    except (requests.RequestException, ValueError) as error:
        error_file = OUTPUT_DIR / f"{template_name}_error.txt"
        error_file.write_text(
            f"Template: {template_name}\n"
            f"ID: {template_id}\n"
            f"Endpoint: {url}\n"
            f"Error: {error}\n",
            encoding="utf-8",
        )

        print(f"Could not retrieve {template_name}: {error}")
        print(f"Error details saved to: {error_file}")
        return False


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    session = authenticate()
    templates = get_templates(session)

    lines = []
    templates_by_id = {}

    for template in templates:
        name = template.get("templateName", "N/A")
        template_id = template.get("templateId", "N/A")
        device_type = template.get("deviceType", "N/A")
        attached_devices = template.get("devicesAttached", 0)

        templates_by_id[template_id] = template

        lines.append(
            f"Name: {name} | "
            f"ID: {template_id} | "
            f"Type: {device_type} | "
            f"Attached devices: {attached_devices}"
        )

    LIST_OUTPUT_FILE.write_text(
        "\n".join(lines) + ("\n" if lines else ""),
        encoding="utf-8",
    )

    print(f"Total templates: {len(templates)}")
    print(f"Template list saved to: {LIST_OUTPUT_FILE}\n")

    for line in lines:
        print(line)

    print("\n--- Inspecting selected C8000V templates ---")

    for name, template_id in TARGET_TEMPLATES.items():
        template = templates_by_id.get(template_id)

        if template is None:
            print(f"\nTemplate not found in list: {name} ({template_id})")
            continue

        if template.get("deviceType") != "vedge-C8000V":
            print(
                f"\nSkipping {name}: unexpected device type "
                f"{template.get('deviceType')}"
            )
            continue

        print(f"\nInspecting: {name}")
        save_template_details(session, name, template_id)


if __name__ == "__main__":
    main()
