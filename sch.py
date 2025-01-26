import json
import asyncio
from datetime import datetime
from telethon import TelegramClient


# Replace these with your own values from my.telegram.org
api_id = '22130231'
api_hash = 'fadba380975fef105f831fdfecbd633b'
phone = '+85599773248'

client = TelegramClient('session_name', api_id, api_hash)

async def send_message_to_group(group_id, message, media=None):
    try:
        # Connect to the client
        await client.start(phone=phone)

        # Get the group entity (by username or ID)
        entity = await client.get_entity(group_id)

        if media:
            await client.send_file(entity, media, caption=message)
        else:
            await client.send_message(entity, message)

        print(f"Message successfully sent to {group_id}.")
    except Exception as e:
        print(f"Failed to send the message to {group_id}. Error: {e}")

async def schedule_message(send_time, group_id, message, media=None):
    now = datetime.now()
    send_time_obj = datetime.strptime(send_time, '%Y-%m-%d %H:%M:%S')
    delay = (send_time_obj - now).total_seconds()

    if delay > 0:
        print(f"Waiting to send the message at {send_time}...")
        await asyncio.sleep(delay)

    await send_message_to_group(group_id, message, media)

async def process_schedule(schedule_file):
    try:
        # Load schedule from the JSON file
        with open(schedule_file, 'r') as file:
            schedules = json.load(file)

        tasks = []
        for entry in schedules:
            send_time = entry['send_time']
            group_id = entry['group_id']
            message = entry['message']
            media = entry.get('media')  # Media is optional

            tasks.append(schedule_message(send_time, group_id, message, media))

        # Run all scheduled tasks concurrently
        await asyncio.gather(*tasks)

    except Exception as e:
        print(f"Error processing schedule: {e}")

# JSON schedule file
schedule_file = 'schedule.json'

# Run the schedule processor
asyncio.run(process_schedule(schedule_file))