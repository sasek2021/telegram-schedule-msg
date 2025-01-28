import streamlit as st
import asyncio
import time
from datetime import datetime
from telethon import TelegramClient
import requests

# Google Apps Script URL for fetching data
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxbjL5HKI-EleVzQZ4s9nQCnvXsrwh5FHciXjlRshue8wOhrN7lUvJgVAH7wNrXEWi4PQ/exec"

# Store clients globally
clients = {}

async def initialize_clients():
    """
    Initialize Telegram clients from configuration data.
    :return: Dictionary with phone numbers as keys and Telegram clients as values.
    """
    global clients
    config_data = fetch_sheet_data("TelegramConfig")

    for config in config_data:
        api_id = config.get("api_id")
        api_hash = config.get("api_hash")
        phone = config.get("phone")

        if api_id and api_hash and phone:
            try:
                client = TelegramClient(f"session_{phone}", api_id, api_hash)
                clients[phone] = client
                st.success(f"Initialized client for {phone}.")
            except Exception as e:
                st.error(f"Failed to initialize client for {phone}: {e}")
        else:
            st.warning(f"Invalid configuration: {config}")


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
        st.error(f"Error fetching data from '{sheet_name}': {e}")
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
        st.success(f"Message sent to {group_id}: {message}")
    except Exception as e:
        st.error(f"Failed to send message to {group_id}: {e}")


async def process_schedules(sheet_name="ScheduleMessage"):
    """
    Process schedules for specific accounts and send messages.
    :param sheet_name: Sheet name to fetch schedule data.
    """
    schedules = fetch_sheet_data(sheet_name)

    if not schedules:
        st.info("No schedules found.")
        return

    tasks = []

    for entry in schedules:
        phone = entry.get("phone")  # Identify the account to use
        send_time = entry.get("send_time")
        group_id = entry.get("group_id")
        message = entry.get("message")
        media = entry.get("media")

        if phone and phone in clients and send_time and group_id and message:
            client = clients[phone]
            tasks.append(schedule_message(client, send_time, group_id, message, media))
        else:
            st.warning(f"Skipping invalid or unassigned schedule entry: {entry}")

    if tasks:
        await asyncio.gather(*tasks)
    else:
        st.info("No valid schedules to process.")


async def schedule_message(client, send_time, group_id, message, media=None):
    """
    Schedule a message to be sent at a specific time.
    :param client: Initialized TelegramClient instance.
    :param send_time: Scheduled time (format: '%Y-%m-%d %H:%M').
    :param group_id: Group ID or username.
    :param message: Text message.
    :param media: Optional media file.
    """
    try:
        now = datetime.now()
        formatted_now = now.strftime("%Y-%m-%d %H:%M")
        send_time_obj = datetime.strptime(send_time, "%Y-%m-%d %H:%M")
        if formatted_now == send_time:
            await send_message(client, group_id, message, media)
    except ValueError:
        st.error(f"Invalid send_time format: {send_time}. Use '%Y-%m-%d %H:%M'.")
    except Exception as e:
        st.error(f"Error scheduling message for {group_id}: {e}")


async def check_and_process_schedules():
    """
    Continuously check for new schedules and process them.
    """
    while True:
        await process_schedules()
        st.info("Waiting for the next check...")
        await asyncio.sleep(60)  # Check every 60 seconds


async def main():
    """
    Main function to initialize clients and start the continuous scheduling check.
    """
    await initialize_clients()
    await check_and_process_schedules()


# Streamlit UI
st.title("Telegram Scheduler with Streamlit")
st.write("This tool allows you to schedule and manage Telegram messages dynamically.")

if st.button("Start Scheduler"):
    asyncio.run(main())
