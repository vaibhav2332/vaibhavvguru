# ocr.py
import os
import json
import re
import requests
from urllib.parse import quote_plus
from pyrogram import Client, filters, enums
from pyrogram.types import Message

from utils.misc import modules_help, prefix

def upload_to_catbox(file_path: str) -> str or None:
    """
    Uploads a file to catbox.moe and returns the direct link.
    """
    try:
        with open(file_path, 'rb') as f:
            files = {'reqtype': (None, 'fileupload'), 'fileToUpload': f}
            response = requests.post("https://catbox.moe/user/api.php", files=files)
            response.raise_for_status()
        if response.status_code == 200:
            return response.text
        return None
    except Exception:
        return None

@Client.on_message(filters.command("ocr", prefix) & filters.me & filters.reply)
async def ocr_image(client: Client, message: Message):
    """
    Describes an image or answers a question about it using an OCR API.
    """
    replied_message = message.reply_to_message
    # Check if the replied message contains any media
    if not replied_message or not replied_message.media:
        await message.edit("<b>Error:</b> Please reply to an image or sticker.")
        return

    # Determine which media object to use (photo, sticker, or document)
    media = replied_message.photo or replied_message.sticker or replied_message.document
    if not media:
        await message.edit("<b>Error:</b> The replied message is not a supported image format.")
        return
        
    # Handle documents that might not be images
    if hasattr(media, 'mime_type') and not media.mime_type.startswith("image/"):
        await message.edit("<b>Error:</b> The replied document is not an image.")
        return

    await message.edit("<code>Processing...</code>")

    # --- File Download ---
    try:
        local_image_path = await client.download_media(media)
    except Exception as e:
        await message.edit(f"<b>Error downloading file:</b>\n<code>{e}</code>")
        return

    # --- Upload to get a public link ---
    await message.edit("<code>Uploading...</code>")
    image_url = upload_to_catbox(local_image_path)
    os.remove(local_image_path) # Clean up the local file immediately after upload

    if not image_url:
        await message.edit("<b>Error:</b> Failed to upload the image to get a public link.")
        return

    # --- API Call ---
    # Combine the arguments after the command to form the query text
    query_text = " ".join(message.command[1:]) if len(message.command) > 1 else "describe this picture"
    
    # URL-encode the parameters to ensure they are safe for the URL
    encoded_query = quote_plus(query_text)
    encoded_link = quote_plus(image_url)

    api_url = f"https://sii3.top/api/OCR.php?text={encoded_query}&link={encoded_link}"

    await message.edit("<code>Analyzing...</code>")
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        
        try:
            data = response.json()
            result_text = data.get("response")
            if not result_text:
                await message.edit("<b>Error:</b> 'response' key not found in API output.")
                return
        except json.JSONDecodeError:
            await message.edit("<b>Error:</b> Failed to parse API response as JSON.")
            return

    except requests.exceptions.RequestException as e:
        await message.edit(f"<b>API Error:</b>\n<code>{e}</code>")
        return
    except Exception as e:
        await message.edit(f"<b>An unexpected error occurred:</b>\n<code>{e}</code>")
        return

    # --- Show Result ---
    # Clean the response text from the API.
    # 1. Replace escaped newlines with actual newlines.
    processed_text = result_text.replace('\\n', '\n')
    
    # 2. Split the text into individual lines.
    lines = processed_text.split('\n')
    
    # 3. Remove any leading/trailing whitespace from each line and filter out empty lines.
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    
    # 4. Join the cleaned lines back together with a single newline.
    final_text = '\n'.join(cleaned_lines)

    # 5. Wrap the entire, cleaned text in a <pre> tag to make it a single, well-formatted code block.
    await message.edit(
        f"<pre>{final_text}</pre>",
        parse_mode=enums.ParseMode.HTML,
        disable_web_page_preview=True
    )


# --- Module Help ---
modules_help["ocr"] = {
    "ocr [prompt]": "Reply to an image/sticker to describe it. You can optionally add a question (e.g., .ocr what color is the car?).",
}