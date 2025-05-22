import asyncio
import time

from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import Message

from utils.misc import modules_help, prefix


@Client.on_message(filters.command(["type2", "typewriter2"], prefix) & filters.me)
async def type_cmd(_, message: Message):
    text = message.text.split(maxsplit=1)[1]
    typed = ""

    for char in text:
        typed += char
        await message.edit(typed)
        await asyncio.sleep(0.01)


modules_help["type2"] = {
    "type2</code> <code>| </code><code>typewriter [text]*": "Typing emulation. Don't use a lot of characters, you can receive a lot of floodwaits!"
}