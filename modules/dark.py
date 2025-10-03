import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message
from utils.misc import modules_help, prefix

# --- API URLs ---
DARK_JOKE_API_URL = "https://abhi-api.vercel.app/api/fun/jdark"
FACTS_API_URL = "https://abhi-api.vercel.app/api/fun/facts"
DEV_JOKE_API_URL = "https://abhi-api.vercel.app/api/fun/jdev"
QUESTION_API_URL = "https://abhi-api.vercel.app/api/fun/question"
ROAST_API_URL = "https://abhi-api.vercel.app/api/fun/roast"


# --- Helper Function ---
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


# --- Command Handlers ---
@Client.on_message(filters.command(["djoke"], prefix))
async def dark_joke_handler(client: Client, message: Message):
    """Handles the .djoke command to fetch a random dark joke."""
    is_self = message.from_user and message.from_user.is_self
    status_message = await (message.edit_text("<code>⚫️ Fetching a dark joke...</code>") if is_self else message.reply("<code>⚫️ Fetching a dark joke...</code>"))

    joke_data = await fetch_json(DARK_JOKE_API_URL)

    if joke_data and joke_data.get("status") and "result" in joke_data:
        try:
            setup = joke_data["result"]["setup"]
            punchline = joke_data["result"]["punchline"]
            
            full_joke = f"<b>Setup:</b>\n{setup}\n\n<b>Punchline:</b>\n{punchline}"
            
            await status_message.edit_text(full_joke)
        except (KeyError, TypeError):
            await status_message.edit_text("<code>❌ Could not parse the joke format from the API response.</code>")
    else:
        await status_message.edit_text("<code>❌ Sorry, I couldn't fetch a dark joke. The API might be down.</code>")


@Client.on_message(filters.command(["devjoke"], prefix))
async def dev_joke_handler(client: Client, message: Message):
    """Handles the .devjoke command to fetch a random developer joke."""
    is_self = message.from_user and message.from_user.is_self
    status_message = await (message.edit_text("<code>💻 Fetching a developer joke...</code>") if is_self else message.reply("<code>💻 Fetching a developer joke...</code>"))

    joke_data = await fetch_json(DEV_JOKE_API_URL)

    if joke_data and joke_data.get("status") and "result" in joke_data:
        try:
            setup = joke_data["result"]["setup"]
            punchline = joke_data["result"]["punchline"]
            
            full_joke = f"<b>Setup:</b>\n{setup}\n\n<b>Punchline:</b>\n{punchline}"
            
            await status_message.edit_text(full_joke)
        except (KeyError, TypeError):
            await status_message.edit_text("<code>❌ Could not parse the joke format from the API response.</code>")
    else:
        await status_message.edit_text("<code>❌ Sorry, I couldn't fetch a developer joke. The API might be down.</code>")


@Client.on_message(filters.command(["facts"], prefix))
async def facts_handler(client: Client, message: Message):
    """Handles the .facts command to fetch a random fact."""
    is_self = message.from_user and message.from_user.is_self
    status_message = await (message.edit_text("<code>🧠 Fetching a fact...</code>") if is_self else message.reply("<code>🧠 Fetching a fact...</code>"))

    fact_data = await fetch_json(FACTS_API_URL)

    if fact_data and fact_data.get("status") and "result" in fact_data:
        try:
            fact = fact_data["result"]
            await status_message.edit_text(f"<b>Fact:</b>\n{fact}")
        except (KeyError, TypeError):
            await status_message.edit_text("<code>❌ Could not parse the fact from the API response.</code>")
    else:
        await status_message.edit_text("<code>❌ Sorry, I couldn't fetch a fact. The API might be down.</code>")


@Client.on_message(filters.command(["question"], prefix))
async def question_handler(client: Client, message: Message):
    """Handles the .question command to fetch a random question."""
    is_self = message.from_user and message.from_user.is_self
    status_message = await (message.edit_text("<code>🤔 Fetching a random question...</code>") if is_self else message.reply("<code>🤔 Fetching a random question...</code>"))

    question_data = await fetch_json(QUESTION_API_URL)

    if question_data and question_data.get("status") and "result" in question_data:
        try:
            question = question_data["result"]["question"]
            await status_message.edit_text(f"<b>{question}</b>")
        except (KeyError, TypeError):
            await status_message.edit_text("<code>❌ Could not parse the question from the API response.</code>")
    else:
        await status_message.edit_text("<code>❌ Sorry, I couldn't fetch a question. The API might be down.</code>")


@Client.on_message(filters.command(["roast"], prefix))
async def roast_handler(client: Client, message: Message):
    """Handles the .roast command to fetch a random roast."""
    is_self = message.from_user and message.from_user.is_self
    status_message = await (message.edit_text("<code>🔥 Fetching a roast...</code>") if is_self else message.reply("<code>🔥 Fetching a roast...</code>"))

    roast_data = await fetch_json(ROAST_API_URL)

    if roast_data and roast_data.get("status") and "result" in roast_data:
        try:
            roast = roast_data["result"]
            await status_message.edit_text(f"<b>{roast}</b>")
        except (KeyError, TypeError):
            await status_message.edit_text("<code>❌ Could not parse the roast from the API response.</code>")
    else:
        await status_message.edit_text("<code>❌ Sorry, I couldn't fetch a roast. The API might be down.</code>")


# --- Help Documentation ---
modules_help["dark_joke"] = {
    "djoke": "Get a random dark joke.",
    "devjoke": "Get a random developer joke.",
    "facts": "Get a random interesting fact.",
    "question": "Get a random question.",
    "roast": "Get a random roast.",
}

