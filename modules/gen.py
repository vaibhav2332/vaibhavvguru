import aiohttp
import os
import urllib.parse
from pyrogram import Client, filters
from pyrogram.types import Message
from utils.misc import modules_help, prefix

# Define the API URLs from the user
API_V1 = "https://botfather.cloud/Apis/ImgGen/?prompt={}"
API_V2 = "https://botfather.cloud/Apis/ImgGen/client.php?inputText={}"


async def download_file(url, path):
    """Asynchronously downloads a file from a URL to a specified path."""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return False  # Indicate failure
                with open(path, "wb") as f:
                    while chunk := await resp.content.read(1024):
                        f.write(chunk)
                return True  # Indicate success
        except aiohttp.ClientError:
            return False


async def get_prompt_and_status(message: Message, cmd: str):
    """
    Extracts the prompt from a message and sends an initial status message.
    """
    is_self = message.from_user and message.from_user.is_self
    prompt = ""
    if message.reply_to_message and message.reply_to_message.text:
        prompt = message.reply_to_message.text.strip()
    elif len(message.command) > 1:
        prompt = message.text.split(maxsplit=1)[1].strip()

    if not prompt:
        usage_text = f"<b>Usage:</b> <code>{prefix}{cmd} [prompt]</code> or reply to a text message."
        if is_self:
            await message.edit(usage_text)
        else:
            await message.reply(usage_text)
        return None, None

    status_message = await (message.edit_text("<code>🎨 Processing your request...</code>") if is_self else message.reply("<code>🎨 Processing your request...</code>"))
    return prompt, status_message


async def process_image_generation(client: Client, message: Message, prompt: str, status: Message, api_version: int):
    """
    Handles the core logic of fetching the image from the API and sending it.
    """
    # URL encode the prompt to handle spaces and special characters
    encoded_prompt = urllib.parse.quote_plus(prompt)

    api_url = API_V1.format(encoded_prompt) if api_version == 1 else API_V2.format(encoded_prompt)
    file_path = "generated_image.jpg"

    try:
        await status.edit_text(f"<code>⏳ Generating image with API V{api_version}...</code>")

        # Download the image from the API
        download_success = await download_file(api_url, file_path)

        if not download_success or not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            await status.edit_text("<code>❌ Failed to generate image. The API might be down or returned an empty response.</code>")
            return

        await status.edit_text("<code>⬆️ Uploading generated image...</code>")

        # Send the downloaded photo
        await client.send_photo(
            chat_id=message.chat.id,
            photo=file_path,
            caption=f"<b>✨ Prompt:</b> <code>{prompt}</code>\n<b>🤖 API Version:</b> V{api_version}",
            reply_to_message_id=message.id
        )
    except Exception as e:
        await status.edit_text(f"<code>An error occurred: {str(e)}</code>")
    finally:
        # Clean up by deleting the downloaded file
        if os.path.exists(file_path):
            os.remove(file_path)
        # Delete the status message
        await status.delete()


@Client.on_message(filters.command(["genv1"], prefix))
async def generate_v1_handler(client: Client, message: Message):
    """Handler for the /genv1 command."""
    prompt, status = await get_prompt_and_status(message, "genv1")
    if prompt and status:
        await process_image_generation(client, message, prompt, status, 1)


@Client.on_message(filters.command(["genv2"], prefix))
async def generate_v2_handler(client: Client, message: Message):
    """Handler for the /genv2 command."""
    prompt, status = await get_prompt_and_status(message, "genv2")
    if prompt and status:
        await process_image_generation(client, message, prompt, status, 2)


# Add help documentation for the module
modules_help["imggen"] = {
    "genv1 [prompt]": "Generate an image using API V1.",
    "genv2 [prompt]": "Generate an image using API V2.",
}
