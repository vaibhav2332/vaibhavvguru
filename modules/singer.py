import os
import re
import random
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

# --- List of available tags for the random feature ---
TAG_LIST = [
    "epic", "orchestra", "cinematic", "emotional", "piano", "sad", "dramatic", "hope", 
    "electronic", "ambient", "dark", "powerful", "pop", "hiphop", "future", "bass", 
    "trap", "lofi", "rock", "guitar", "melancholy", "uplifting", "chill", "deep", 
    "house", "edm", "techno", "synthwave", "retro", "classical", "violin", 
    "instrumental", "acoustic", "melodic", "harmonic", "dreamy", "romantic", "intense", 
    "soft", "hardstyle", "progressive", "vocal", "beats", "rap", "freestyle", "club", 
    "party", "funk", "groove", "metal", "jazz", "blues", "soul", "indie", 
    "alternative", "folk", "ballad", "anthemic", "minimal", "industrial", "world", 
    "afrobeat", "latin", "reggaeton", "dancehall", "oriental", "arabic", "ethnic", 
    "tribal", "drums", "percussion", "strings", "choir", "opera", "symphonic", "modern", 
    "experimental", "psytrance", "chillwave", "downtempo", "relaxing", "meditation", "zen", 
    "trance", "hardcore", "dnb", "breakbeat", "glitch", "future_garage", "electro", "urban", "dreamwave"
]

# --- API and Download Helper Functions ---
async def query_song_api(lyrics: str, tags: str) -> tuple[bool, str]:
    """
    Sends a request to the music API, parses JSON, and extracts the 'url'.
    Returns (True, music_url) on success, or (False, debug_api_url) on failure.
    """
    api_url = f"https://sii3.top/api/music.php?lyrics={quote_plus(lyrics)}&tags={quote_plus(tags)}"
    try:
        timeout = aiohttp.ClientTimeout(total=120) # 2-minute timeout for song generation
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(api_url, headers=BROWSER_HEADERS) as response:
                if response.status == 200:
                    response_json = await response.json()
                    # --- FIX: Changed "response" to "url" to match the API ---
                    if isinstance(response_json, dict) and response_json.get("url"):
                        return True, response_json["url"]
                return False, api_url
    except Exception:
        return False, api_url

async def download_audio(url: str, file_path: str):
    """Downloads the generated audio file."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=BROWSER_HEADERS) as response:
                response.raise_for_status()
                with open(file_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(1024 * 512):
                        f.write(chunk)
        return True
    except Exception:
        return False

# --- Main Song Command ---
@Client.on_message(filters.command("singer", prefix) & filters.me)
async def generate_song_command(client: Client, message: Message):
    """Generates a song with lyrics and music from a text prompt."""
    
    args = message.text.split(maxsplit=1)
    lyrics = ""
    tags_str = ""
    use_random_tags = False

    # --- 1. Parse Input ---
    if message.reply_to_message and message.reply_to_message.text:
        lyrics = message.reply_to_message.text
        if len(args) > 1:
            tags_str = args[1]
    elif len(args) > 1:
        # The logic for parsing flags and lyrics is here
        full_arg_str = args[1]
        if full_arg_str.strip().startswith("-r"):
            use_random_tags = True
            lyrics = full_arg_str.replace("-r", "", 1).strip()
        elif full_arg_str.strip().startswith("-t"):
            match = re.search(r"-t\s+([\w,]+)\s+(.*)", full_arg_str, re.DOTALL)
            if match:
                tags_str = match.group(1).strip()
                lyrics = match.group(2).strip()
            else:
                return await message.edit_text("<b>Invalid format.</b> Use <code>-t tag1,tag2 lyrics</code>")
        else: # No flags, the whole thing is lyrics
            lyrics = full_arg_str
    else:
        return await message.edit_text(
            "<b>Usage:</b> <code>.singer [flags] &lt;lyrics&gt;</code>\n\n"
            "<b>Example:</b> <code>.singer -t pop,rock Breaking all the chains</code>\n"
            "<b>Random:</b> <code>.singer -r a new day begins</code>\n"
            "Or reply to a message containing lyrics."
        )

    if not lyrics:
        return await message.edit_text("<b>Error:</b> No lyrics provided.")

    # --- 2. Determine Tags ---
    if use_random_tags:
        selected_tags = random.sample(TAG_LIST, k=random.randint(3, 4))
    elif tags_str:
        selected_tags = [tag.strip() for tag in tags_str.split(',')]
    else: # Default tags if none are provided
        selected_tags = ["pop", "electronic"]
    
    tags_for_api = "+".join(selected_tags)

    status_msg = await message.edit_text(f"<b>🎵 Generating song...</b>\n\n<b>Tags:</b> <code>{', '.join(selected_tags)}</code>")
    
    # --- 3. Get the music URL from the API ---
    success, result = await query_song_api(lyrics, tags_for_api)
    
    if not success:
        error_text = (
            "<b>❗️ The Song API failed to respond correctly.</b>\n\n"
            "Here is the direct debug link to test in your browser:\n"
            f"<code>{result}</code>"
        )
        return await status_msg.edit_text(error_text, disable_web_page_preview=True)

    # --- 4. Download and Upload ---
    music_url = result
    file_path = f"./downloads/song_{message.id}.mp3"
    
    # Ensure the downloads directory exists
    if not os.path.isdir("./downloads"):
        os.makedirs("./downloads")
    
    await status_msg.edit_text("<b>Downloading generated song...</b>")
    if not await download_audio(music_url, file_path):
        return await status_msg.edit_text("<b>Error:</b> Failed to download the generated audio file.")

    try:
        await status_msg.edit_text("<b>⬆️ Uploading to Telegram...</b>")
        
        # Improved caption logic
        lyrics_preview = lyrics if len(lyrics) <= 800 else f"{lyrics[:800]}..."

        final_caption = (
            f"<b>🎵 Song Generated</b>\n\n"
            f"<b>Lyrics:</b>\n<i>{lyrics_preview}</i>\n\n"
            f"<b>Tags:</b> <code>{', '.join(selected_tags)}</code>"
        )
        await client.send_audio(
            chat_id=message.chat.id,
            audio=file_path,
            caption=final_caption,
            reply_to_message_id=message.id
        )
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text(f"<b>Error during upload:</b>\n<code>{format_exc(e)}</code>")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

# --- Help Section ---
modules_help["song_generator"] = {
    "singer [flags] <lyrics>": "Generates a song with lyrics. Use -t for custom tags or -r for random tags.",
}

