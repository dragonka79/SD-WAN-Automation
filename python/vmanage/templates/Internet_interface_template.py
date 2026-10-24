
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

FEATURE_TEMPLATE_ID = "98b74a6f-0b52-47a2-8a02-8fa9042396ae"


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


def save_device_template_details(session, name, template_id):
    url = f"{BASE_URL}/dataservice/template/device/object/{template_id}"
    response = session.get(url, timeout=30)
    response.raise_for_status()

    output_file = OUTPUT_DIR / f"{name}.json"
    output_file.write_text(
        json.dumps(response.json(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Saved device template: {output_file}")


def inspect_feature_template(session, template_id):
    url = f"{BASE_URL}/dataservice/template/feature"

    print(f"\nRetrieving feature template: {template_id}")

    response = session.get(
        url,
        params={"summary": "true"},
        timeout=30,
    )

    print(f"HTTP status: {response.status_code}")
    response.raise_for_status()

    result = response.json()
    templates = result.get("data", [])

    for template in templates:
        if template.get("templateId") == template_id:
            output_file = (
                OUTPUT_DIR / f"feature_template_{template_id}.json"
            )

            output_file.write_text(
                json.dumps(template, indent=2),
                encoding="utf-8",
            )

            print(f"Template name: {template.get('templateName')}")
            print(f"Template type: {template.get('templateType')}")
            print(f"Device type: {template.get('deviceType')}")
            print(f"Template details saved to: {output_file}")
            print(json.dumps(template, indent=2))
            return template

    print(f"Template ID not found in feature-template list: {template_id}")
    return None

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
    print(f"Template list saved to: {LIST_OUTPUT_FILE}")

    for line in lines:
        print(line)

    print("\n--- Inspecting selected C8000V templates ---")

    for name, template_id in TARGET_TEMPLATES.items():
        template = templates_by_id.get(template_id)

        if template is None:
            print(f"Template not found: {name} ({template_id})")
            continue

        if template.get("deviceType") != "vedge-C8000V":
            print(
                f"Skipping {name}: unexpected device type "
                f"{template.get('deviceType')}"
            )
            continue

        try:
            save_device_template_details(session, name, template_id)
        except (requests.RequestException, ValueError) as error:
            print(f"Failed to inspect {name}: {error}")

    print("\n--- Inspecting VPN interface feature template ---")

    try:
        inspect_feature_template(session, FEATURE_TEMPLATE_ID)
    except (requests.RequestException, ValueError) as error:
        print(f"Feature-template retrieval failed: {error}")


if __name__ == "__main__":
    main()

