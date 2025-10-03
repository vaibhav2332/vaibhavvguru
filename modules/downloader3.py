import aiohttp
import os
import re
import asyncio

from pyrogram import Client, filters
from pyrogram.types import Message
from utils.misc import modules_help

# --- API Configuration ---
API_URL = "https://socialdown.itz-ashlynn.workers.dev"
URL_REGEX = r'(https?://\S+)'
SUPPORTED_DOMAINS = [
    "facebook.com", "fb.watch", "instagram.com", "spotify.com",
    "mediafire.com", "soundcloud.com", "threads.net", "x.com",
    "twitter.com", "tiktok.com", "capcut.com", "youtube.com", "youtu.be"
]

# --- Helper Functions ---
async def post_json(url, data):
    """Posts JSON data to a URL and returns the JSON response."""
    try:
        async with aiohttp.ClientSession() as session:
            headers = {'User-Agent': 'Mozilla/5.0'}
            async with session.post(url, json=data, headers=headers, timeout=40) as response:
                if response.status == 200:
                    return await response.json()
                print(f"API Error: Status {response.status} for URL {url}")
                return None
    except aiohttp.ClientError as e:
        print(f"HTTP Client Error: {e}")
        return None

async def download_file(url, file_path, status_msg, referer_url):
    """
    Directly downloads a file with progress updates.
    Includes a Referer header for protected links.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Referer': referer_url
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    return False, f"HTTP {response.status}"
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded_size = 0
                last_update = asyncio.get_event_loop().time()

                with open(file_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(1024 * 1024):
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        current_time = asyncio.get_event_loop().time()
                        if total_size > 0 and (current_time - last_update) > 2:
                            progress = (downloaded_size / total_size) * 100
                            await status_msg.edit_text(f"<code>Downloading... {progress:.1f}%</code>")
                            last_update = current_time
                return True, None
    except Exception as e:
        return False, str(e)

def safe_filename(title, quality, ext):
    """Creates a safe filename."""
    s_title = "".join(c for c in title if c.isalnum() or c in ' ._-').rstrip()[:50]
    s_quality = "".join(c for c in quality if c.isalnum())
    return f"{s_title}_{s_quality}.{ext}"

# --- Main Handler ---
@Client.on_message(filters.text & filters.regex(URL_REGEX) & ~filters.bot)
async def ashlynn_auto_downloader(client: Client, message: Message):
    if message.edit_date or message.forward_date:
        return

    status_msg = None
    try:
        url_match = re.search(URL_REGEX, message.text)
        if not url_match: return
            
        media_url = url_match.group(0)

        if not any(domain in media_url for domain in SUPPORTED_DOMAINS):
            return

        status_msg = await message.reply_text("<code>Processing link...</code>", quote=True)

        platform = "unknown"
        if "facebook.com" in media_url or "fb.watch" in media_url: platform = "fb"
        elif "instagram.com" in media_url: platform = "insta"
        elif "spotify.com" in media_url: platform = "spotify"
        elif "mediafire.com" in media_url: platform = "mediafire"
        elif "soundcloud.com" in media_url: platform = "soundcloud"
        elif "threads.net" in media_url: platform = "threads"
        elif "x.com" in media_url or "twitter.com" in media_url: platform = "x"
        elif "tiktok.com" in media_url: platform = "tiktok"
        elif "capcut.com" in media_url: platform = "capcut"
        elif "youtube.com" in media_url or "youtu.be" in media_url: platform = "yt"

        if platform == "unknown":
            await status_msg.delete()
            return

        endpoint_url = f"{API_URL}/{platform}"
        downloads_to_process = []
        title = "Downloaded Media"

        if platform == 'yt':
            mp4_payload = {"url": media_url, "format": "mp4"}
            mp3_payload = {"url": media_url, "format": "mp3"}
            
            mp4_response, mp3_response = await asyncio.gather(
                post_json(endpoint_url, mp4_payload),
                post_json(endpoint_url, mp3_payload)
            )
            
            if mp4_response and mp4_response.get("success"):
                data = mp4_response.get('data', [{}])[0]
                title, url, fmt = data.get('title'), data.get('downloadUrl'), data.get('format', 'mp4')
                downloads_to_process.append({"url": url, "quality": "Video", "ext": fmt, "type": "video"})
            
            if mp3_response and mp3_response.get("success"):
                data = mp3_response.get('data', [{}])[0]
                title = data.get('title') or title
                url, fmt = data.get('downloadUrl'), data.get('format', 'mp3')
                downloads_to_process.append({"url": url, "quality": "Audio", "ext": fmt, "type": "audio"})
                
        else:
            response_data = await post_json(endpoint_url, {"url": media_url})
            if not response_data or not response_data.get("success"):
                error = response_data.get("error", "API request failed.") if response_data else "No response."
                await status_msg.edit_text(f"<code>❌ Error: {error}</code>")
                return

            if platform == "fb":
                title = response_data.get("platform", "Facebook Video")
                if response_data.get("hd"): downloads_to_process.append({"url": response_data["hd"], "quality": "HD", "ext": "mp4", "type": "video"})
                if response_data.get("sd"): downloads_to_process.append({"url": response_data["sd"], "quality": "SD", "ext": "mp4", "type": "video"})
                if response_data.get("audio"): downloads_to_process.append({"url": response_data["audio"], "quality": "Audio", "ext": "mp3", "type": "audio"})
            
            # CORRECTED: Robustly handle both string lists (Instagram) and dict lists (X)
            elif platform in ["insta", "threads", "x"]:
                title = response_data.get("metadata", {}).get("creator", "Social Media Post")
                media_list = response_data.get("urls") or (response_data.get("media") if platform == "x" else [])
                for i, media_item in enumerate(media_list, 1):
                    url, ext, file_type = (None, None, None)
                    if isinstance(media_item, str):
                        url, ext, file_type = media_item, "mp4", "video"
                    elif isinstance(media_item, dict):
                        url = media_item.get("url")
                        file_type = "audio" if "audio" in media_item.get("type", "") else "video"
                        ext = "mp3" if file_type == "audio" else "mp4"
                    
                    if url:
                        downloads_to_process.append({"url": url, "quality": f"File_{i}", "ext": ext, "type": file_type})

            elif platform == "spotify":
                title, url = response_data.get("name", "Track"), response_data.get("download_url")
                downloads_to_process.append({"url": url, "quality": "Audio", "ext": "mp3", "type": "audio"})
            elif platform == "mediafire":
                title, url = response_data.get("name", "File"), response_data.get("download")
                ext = title.split('.')[-1] if '.' in title else 'zip'
                downloads_to_process.append({"url": url, "quality": "File", "ext": ext, "type": "document"})
            elif platform == 'tiktok':
                data = response_data.get('data', [{}])[0]
                title = data.get('title', "TikTok")
                for link_info in data.get('downloadLinks', []):
                    downloads_to_process.append({"url": link_info['link'], "quality": link_info['text'], "ext": "mp4", "type": "video"})
            elif platform == 'capcut':
                title, url = response_data.get('title'), response_data.get('videoUrl')
                downloads_to_process.append({"url": url, "quality": "Video", "ext": "mp4", "type": "video"})
            elif platform == 'soundcloud':
                title, url = response_data.get('title'), response_data.get('download_url')
                downloads_to_process.append({"url": url, "quality": "Audio", "ext": "mp3", "type": "audio"})

        if not downloads_to_process:
            await status_msg.edit_text("<code>❌ No downloadable media found.</code>")
            return

        await status_msg.delete()
        status_msg = None # Prevent editing deleted message in finally block

        for item in downloads_to_process:
            url, quality, ext, file_type = item.get("url"), item.get("quality"), item.get("ext"), item.get("type", "video")
            if not url: continue
            
            file_path = safe_filename(title, quality, ext)
            dl_status = await message.reply_text(f"<code>Downloading '{title}' ({quality})...</code>", quote=True)
            
            try:
                success, error = await download_file(url, file_path, dl_status, referer_url=media_url)
                if not success:
                    await dl_status.edit_text(f"<code>❌ Download failed for {quality}. Reason: {error}</code>")
                    continue

                await dl_status.edit_text(f"<code>Uploading '{quality}'...</code>")
                caption = f"<b>{title}</b>\n<b>Quality:</b> <code>{quality}</code>"
                
                if file_type == "audio":
                    await client.send_audio(message.chat.id, audio=file_path, caption=caption)
                elif file_type == "document":
                    await client.send_document(message.chat.id, document=file_path, caption=caption)
                else:
                    await client.send_video(message.chat.id, video=file_path, caption=caption)
                
                await dl_status.delete()
            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)
    
    except Exception as e:
        if status_msg:
            await status_msg.edit_text(f"<b>An unexpected error occurred:</b>\n<code>{e}</code>")
        print(f"Error in downloader: {e}")

# --- Help Documentation ---
modules_help["ashlynn_downloader"] = {
    "AutoDownloader": "This module is command-less. It auto-detects and downloads content from any supported social media link.",
}

