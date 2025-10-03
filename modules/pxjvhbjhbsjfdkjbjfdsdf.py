import aiohttp
import os
from urllib.parse import quote_plus
from pyrogram import Client, filters
from pyrogram.types import Message
from utils.misc import modules_help, prefix

# --- API Configuration ---
API_URL = "https://api.redtube.com/?data=redtube.Videos.searchVideos&output=json&search={search_query}&thumbsize=medium"

# --- Helper Functions ---
async def fetch_json(url):
    """Fetches JSON data from a URL and returns data or an error message."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json(), None  # Return data, no error
                else:
                    return None, f"API returned status {response.status}"  # Return error
    except aiohttp.ClientError as e:
        return None, f"Connection error: {e}" # Return error

async def download_file(url, path):
    """Downloads a file from a URL to a given path."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return False
                with open(path, "wb") as f:
                    f.write(await resp.read())
                return True
    except Exception:
        return False


# --- Command Handler ---
@Client.on_message(filters.command(["rsearch"], prefix))
async def redtube_search(client: Client, message: Message):
    """Handles the .rsearch command to search for videos."""
    is_self = message.from_user and message.from_user.is_self
    
    if len(message.command) < 2:
        usage_text = f"<b>Usage:</b> <code>{prefix}rsearch [query]</code>"
        await (message.edit(usage_text) if is_self else message.reply(usage_text))
        return

    search_query = message.text.split(None, 1)[1]
    
    status_message = await (message.edit_text(f"<code>Searching for '{search_query}'...</code>") if is_self else message.reply(f"<code>Searching for '{search_query}'...</code>"))
    
    encoded_query = quote_plus(search_query)
    request_url = API_URL.format(search_query=encoded_query)
    
    response_data, error = await fetch_json(request_url)

    if error:
        await status_message.edit_text(f"<code>❌ API Error: {error}. The service may be offline or blocked.</code>")
        return

    if not response_data or "videos" not in response_data or not response_data["videos"]:
        await status_message.edit_text(f"<code>❌ No results found for '{search_query}'.</code>")
        return
        
    videos = response_data["videos"]
    
    # To avoid spam, let's send the top 5 results
    results_to_send = videos[:5]
    
    await status_message.delete() # Delete the "searching" message before sending results

    for item in results_to_send:
        video_info = item.get("video")
        if not video_info:
            continue

        title = video_info.get("title", "No Title")
        duration = video_info.get("duration", "N/A")
        views = video_info.get("views", "N/A")
        rating = video_info.get("rating", "N/A")
        video_url = video_info.get("url", "#")
        thumb_url = video_info.get("thumb")
        
        caption = (
            f"<b>{title}</b>\n\n"
            f"<b>Duration:</b> {duration}\n"
            f"<b>Views:</b> {views}\n"
            f"<b>Rating:</b> {rating}\n"
            f"<b>URL:</b> {video_url}"
        )
        
        thumb_path = f"temp_thumb_{video_info.get('video_id')}.jpg"
        
        try:
            if thumb_url and await download_file(thumb_url, thumb_path):
                await client.send_photo(
                    chat_id=message.chat.id,
                    photo=thumb_path,
                    caption=caption
                )
            else:
                # If thumbnail fails to download, send text only
                await message.reply_text(caption, disable_web_page_preview=True)
        finally:
            if os.path.exists(thumb_path):
                os.remove(thumb_path)


# --- Help Documentation ---
modules_help["redtube_search"] = {
    "rsearch [query]": "Searches RedTube for the given query and returns the top 5 results.",
}

