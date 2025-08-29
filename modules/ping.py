#  Moon-Userbot - telegram userbot
#  Copyright (C) 2020-present Moon Userbot Organization
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

import datetime
from time import perf_counter

from pyrogram import Client, filters
from pyrogram.types import Message

from utils.misc import modules_help, prefix

# Store the bot's start time when the module is loaded.
bot_start_time = datetime.datetime.now()


@Client.on_message(filters.command(["ping", "p"], prefix) & filters.me)
async def ping(_, message: Message):
    """
    Handles the /ping command to check the bot's latency and uptime.
    """
    # Record the start time for latency calculation
    start_time = perf_counter()

    # Edit the message to show the user that the ping is in progress
    await message.edit("<b>Pinging...</b>")

    # Record the end time after the first API call (edit message) is complete
    end_time = perf_counter()

    # Calculate the latency in milliseconds
    latency = round((end_time - start_time) * 1000, 2)

    # Calculate the bot's uptime
    current_time = datetime.datetime.now()
    uptime = current_time - bot_start_time
    # Format the uptime to a human-readable string (HH:MM:SS)
    uptime_str = str(uptime).split('.')[0]

    # Create the final, more detailed response message
    response_text = (
        f"🏓 <b>Pong!</b>\n\n"
        f"<b>⚡️ Latency:</b> <code>{latency} ms</code>\n"
        f"<b>⏳ Uptime:</b> <code>{uptime_str}</code>"
    )

    # Edit the message one last time to show the final result
    await message.edit(response_text)


# Update the module help description
modules_help["ping"] = {
    "ping": "Check ping to Telegram servers and bot uptime.",
}