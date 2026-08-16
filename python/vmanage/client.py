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

        # Store the SSL verification setting.
        self.verify_ssl = verify_ssl

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

        try:
            response = self.session.post(url, data=payload)

        except requests.exceptions.RequestException as e:
            raise RuntimeError(
                f"Unable to connect to vManage during login: {e}"
            ) from e

        # Reject an unsuccessful HTTP response.
        if response.status_code != 200:
            raise RuntimeError(
                f"vManage login failed: HTTP {response.status_code}"
            )

        # vManage should return a JSESSIONID cookie after successful login.
        if "JSESSIONID" not in self.session.cookies:
            raise RuntimeError(
                "vManage login failed: no JSESSIONID received"
            )

    def get_devices(self):
        # Retrieve the devices known to vManage.
        url = f"{self.base_url}/dataservice/device"

        try:
            response = self.session.get(url)

        except requests.exceptions.RequestException as e:
            raise RuntimeError(
                f"Unable to connect to vManage while retrieving devices: {e}"
            ) from e

        # Raise an exception if vManage returns an HTTP error.
        try:
            response.raise_for_status()

        except requests.exceptions.HTTPError as e:
            raise RuntimeError(
                f"vManage device request failed: HTTP "
                f"{response.status_code}"
            ) from e

        # Convert the JSON response into a Python object.
        try:
            data = response.json()

        except ValueError as e:
            raise RuntimeError(
                "vManage returned an invalid JSON response"
            ) from e

        # Validate the expected vManage API response structure.
        if not isinstance(data, dict):
            raise RuntimeError(
                "Unexpected vManage response: expected a JSON object"
            )

        if "data" not in data:
            raise RuntimeError(
                "Unexpected vManage response: 'data' field is missing"
            )

        if not isinstance(data["data"], list):
            raise RuntimeError(
                "Unexpected vManage response: 'data' is not a list"
            )

        return data["data"]

    def get_controllers(self):
        # Retrieve the controllers known to vManage.
        response = self.session.get(
            f"{self.base_url}/dataservice/system/device/controllers",
            verify=False
        )

        # Raise an exception if vManage returns an HTTP error.
        response.raise_for_status()

        # Return only the actual controller information.
        return response.json()["data"]

        