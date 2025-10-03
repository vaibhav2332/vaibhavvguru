import os
import asyncio
import aiohttp
from urllib.parse import quote_plus
from pyrogram import Client, filters
from pyrogram.types import Message

from utils.misc import modules_help, prefix
from utils.scripts import format_exc

# --- Browser headers to prevent being blocked by the API ---
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
}

# --- Reusable function to query the Music API ---
async def query_music_api(prompt: str) -> tuple[bool, str]:
    """
    Sends a request to the music API, parses the JSON, and extracts the 'response' URL.
    Returns (True, music_url) on success.
    Returns (False, debug_api_url) on any failure.
    """
    # The API documentation shows create-music.php, which is likely the intended endpoint.
    api_url = f"https://sii3.top/api/create-music.php?text={quote_plus(prompt)}"
    
    try:
        # Music generation can be slow, so we use a longer timeout.
        timeout = aiohttp.ClientTimeout(total=90)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(api_url, headers=BROWSER_HEADERS) as response:
                if response.status == 200:
                    response_json = await response.json()
                    if isinstance(response_json, dict) and response_json.get("response"):
                        # Success: return the MP3 link
                        return True, response_json["response"]
                # Any other status code or a malformed response is a failure
                return False, api_url
    except Exception:
        # Any exception (timeout, network error, etc.) is a failure
        return False, api_url

# --- Helper to download the final MP3 file ---
async def download_audio(url: str, file_path: str, status_msg: Message):
    """Downloads the generated audio file with progress updates."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=BROWSER_HEADERS) as response:
                response.raise_for_status()
                total_size = int(response.headers.get('content-length', 0))
                downloaded_size = 0
                with open(file_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(1024 * 1024):
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0:
                            percent = (downloaded_size / total_size) * 100
                            await status_msg.edit_text(f"<b>Downloading music... {percent:.1f}%</b>")
        return True
    except Exception:
        return False

# --- Main Music Command ---
@Client.on_message(filters.command("musician", prefix) & filters.me)
async def generate_music_command(client: Client, message: Message):
    """Generates a short music clip from a text prompt."""
    
    if len(message.command) < 2:
        return await message.edit_text("<b>Usage:</b> <code>.music &lt;your prompt&gt;</code>\n\n<b>Example:</b> <code>.music epic cinematic battle score</code>")

    prompt = message.text.split(maxsplit=1)[1]
    status_msg = await message.edit_text("<b>🎵 Generating music from your prompt...</b>")
    
    # 1. Get the music URL from the API
    success, result = await query_music_api(prompt)
    
    if not success:
        error_text = (
            "<b>❗️ The Music API failed to respond correctly.</b>\n\n"
            "Here is the direct debug link to test in your browser:\n"
            f"<code>{result}</code>"
        )
        return await status_msg.edit_text(error_text, disable_web_page_preview=True)

    # 2. Download the generated MP3 file
    music_url = result
    file_path = f"./downloads/music_{message.id}.mp3"
    
    if not await download_audio(music_url, file_path, status_msg):
        return await status_msg.edit_text("<b>Error:</b> Failed to download the generated audio file.")

    # 3. Upload the audio file to Telegram
    try:
        await status_msg.edit_text("<b>⬆️ Uploading generated music...</b>")
        await client.send_audio(
            chat_id=message.chat.id,
            audio=file_path,
            caption=f"<b>🎵 Music generated from prompt:</b>\n<code>{prompt}</code>",
            reply_to_message_id=message.id
        )
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text(f"<b>Error during upload:</b>\n<code>{format_exc(e)}</code>")
    finally:
        # 4. Clean up the downloaded file
        if os.path.exists(file_path):
            os.remove(file_path)

# --- Help Section ---
modules_help["music_generator"] = {
    "musician <prompt>": "Generates a 15-second instrumental music clip based on your prompt.",
}