import aiohttp
import os
from urllib.parse import quote_plus
from pyrogram import Client, filters
from pyrogram.types import Message
# Assuming 'utils.misc' exists in your project structure
# from utils.misc import modules_help, prefix

# --- Mock objects for standalone testing if utils are not available ---
# If you have these utils, you can remove this section
try:
    from utils.misc import modules_help, prefix
except ImportError:
    print("Warning: 'utils.misc' not found. Using mock objects for 'modules_help' and 'prefix'.")
    modules_help = {}
    prefix = "."
# --- End of Mock objects section ---


# --- API Configuration ---
API_URL = "https://name-to-app.rishuapi.workers.dev/?name={name}"


# --- Helper Functions ---
async def fetch_json(url):
    """Fetches JSON data from a URL."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
    except aiohttp.ClientError:
        return None
    return None


async def download_file(url, path):
    """Downloads a file from a URL to a given path."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return False
                with open(path, "wb") as f:
                    while True:
                        chunk = await resp.content.read(4096)
                        if not chunk:
                            break
                        f.write(chunk)
                return True
    except Exception:
        return False


def safe_filename(name):
    """Creates a safe, simple filename from a string."""
    return "".join(c for c in name if c.isalnum() or c in (' ', '.', '_')).rstrip()


# --- Merged Command Handler ---
@Client.on_message(filters.command(["apk"], prefix))
async def apk_handler(client: Client, message: Message):
    """
    Handles the .apk command.
    First, it shows app details, then downloads and uploads the APK for the top result.
    """
    is_self = message.from_user and message.from_user.is_self

    if len(message.command) < 2:
        usage_text = f"<b>Usage:</b> <code>{prefix}apk [app name]</code>"
        await (message.edit(usage_text) if is_self else message.reply(usage_text))
        return

    app_name = message.text.split(maxsplit=1)[1]
    status_message = await (message.edit_text(f"<code>Searching for '{app_name}'...</code>") if is_self else message.reply(f"<code>Searching for '{app_name}'...</code>"))

    encoded_name = quote_plus(app_name)
    request_url = API_URL.format(name=encoded_name)

    response_data = await fetch_json(request_url)

    if not response_data or not isinstance(response_data, list) or not response_data:
        error_text = f"<code>❌ No apps found for '{app_name}'.</code>" if isinstance(response_data, list) else "<code>❌ Failed to fetch details. The API might be down.</code>"
        await status_message.edit_text(error_text)
        return

    # --- Part 1: Display App Details ---
    await status_message.edit_text(f"<code>Found {len(response_data)} result(s). Sending details...</code>")
    try:
        details_text = ""
        # Limit details to the top 5 results for readability
        for app in response_data[:5]:
            filesize_mb = f"{app.get('filesize', 0) / (1024 * 1024):.2f} MB"
            details_text += (
                f"<b>Name:</b> <code>{app.get('name', 'N/A')}</code>\n"
                f"<b>Package:</b> <code>{app.get('package', 'N/A')}</code>\n"
                f"<b>Developer:</b> <code>{app.get('developer', 'N/A')}</code>\n"
                f"<b>Size:</b> <code>{filesize_mb}</code>\n"
                f"-----------------------------------\n"
            )

        first_app_image = response_data[0].get("image")
        if first_app_image:
            await client.send_photo(chat_id=message.chat.id, photo=first_app_image, caption=details_text)
        else:
            await client.send_message(message.chat.id, details_text) # Fallback if no image

    except (KeyError, IndexError, TypeError) as e:
        await client.send_message(message.chat.id, f"<code>⚠️ Could not parse app details: {e}</code>")

    # --- Part 2: Download and Upload Top Result ---
    top_app = response_data[0]
    download_url = top_app.get("path")
    app_title = top_app.get("name", "Untitled App")

    if not download_url:
        await status_message.edit_text(f"<code>No download path found for '{app_title}'. Cannot proceed.</code>")
        return

    await status_message.edit_text(f"<code>Now downloading '{app_title}'...</code>")

    filename = f"{safe_filename(app_title)}.apk"
    thumb_path = "temp_thumb.jpg" if top_app.get("image") else None

    try:
        if thumb_path:
            await download_file(top_app["image"], thumb_path)

        download_success = await download_file(download_url, filename)

        if download_success:
            await status_message.edit_text(f"<code>Uploading '{app_title}'...</code>")

            filesize_mb = f"{top_app.get('filesize', 0) / (1024 * 1024):.2f} MB"
            file_caption = (
                f"<b>Name:</b> <code>{top_app.get('name', 'N/A')}</code>\n"
                f"<b>Package:</b> <code>{top_app.get('package', 'N/A')}</code>\n"
                f"<b>Size:</b> <code>{filesize_mb}</code>"
            )

            await client.send_document(
                chat_id=message.chat.id,
                document=filename,
                caption=file_caption,
                thumb=thumb_path if thumb_path and os.path.exists(thumb_path) else None
            )
            await status_message.delete()
        else:
            await status_message.edit_text(f"<code>Failed to download APK for '{app_title}'.</code>")

    except Exception as e:
        await status_message.edit_text(f"<code>An error occurred while processing '{app_title}': {e}</code>")
    finally:
        # Clean up downloaded files to save space
        if os.path.exists(filename):
            os.remove(filename)
        if thumb_path and os.path.exists(thumb_path):
            os.remove(thumb_path)


# --- Help Documentation ---
modules_help["apk"] = {
    "apk [app name]": "Search for an app, show its details, and upload the APK file of the top result.",
}