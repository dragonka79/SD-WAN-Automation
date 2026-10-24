
import requests
from pathlib import Path
from dotenv import load_dotenv
import os
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables
load_dotenv()

VMANAGE_HOST = os.getenv("VMANAGE_HOST", "10.0.200.10")
VMANAGE_PORT = os.getenv("VMANAGE_PORT", "8443")
VMANAGE_USERNAME = os.getenv("VMANAGE_USERNAME")
VMANAGE_PASSWORD = os.getenv("VMANAGE_PASSWORD")

BASE_URL = f"https://{VMANAGE_HOST}:{VMANAGE_PORT}"
COOKIE_FILE = Path("vmanage-cookies.txt")
OUTPUT_FILE = Path("output/vmanage/device_templates.txt")


def main():
    if not VMANAGE_USERNAME or not VMANAGE_PASSWORD:
        raise ValueError(
            "VMANAGE_USERNAME or VMANAGE_PASSWORD is missing from .env"
        )

    session = requests.Session()
    session.verify = False

    # Authenticate to vManage
    login_url = f"{BASE_URL}/j_security_check"

    login_response = session.post(
        login_url,
        data={
            "j_username": VMANAGE_USERNAME,
            "j_password": VMANAGE_PASSWORD,
        },
        timeout=30,
    )
    login_response.raise_for_status()

    # Check whether authentication succeeded
    if "JSESSIONID" not in session.cookies:
        raise RuntimeError(
            "vManage authentication may have failed. "
            "Check credentials and the login response."
        )

    # Save cookies for reuse by other scripts
    COOKIE_FILE.write_text(
        "\n".join(
            f"{cookie.name}={cookie.value}"
            for cookie in session.cookies
        ),
        encoding="utf-8",
    )

    # Retrieve device templates
    templates_url = f"{BASE_URL}/dataservice/template/device"
    response = session.get(templates_url, timeout=30)
    response.raise_for_status()

    data = response.json()
    templates = data.get("data", [])

    if not templates:
        print("No device templates were returned by vManage.")

    # Format output
    lines = []

    for template in templates:
        name = template.get("templateName", "N/A")
        template_id = template.get("templateId", "N/A")
        device_type = template.get("deviceType", "N/A")
        attached_devices = template.get("devicesAttached", 0)

        lines.append(
            f"Name: {name} | "
            f"ID: {template_id} | "
            f"Type: {device_type} | "
            f"Attached devices: {attached_devices}"
        )

    # Save output to file
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        "\n".join(lines) + ("\n" if lines else ""),
        encoding="utf-8",
    )

    # Display results
    for line in lines:
        print(line)

    print(f"\nTotal templates: {len(templates)}")
    print(f"Output saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
