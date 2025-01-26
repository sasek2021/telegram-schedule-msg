import json
import asyncio
from datetime import datetime
from telethon import TelegramClient
import requests

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


async def send_message_to_group(client, group_id, message, media=None):
    """
    Send a message or media file to a Telegram group using the provided client.
    
    :param client: Telethon TelegramClient instance.
    :param group_id: Telegram group ID or username.
    :param message: Text message to send.
    :param media: Optional media file to send.
    """
    try:
        await client.start()  # Ensure the client starts successfully
        entity = await client.get_entity(group_id)

        if media:
            await client.send_file(entity, media, caption=message)
        else:
            await client.send_message(entity, message)

        print(f"Message successfully sent to {group_id}.")
    except Exception as e:
        print(f"Failed to send the message to {group_id}. Error: {e}")


async def schedule_message(send_time, group_id, message, media=None, api_id=None, api_hash=None, phone=None):
    """
    Schedule a message to be sent at a specific time.

    :param send_time: The scheduled time in '%Y-%m-%d %H:%M:%S' format.
    :param group_id: Telegram group ID or username.
    :param message: Text message to send.
    :param media: Optional media file to send.
    :param api_id: Telegram API ID.
    :param api_hash: Telegram API Hash.
    :param phone: Telegram account phone number.
    """
    try:
        # Initialize the Telethon client with the given credentials
        client = TelegramClient(phone, api_id, api_hash)

        now = datetime.now()
        send_time_obj = datetime.strptime(send_time, '%Y-%m-%d %H:%M:%S')
        delay = (send_time_obj - now).total_seconds()

        if delay > 0:
            print(f"Waiting {delay:.2f} seconds to send the message at {send_time}...")
            await asyncio.sleep(delay)

        await send_message_to_group(client, group_id, message, media)

        # After the message is sent, disconnect the client
        await client.disconnect()
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
        # Fetch the schedule data from Google Sheets
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
            api_id = entry.get('api_id')  # config api_id
            api_hash = entry.get('api_hash')  # config api_hash
            phone = entry.get('phone')  # config phone

            if send_time and group_id and message and api_id and api_hash and phone:
                print(f"Scheduling message for {send_time}: {message}")
                tasks.append(schedule_message(send_time, group_id, message, media, api_id, api_hash, phone))
            else:
                print(f"Skipping incomplete schedule entry: {entry}")

        # Run all tasks concurrently
        if tasks:
            await asyncio.gather(*tasks)
        else:
            print("No valid schedules to process.")
    except Exception as e:
        print(f"Error processing schedule: {e}")


async def initialize_clients_and_send_messages():
    """
    Initialize the clients from the fetched configurations and schedule messages.
    """
    # Fetch the configuration data from the Google Sheet (assuming it returns an array of dictionaries)
    config_data = fetch_sheet_data('TelegramConfig')

    tasks = []
    
    # Iterate through each entry in the config_data array and extract credentials
    for config in config_data:
        API_ID = config.get('api_id')  # Adjust based on how your data is structured
        API_HASH = config.get('api_hash')  # Adjust based on how your data is structured
        PHONE = config.get('phone')  # Assuming phone is a string like '+85599773248'

        if API_ID and API_HASH and PHONE:
            print(f"Client initialized for phone: {PHONE}")

            # Add the task to process scheduling for this client
            tasks.append(process_schedule())

    # Run all tasks concurrently
    if tasks:
        await asyncio.gather(*tasks)
    else:
        print("No valid configurations to process.")


async def main():
    """
    Main function to initialize clients and process scheduled messages.
    """
    await initialize_clients_and_send_messages()


# Run the main event loop
if __name__ == "__main__":
    asyncio.run(main())
