import requests
import json

# Define the Google Apps Script URL
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxbjL5HKI-EleVzQZ4s9nQCnvXsrwh5FHciXjlRshue8wOhrN7lUvJgVAH7wNrXEWi4PQ/exec"

def fetch_sheet_name(sheet_name="ScheduleMessage"):
    """
    Fetch data from a specific sheet in Google Sheets.

    :param sheet_name: Name of the sheet to fetch data from (default is "ScheduleMessage").
    :return: Parsed JSON data from the Google Apps Script.
    :raises: Exception if the request fails.
    """
    try:
        # Add the sheet name as a query parameter
        params = {"sheetName": sheet_name}
        response = requests.get(SCRIPT_URL, params=params)

        # Raise an error if the response status code indicates a failure
        response.raise_for_status()

        # Parse the JSON response
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data from sheet '{sheet_name}': {e}")
        raise

def create_data_by_sheet_name(config=None, data=None):
    """
    Send data to the Google Apps Script with configuration options.

    :param config: Configuration options as a dictionary (default is {"isContact": True}).
    :param data: Data to send as a dictionary (default is an empty dictionary).
    :return: The response object from the request.
    :raises: Exception if the request fails.
    """
    if config is None:
        config = {"isContact": True}
    if data is None:
        data = {}

    try:
        # Merge config and data dictionaries
        payload = {**config, **data}

        # Send the POST request with JSON payload
        response = requests.post(SCRIPT_URL, json=payload)

        # Raise an error if the response status code indicates a failure
        response.raise_for_status()

        return response.json()  # Return parsed JSON response
    except requests.RequestException as e:
        print(f"Error sending data: {e}")
        raise
