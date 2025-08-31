import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message
from utils.misc import modules_help, prefix

# --- API Configuration ---
API_URL = "https://girlfriend.revangeapi.workers.dev/revnageapi/chat"

# --- Main Command ---
@Client.on_message(filters.command("gff", prefix) & filters.me)
async def gff_chat(client: Client, message: Message):
    """Interacts with the Shizuka AI API from a query or reply."""
    try:
        query = None
        # Check if the command is a reply to another message
        if message.reply_to_message and message.reply_to_message.text:
            query = message.reply_to_message.text
        # If not a reply, check for text after the command
        elif len(message.command) > 1:
            query = " ".join(message.command[1:])

        # If no query is found, show usage instructions
        if not query:
            await message.edit(
                "<b>Please provide a message or reply to one.</b>\n\n"
                "<b>Usage:</b> <code>.gff [your message]</code>\n"
                "or reply <code>.gff</code> to a message."
            )
            return

        await message.edit("<code>Thinking...</code>")

        # --- Make the API Request ---
        async with aiohttp.ClientSession() as session:
            params = {"prompt": query}
            async with session.get(API_URL, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    ai_reply = data.get("reply", "Sorry, I couldn't get a response.")
                    await message.edit(ai_reply)
                else:
                    error_text = await response.text()
                    await message.edit(
                        f"<b>Error:</b> Received status <code>{response.status}</code> from the API.\n\n"
                        f"<code>{error_text}</code>"
                    )

    except Exception as e:
        await message.edit(f"<b>An error occurred:</b> <code>{e}</code>")


# --- Add to modules_help ---
modules_help["gff"] = {
    "gff [query/reply]": "Chat with the Shizuka AI. You can either provide your message after the command or reply to a text."
}