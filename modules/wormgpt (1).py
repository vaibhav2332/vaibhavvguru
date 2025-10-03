import aiohttp
import os
import re
import json
import codecs
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import MessageTooLong

from utils.misc import modules_help, prefix
from utils.scripts import format_exc

# --- Constants ---
API_URL = "https://sii3.top/DARK/api/wormgpt.php"
TELEGRAM_MAX_MSG_LENGTH = 4096

# --- Browser headers to look like a real user ---
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
}

# --- Reusable function to query the WormGPT API (Corrected) ---
async def query_wormgpt_api(prompt: str) -> str | None:
    """
    Queries the WormGPT API, parses the JSON, and returns the "response" text.
    Returns None on failure.
    """
    data = {"text": prompt}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, data=data, headers=BROWSER_HEADERS, timeout=300) as response:
                if response.status == 200:
                    try:
                        # ** THE FIX IS HERE: Parse JSON and get the "response" key **
                        json_data = await response.json(content_type=None)
                        return json_data.get("response")
                    except json.JSONDecodeError:
                        print("WormGPT API Error: Failed to decode JSON from response.")
                        return None
                else:
                    print(f"WormGPT API Error: Received status code {response.status}")
                    return None
    except Exception as e:
        print(f"An exception occurred while querying the WormGPT API: {format_exc(e)}")
        return None

# --- Advanced Formatting Engine ---
def advanced_format(text: str) -> str:
    """
    Processes raw API text to handle escape sequences and convert
    Markdown-like and LaTeX notations to Telegram HTML.
    """
    # 1. Decode escape sequences like \n, \t
    try:
        processed_text = codecs.decode(text, 'unicode_escape')
    except Exception:
        processed_text = text.replace('\\n', '\n').replace('\\t', '\t')

    # 2. Markdown to HTML Conversion
    processed_text = re.sub(r'```(\w+)?\n(.*?)```', r'<pre><code class="\1">\2</code></pre>', processed_text, flags=re.DOTALL)
    processed_text = re.sub(r'```(.*?)```', r'<pre><code>\1</code></pre>', processed_text, flags=re.DOTALL)
    processed_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', processed_text)
    processed_text = re.sub(r'__(.*?)__', r'<b>\1</b>', processed_text)
    processed_text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', processed_text)
    processed_text = re.sub(r'(?<!\w)_(.*?)_(?!\w)', r'<i>\1</i>', processed_text)
    processed_text = re.sub(r'`(.*?)`', r'<code>\1</code>', processed_text)

    # 3. LaTeX Formatting
    processed_text = re.sub(r'\$\$(.*?)\$\$', r'<code>$$\1$$</code>', processed_text, flags=re.DOTALL)
    processed_text = re.sub(r'\$(.*?)\$', r'<code>$\1$</code>', processed_text)

    return processed_text.strip()

# --- Main WormGPT Command ---
@Client.on_message(filters.command("worm", prefix) & filters.me)
async def wormgpt_command(client: Client, message: Message):
    """
    Interacts with the WormGPT AI, with advanced formatting.
    """
    if len(message.command) < 2:
        return await message.edit_text(
            "<b>🐍 WormGPT AI</b>\n\n"
            "<b>Usage:</b> <code>.worm &lt;your prompt&gt;</code>\n"
            "<b>Example:</b> <code>.worm explain the theory of relativity in simple terms</code>"
        )
    
    prompt = message.text.split(maxsplit=1)[1]
    status_msg = await message.edit_text("<b>🐍 Thinking with WormGPT...</b>")

    raw_response = await query_wormgpt_api(prompt)

    if not raw_response:
        return await status_msg.edit_text("<b>❗️ Error:</b> The WormGPT API did not return a valid response or the 'response' key was missing.")

    final_text = advanced_format(raw_response)
    response_header = "<b>🐍 WormGPT</b>\n\n"
    full_response = response_header + final_text

    try:
        await status_msg.edit_text(full_response, disable_web_page_preview=True)
    except MessageTooLong:
        await status_msg.edit_text("<b>Response is too long, sending as a file...</b>")
        file_path = f"wormgpt_response_{message.id}.txt"
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(final_text)

            await client.send_document(
                chat_id=message.chat.id,
                document=file_path,
                caption=f"<b>🐍 WormGPT Response</b>\n\n<b>Prompt:</b> <code>{prompt[:100]}...</code>",
                reply_to_message_id=message.id
            )
            await status_msg.delete()
        except Exception as e:
            await status_msg.edit_text(f"<b>Error sending file:</b>\n<code>{format_exc(e)}</code>")
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

# --- Help Section ---
modules_help["wormgpt"] = {
    "worm <prompt>": "Ask a question to the WormGPT AI. The response will be formatted."
}