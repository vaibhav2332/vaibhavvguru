import aiohttp
import json
from urllib.parse import quote_plus
from pyrogram import Client, filters
from pyrogram.types import Message

from utils.misc import modules_help, prefix
from utils.scripts import format_exc

# --- Browser headers to look like a real user ---
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
}

# --- Reusable function to query the Prompt Expansion API (MODIFIED) ---
async def expand_prompt_api(text: str) -> str | None:
    """
    Queries the prompt expansion API, parses the JSON response,
    and returns the expanded prompt text from the 'response' key.
    Returns None on failure.
    """
    api_url = f"https://sii3.top/api/prompt-img.php?text={quote_plus(text)}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, headers=BROWSER_HEADERS) as response:
                if response.status == 200:
                    try:
                        # Parse the JSON response
                        data = await response.json()
                        # Extract the value from the "response" key
                        return data.get("response")
                    except (json.JSONDecodeError, aiohttp.ContentTypeError):
                        print("Prompt API Error: Failed to decode JSON response.")
                        return None
                else:
                    # Log error if status is not 200
                    print(f"Prompt API Error: Received status code {response.status}")
                    return None
    except Exception as e:
        print(f"An exception occurred while querying the Prompt API: {format_exc(e)}")
        return None

# --- Main Prompt Expander Command (MODIFIED for better output) ---
@Client.on_message(filters.command("pe", prefix) & filters.me)
async def promptex_command(client: Client, message: Message):
    """
    Expands a short prompt into a detailed one using an API.
    """
    # Check for prompt text
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return await message.edit_text(
            "🎨 Prompt Expander\n\n"
            "Usage: .pe <your short prompt>\n"
            "Example: .pe a cat"
        )
    
    original_prompt = args[1]
    status_msg = await message.edit_text(f"🎨 Expanding prompt for: {original_prompt}")
    
    # Call the API
    expanded_prompt = await expand_prompt_api(original_prompt)
    
    # Process the result
    if expanded_prompt:
        # Format the response with the extracted prompt
        response_text = (
            f"🎨 Original Prompt:\n{original_prompt}\n\n"
            f"✨ Expanded Prompt:\n{expanded_prompt}"
        )
        await status_msg.edit_text(response_text)
    else:
        # Handle API failure
        await status_msg.edit_text(
            f"❗️ Error\n\n"
            f"The prompt expansion API failed to respond correctly for {original_prompt}."
        )

# --- Help Section ---
modules_help["promptex"] = {
    "pe ": "Expands your short text into a detailed AI image generation prompt."
}