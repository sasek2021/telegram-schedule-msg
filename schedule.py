import json
import asyncio
from datetime import datetime
from telethon import TelegramClient
import requests

# # Replace these with your own values from my.telegram.org
# API_ID = '22130231'
# API_HASH = 'fadba380975fef105f831fdfecbd633b'
# PHONE = '+85599773248'

# # Initialize Telethon client
# client = TelegramClient('session_name', API_ID, API_HASH)

# Google Apps Script URL for fetching data
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxbjL5HKI-EleVzQZ4s9nQCnvXsrwh5FHciXjlRshue8wOhrN7lUvJgVAH7wNrXEWi4PQ/exec"


def fetch_sheet_data(sheet_name="ScheduleMessage"):
    """
    Fetch data from a specific sheet in Google Sheets via Google Apps Script.

    :param sheet_name: Name of the sheet to fetch data from (default is "ScheduleMessage").
    :return: Parsed JSON data from the Google Apps Script.
    :raises: Exception if the request fails.
    """
    try:
        response = requests.get(SCRIPT_URL, params={"sheetName": sheet_name})
        response.raise_for_status()  # Raise an HTTPError for bad responses

        data = response.json()
        print(f"Fetched JSON data: {json.dumps(data, indent=2)}")
        return data
    except requests.RequestException as e:
        print(f"Error fetching data from sheet '{sheet_name}': {e}")
        raise


# Fetch the configuration data from the Google Sheet (assuming it returns an array of dictionaries)
config_data = fetch_sheet_data('TelegramConfig')

# Iterate through each entry in the config_data array and extract credentials
for config in config_data:
    API_ID = config.get('api_id')  # Adjust based on how your data is structured
    API_HASH = config.get('api_hash')  # Adjust based on how your data is structured
    PHONE = config.get('phone')  # Assuming phone is a string like '+85599773248'

    if API_ID and API_HASH and PHONE:
        print(f"Client initialized for phone: {PHONE}")

        # Initialize the Telethon client with the fetched credentials
        client = TelegramClient('session_name', API_ID, API_HASH)
        print(f"Client initialized for phone: {PHONE}")

        # Perform any additional operations (such as sending messages)
        # Example: you can add your send_message_to_group or other functions here
        break  # Stop after using the first valid config, remove if you want to process all configs
    else:
        print("Invalid configuration, skipping this entry.")



async def send_message_to_group(group_id, message, media=None):
    """
    Send a message or media file to a Telegram group.

    :param group_id: Telegram group ID or username.
    :param message: Text message to send.
    :param media: Optional media file to send.
    """
    try:
        await client.start(phone=PHONE)
        entity = await client.get_entity(group_id)

        if media:
            await client.send_file(entity, media, caption=message)
        else:
            await client.send_message(entity, message)

        print(f"Message successfully sent to {group_id}.")
    except Exception as e:
        print(f"Failed to send the message to {group_id}. Error: {e}")


async def schedule_message(send_time, group_id, message, media=None):
    """
    Schedule a message to be sent at a specific time.

    :param send_time: The scheduled time in '%Y-%m-%d %H:%M:%S' format.
    :param group_id: Telegram group ID or username.
    :param message: Text message to send.
    :param media: Optional media file to send.
    """
    try:
        now = datetime.now()
        send_time_obj = datetime.strptime(send_time, '%Y-%m-%d %H:%M:%S')
        delay = (send_time_obj - now).total_seconds()

        if delay > 0:
            print(f"Waiting {delay:.2f} seconds to send the message at {send_time}...")
            await asyncio.sleep(delay)

        await send_message_to_group(group_id, message, media)
    except ValueError:
        print(f"Invalid send_time format: {send_time}. Use '%Y-%m-%d %H:%M:%S'.")
    except Exception as e:
        print(f"Error scheduling message: {e}")


async def process_schedule(sheet_name="ScheduleMessage"):
    """
    Process the schedule data fetched from Google Sheets.

    :param sheet_name: Name of the sheet to fetch data from.
    """
    try:
        # Fetch the schedule data from Google Sheets (you need to define `fetch_sheet_data`)
        schedules = fetch_sheet_data(sheet_name)
        print(f"Fetched schedules: {schedules}")

        if not schedules:
            print("No schedules found in the sheet.")
            return

        tasks = []
        for entry in schedules:
            send_time = entry.get('send_time')
            group_id = entry.get('group_id')
            message = entry.get('message')
            media = entry.get('media')  # Optional field

            if send_time and group_id and message:
                print(f"Scheduling message for {send_time}: {message}")
                tasks.append(schedule_message(send_time, group_id, message, media))
            else:
                print(f"Skipping incomplete schedule entry: {entry}")

        # Run all tasks concurrently
        if tasks:
            await asyncio.gather(*tasks)
        else:
            print("No valid schedules to process.")
    except Exception as e:
        print(f"Error processing schedule: {e}")



async def main():
    """
    Main function to process scheduled messages.
    """
    sheet_name = "ScheduleMessage"
    await process_schedule(sheet_name)


# Run the main event loop
if __name__ == "__main__":
    asyncio.run(main())