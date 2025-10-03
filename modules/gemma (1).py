import aiohttp
import os
import json
import codecs
from pyrogram import Client, filters
from pyrogram.types import Message

from utils.misc import modules_help, prefix
from utils.scripts import format_exc

# --- Constants ---
API_URL = "https://sii3.top/api/gemma.php"
TELEGRAM_MAX_MSG_LENGTH = 4096
DEFAULT_MODEL = "27b"
AVAILABLE_MODELS = ["4b", "12b", "27b"]

# --- Browser headers to look like a real user ---
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/5.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
}

# --- Reusable function to query the Gemma API ---
async def query_gemma_api(prompt: str, model: str) -> str | None:
    """
    Queries the Gemma API and returns the raw response text.
    Returns None on failure.
    """
    params = {model: prompt}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, data=params, headers=BROWSER_HEADERS, timeout=300) as response:
                if response.status == 200:
                    try:
                        data = await response.json(content_type=None)
                        return data.get("response")
                    except json.JSONDecodeError:
                        print("Gemma API Error: Failed to decode JSON from response.")
                        return None
                else:
                    print(f"Gemma API Error: Received status code {response.status}")
                    return None
    except Exception as e:
        print(f"An exception occurred while querying the Gemma API: {format_exc(e)}")
        return None

# --- Main Gemma Command (Updated for response formatting) ---
@Client.on_message(filters.command("gemma", prefix) & filters.me)
async def gemma_command(client: Client, message: Message):
    """
    Interacts with the Gemma AI models.
    """
    parts = message.text.split(maxsplit=2)
    model = DEFAULT_MODEL
    prompt = ""

    if len(parts) < 2:
        return await message.edit_text(
            "<b>✨ Gemma AI</b>\n\n"
            "<b>Usage:</b> <code>.gemma [-model] &lt;your prompt&gt;</code>\n\n"
            "<b>Models:</b>\n"
            "• <code>-4b</code>\n"
            "• <code>-12b</code>\n"
            "• <code>-27b</code> (Default)\n\n"
            "<b>Example:</b> <code>.gemma -12b write a short story about a robot who discovers music</code>"
        )

    potential_flag = parts[1].replace("-", "")
    if potential_flag in AVAILABLE_MODELS:
        model = potential_flag
        if len(parts) > 2:
            prompt = parts[2]
        else:
            return await message.edit_text("<b>Error:</b> Please provide a prompt after the model flag.")
    else:
        prompt = message.text.split(maxsplit=1)[1]

    status_msg = await message.edit_text(f"<b>✨ Thinking with Gemma ({model})...</b>")

    api_response = await query_gemma_api(prompt, model)

    if not api_response:
        return await status_msg.edit_text("<b>❗️ Error:</b> The Gemma API did not return a valid response.")

    # --- NEW: Process the raw string to handle escape sequences like \n ---
    # This converts the string '\\n' into an actual newline character.
    try:
        processed_text = codecs.decode(api_response, 'unicode_escape')
    except Exception:
        # Fallback for any decoding errors
        processed_text = api_response.replace('\\n', '\n')
    
    final_text = processed_text.strip()

    if len(final_text) > TELEGRAM_MAX_MSG_LENGTH:
        await status_msg.edit_text("<b>Response is too long, sending as a file...</b>")
        file_path = f"gemma_response_{message.id}.txt"
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(final_text)

            await client.send_document(
                chat_id=message.chat.id,
                document=file_path,
                caption=f"<b>✨ Gemma AI ({model}) Response</b>\n\n<b>Prompt:</b> <code>{prompt[:100]}...</code>",
                reply_to_message_id=message.id
            )
            await status_msg.delete()
        except Exception as e:
            await status_msg.edit_text(f"<b>Error sending file:</b>\n<code>{format_exc(e)}</code>")
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
    else:
        response_header = f"<b>✨ Gemma AI ({model})</b>\n\n"
        await status_msg.edit_text(response_header + final_text)

# --- Help Section ---
modules_help["gemma"] = {
    "gemma [-model] <prompt>": "Ask a question to a Gemma AI model. Defaults to 27b if no model flag is provided."
}