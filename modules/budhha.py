import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message
from utils.misc import modules_help, prefix

# --- API URL ---
BUDDHA_API_URL = "https://buddha-api.com/api/random"


# --- Helper Function ---
async def fetch_json(url):
    """Asynchronously fetches JSON data from a URL."""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
        except aiohttp.ClientError:
            return None


# --- Command Handler ---
@Client.on_message(filters.command(["buddha"], prefix))
async def buddha_quote_handler(client: Client, message: Message):
    """Handles the .buddha command to fetch a random quote with an image."""
    is_self = message.from_user and message.from_user.is_self
    status_message = await (message.edit_text("<code>🧘‍♂️ Fetching a wise quote...</code>") if is_self else message.reply("<code>🧘‍♂️ Fetching a wise quote...</code>"))

    quote_data = await fetch_json(BUDDHA_API_URL)

    if quote_data and "text" in quote_data and "byName" in quote_data:
        text = quote_data.get("text")
        author = quote_data.get("byName")
        image_url = quote_data.get("byImage")
        
        caption = f"<blockquote>{text}</blockquote>\n\n<b>— {author}</b>"
        
        try:
            if image_url:
                await client.send_photo(
                    chat_id=message.chat.id,
                    photo=image_url,
                    caption=caption
                )
                await status_message.delete()
            else:
                # If no image is available, send the quote as text.
                await status_message.edit_text(caption)

        except Exception as e:
            # Handle potential errors during file sending
            await status_message.edit_text(f"<code>❌ Error sending quote: {e}</code>")
    else:
        await status_message.edit_text("<code>❌ Sorry, I couldn't fetch a quote. The API might be down.</code>")


# --- Help Documentation ---
modules_help["buddha_quotes"] = {
    "buddha": "Get a random wise quote as an image with a caption.",
}
