"""
vManage API client.

This module provides a small Python client for interacting with the
Cisco SD-WAN vManage REST API.

The client currently supports:
    - Creating an HTTP session
    - Authenticating to vManage
    - Retrieving the list of devices from /dataservice/device

A requests.Session() is used so that the authentication session
(JSESSIONID cookie) is automatically reused for subsequent API calls.

SSL certificate verification is disabled by default because this
lab uses the vManage self-signed certificate. This should be enabled
in a production environment with a trusted certificate.
"""

import requests

class VManageClient:
    def __init__(self, host, username, password, verify_ssl=False):
        # Store the vManage connection and authentication parameters.
        self.base_url = f"https://{host}"
        self.username = username
        self.password = password

        # Use one persistent HTTP session so authentication cookies
        # are automatically reused for subsequent API requests.
        self.session = requests.Session()
        self.session.verify = verify_ssl

    def login(self):
        # Authenticate to vManage and establish an authenticated session.
        url = f"{self.base_url}/j_security_check"

        payload = {
            "j_username": self.username,
            "j_password": self.password,
        }

        response = self.session.post(url, data=payload)

        # Reject an unsuccessful HTTP response.
        if response.status_code != 200:
            raise RuntimeError(
                f"vManage login failed: HTTP {response.status_code}"
            )

        # vManage should return a JSESSIONID cookie after successful login.
        if "JSESSIONID" not in self.session.cookies:
            raise RuntimeError("vManage login failed: no JSESSIONID received")

    def get_devices(self):
        # Retrieve the devices known to vManage.
        url = f"{self.base_url}/dataservice/device"

        response = self.session.get(url)

        # Raise an exception if vManage returns an HTTP error.
        response.raise_for_status()

        # Convert the JSON response into a Python dictionary.
        return response.json()

