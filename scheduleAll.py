import json
import asyncio
from datetime import datetime
from telethon import TelegramClient
import requests

# Google Apps Script URL for fetching data
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxbjL5HKI-EleVzQZ4s9nQCnvXsrwh5FHciXjlRshue8wOhrN7lUvJgVAH7wNrXEWi4PQ/exec"

async def initialize_clients():
    """
    Initialize Telegram clients from configuration data.
    :return: List of initialized Telegram clients.
    """
    config_data = fetch_sheet_data("TelegramConfig")
    clients = []

    for config in config_data:
        api_id = config.get("api_id")
        api_hash = config.get("api_hash")
        phone = config.get("phone")

        if api_id and api_hash and phone:
            try:
                client = TelegramClient(f"session_{phone}", api_id, api_hash)
                clients.append(client)
                print(f"Initialized client for {phone}.")
            except Exception as e:
                print(f"Failed to initialize client for {phone}: {e}")
        else:
            print(f"Invalid configuration: {config}")

    return clients


def fetch_sheet_data(sheet_name="ScheduleMessage"):
    """
    Fetch data from a specific Google Sheet via Google Apps Script.
    :param sheet_name: Name of the sheet.
    :return: Parsed JSON data.
    """
    try:
        response = requests.get(SCRIPT_URL, params={"sheetName": sheet_name})
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data from '{sheet_name}': {e}")
        return []


async def send_message(client, group_id, message, media=None):
    """
    Send a message or media to a Telegram group.
    :param client: Initialized TelegramClient instance.
    :param group_id: Group ID or username.
    :param message: Text message.
    :param media: Optional media file.
    """
    try:
        await client.start()
        entity = await client.get_entity(group_id)
        if media:
            await client.send_file(entity, media, caption=message)
        else:
            await client.send_message(entity, message)
        print(f"Message sent to {group_id}: {message}")
    except Exception as e:
        print(f"Failed to send message to {group_id}: {e}")


async def schedule_message(client, send_time, group_id, message, media=None):
    """
    Schedule a message to be sent at a specific time.
    :param client: Initialized TelegramClient instance.
    :param send_time: Scheduled time (format: '%Y-%m-%d %H:%M:%S').
    :param group_id: Group ID or username.
    :param message: Text message.
    :param media: Optional media file.
    """
    try:
        now = datetime.now()
        send_time_obj = datetime.strptime(send_time, "%Y-%m-%d %H:%M:%S")
        delay = (send_time_obj - now).total_seconds()

        if delay > 0:
            print(f"Waiting {delay:.2f} seconds to send the message at {send_time}...")
            await asyncio.sleep(delay)

        await send_message(client, group_id, message, media)
    except ValueError:
        print(f"Invalid send_time format: {send_time}. Use '%Y-%m-%d %H:%M:%S'.")
    except Exception as e:
        print(f"Error scheduling message for {group_id}: {e}")


async def process_schedule(client, sheet_name="ScheduleMessage"):
    """
    Process schedules from Google Sheets and send messages.
    :param client: Initialized TelegramClient instance.
    :param sheet_name: Sheet name to fetch schedule data.
    """
    schedules = fetch_sheet_data(sheet_name)

    if not schedules:
        print("No schedules found.")
        return

    tasks = []
    for entry in schedules:
        send_time = entry.get("send_time")
        group_id = entry.get("group_id")
        message = entry.get("message")
        media = entry.get("media")

        if send_time and group_id and message:
            tasks.append(schedule_message(client, send_time, group_id, message, media))
        else:
            print(f"Skipping invalid schedule entry: {entry}")

    if tasks:
        await asyncio.gather(*tasks)
    else:
        print("No valid schedules to process.")


async def main():
    """
    Main function to initialize clients and process schedules.
    """
    clients = await initialize_clients()
    tasks = [process_schedule(client) for client in clients]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
