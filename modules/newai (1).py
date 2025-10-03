import asyncio
import aiohttp
from urllib.parse import quote_plus
from pyrogram import Client, filters
from pyrogram.types import Message

from utils.misc import modules_help, prefix
from utils.scripts import format_exc

# --- Global variable to store the ID of the user to auto-reply to ---
AI_TARGET_USER = None

# --- Reusable function to query the AI API (Corrected Logic) ---
async def query_ai(text: str, prompt: str = "You are a helpful AI assistant.") -> str:
    """
    Sends a request to the AI API and returns the response, handling the correct JSON structure.
    """
    api_url = f"https://venom-api.x10.mx/api/gpt4.php?txt={quote_plus(text)}&prompt={quote_plus(prompt)}"
    
    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(api_url) as response:
                if response.status == 200:
                    if "application/json" in response.headers.get("Content-Type", ""):
                        response_json = await response.json()
                        
                        # ** THE FIX IS HERE: Check for a dictionary and the "response" key **
                        if isinstance(response_json, dict) and response_json.get("response"):
                            return response_json["response"]
                        else:
                            return "<b>Error:</b> The API returned a valid but empty or unexpected response."
                    else:
                        return "<b>Error:</b> The API did not return a valid JSON response. It might be down or overloaded."
                else:
                    return f"<b>Error:</b> The API service returned an HTTP status code <code>{response.status}</code>."
    except asyncio.TimeoutError:
        return "<b>Error:</b> The API took too long to respond. Please try again later."
    except Exception as e:
        return f"<b>Error:</b> A network exception occurred while contacting the API.\n<code>{format_exc(e)}</code>"

# --- Main AI Command ---
@Client.on_message(filters.command("mai", prefix) & filters.me)
async def ai_command(client: Client, message: Message):
    """Handles direct and reply-based AI queries."""
    try:
        import aiohttp
    except ImportError:
        return await message.edit_text(
            "<b>Error: `aiohttp` is not installed.</b>\n\n"
            "Please install it by running: <code>pip install aiohttp</code>"
        )

    question = ""
    if message.reply_to_message:
        replied_text = message.reply_to_message.text or message.reply_to_message.caption or ""
        prompt_text = message.text.split(maxsplit=1)[1] if len(message.command) > 1 else "Respond to this."
        question = f"Context: \"{replied_text}\"\n\nMy instruction: \"{prompt_text}\""
    elif len(message.command) > 1:
        question = message.text.split(maxsplit=1)[1]
    else:
        return await message.edit_text(
            "<b>Usage:</b>\n"
            "• <code>.mai &lt;your question&gt;</code>\n"
            "• Reply to a message with <code>.ai [prompt]</code> for context."
        )

    status_msg = await message.edit_text("<b>🤔 Thinking...</b>")
    response = await query_ai(question)
    await status_msg.edit_text(response, disable_web_page_preview=True)

# --- AI Auto-Reply Commands ---
@Client.on_message(filters.command("addai", prefix) & filters.me)
async def add_ai_target(client: Client, message: Message):
    """Sets a user to be auto-replied to by the AI."""
    global AI_TARGET_USER
    try:
        if message.reply_to_message:
            user = message.reply_to_message.from_user
        elif len(message.command) > 1:
            user = await client.get_users(message.command[1])
        else:
            return await message.edit_text("<b>Usage:</b> <code>.addai &lt;username/id&gt;</code> or reply to a user.")
        
        AI_TARGET_USER = user.id
        await message.edit_text(f"<b>✅ AI auto-reply has been enabled for {user.mention}.</b>")
    except Exception as e:
        await message.edit_text(f"<b>Error:</b> Could not find user.\n<code>{format_exc(e)}</code>")

@Client.on_message(filters.command("rmai", prefix) & filters.me)
async def remove_ai_target(client: Client, message: Message):
    """Disables the AI auto-reply feature."""
    global AI_TARGET_USER
    if AI_TARGET_USER is None:
        return await message.edit_text("<b>AI auto-reply is not currently active.</b>")
    AI_TARGET_USER = None
    await message.edit_text("<b>❌ AI auto-reply has been disabled.</b>")

# --- The Watcher ---
@Client.on_message(filters.incoming & ~filters.me & filters.text, group=1)
async def ai_watcher(client: Client, message: Message):
    """If a target user is set, this function triggers on their text messages."""
    global AI_TARGET_USER
    
    if AI_TARGET_USER is None or not message.from_user or message.from_user.id != AI_TARGET_USER or not message.text:
        return
        
    try:
        response = await query_ai(message.text)
        await message.reply_text(response, disable_web_page_preview=True)
    except Exception:
        pass

# --- Help Section ---
modules_help["ai_assistant"] = {
    "mai <prompt>": "Ask a question to the AI. Reply to a message to provide context.",
    "addai <user>": "Enable AI auto-reply for a specific user (by username, ID, or reply).",
    "rmai": "Disable the AI auto-reply feature.",
}