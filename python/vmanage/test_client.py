"""
Test script for the vManage API client.

This script:
    1. Reads the vManage username and password from environment variables.
    2. Creates a VManageClient instance.
    3. Logs in to vManage.
    4. Retrieves /dataservice/device.
    5. Prints the API response.

Credentials are deliberately not stored in this source file.
"""

import os
from client import VManageClient
from datetime import datetime
from pathlib import Path
import json

# vManage uses a self-signed certificate in the lab.
# SSL certificate verification is disabled, so suppress the resulting warning.
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# vManage management/API address.
VMANAGE_HOST = "10.0.200.10"

# Read credentials from environment variables rather than storing
# them directly in the source code.
VMANAGE_USERNAME = os.environ["VMANAGE_USERNAME"]
VMANAGE_PASSWORD = os.environ["VMANAGE_PASSWORD"]


# Create the vManage API client.
client = VManageClient(
    host=VMANAGE_HOST,
    username=VMANAGE_USERNAME,
    password=VMANAGE_PASSWORD,
    verify_ssl=False,
)


# Authenticate and establish the vManage API session.
client.login()


# Retrieve the devices currently known to vManage.
data = client.get_devices()

devices = client.get_devices()

# Directory for generated vManage API output.
OUTPUT_DIR = Path(__file__).resolve().parents[2] / "output" / "vmanage"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Create a timestamped output filename.
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = OUTPUT_DIR / f"devices_{timestamp}.json"

# Save the device inventory as formatted JSON.
with open(output_file, "w") as f:
    json.dump(devices, f, indent=2)

print(f"Device information saved to {output_file}")

# Extract the device inventory from the API response.
devices = data["data"]


# Display a compact summary of the devices.
if not devices:
    print("No devices registered in vManage.")
else:
    for device in devices:
        print(
            f"{device.get('host-name', 'N/A'):20} "
            f"{device.get('system-ip', 'N/A'):15} "
            f"{device.get('device-model', 'N/A'):15} "
            f"{device.get('reachability', 'N/A')}"
        )

