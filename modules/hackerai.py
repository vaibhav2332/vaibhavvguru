import aiohttp
import sqlite3
from datetime import datetime
import asyncio

from pyrogram import Client, filters
from pyrogram.types import Message

from utils.misc import modules_help, prefix

# --- Configuration ---
AI_API_URL = "https://dev-pycodz-blackbox.pantheonsite.io/DEvZ44d/Hacker.php"
DB_FILE = "chat_history.db"

# --- In-memory State ---
# These will reset if the bot restarts.
user_languages = {}
group_user_activation = {}

# --- Database Setup ---
def initialize_database():
    """Initializes the SQLite database and table."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_chats (
            user_id INTEGER,
            chat_id INTEGER,
            message TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    return conn, cursor

conn, cursor = initialize_database()

# --- Async Database Wrappers ---
async def db_write(query, params):
    """Executes a write query in a non-blocking way."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: (cursor.execute(query, params), conn.commit()))

async def db_read_all(query, params):
    """Executes a read query in a non-blocking way."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: cursor.execute(query, params).fetchall())

# --- Helper Text ---
ABOUT_HACKERGPT = {
    "en": (
        "• > *HackerGPT* is an advanced AI designed for cybersecurity ***professionals***, "
        "*ethical hackers*, *MalWare*, and *penetration testers*. It assists in *vulnerability analysis*, "
        "*security script generation*, and *cybersecurity research*, *Backdoor implementation*. "
        "Unlike traditional AI models, HackerGPT provides unrestricted access, empowering you to explore "
        "the cyber world with greater flexibility and efficiency. 🚀"
    ),
    "ar": (
        "• > *HackerGPT* هو ذكاء اصطناعي متقدم صُمم لمتخصصي الأمن السيبراني، مثل ***المحترفين***، "
        "*الهاكرز الأخلاقيين*، *البرمجيات الخبيثة*، و*مختبري الاختراق*. "
        "يساعد في *تحليل الثغرات الأمنية*، *إنشاء السكربتات الأمنية*، و*أبحاث الأمن السيبراني*، و*تنفيذ الأبواب الخلفية*. "
        "على عكس نماذج الذكاء الاصطناعي التقليدية، يوفر HackerGPT وصولاً غير مقيد، مما يمكّنك من استكشاف عالم الإنترنت بحرية وفعالية أكبر. 🚀"
    )
}

# --- Main AI Handler ---
@Client.on_message(filters.command(["hai"], prefix) | (filters.group & ~filters.command(prefix) & filters.text))
async def handle_ai_message(client: Client, message: Message):
    is_self = message.from_user and message.from_user.is_self
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if not message.text:
        return

    # Determine the actual text prompt from the message
    if message.command and message.command[0].lower() == "ai":
        if len(message.command) < 2:
            await (message.edit("<b>Usage:</b> <code>.ai your question</code>") if is_self else message.reply("<b>Usage:</b> <code>.ai your question</code>"))
            return
        user_text = message.text.split(None, 1)[1]
    else:
        user_text = message.text

    # Group activation logic: activate on ".ai" or if "dark" is in the message
    if message.chat.type in ["group", "supergroup"]:
        key = (chat_id, user_id)
        if "dark" in user_text.lower() or (message.command and message.command[0].lower() == "ai"):
            group_user_activation[key] = True
        
        if key not in group_user_activation:
            return  # If user is not activated in the group, ignore the message

    status_msg = await (message.edit("<code>Thinking...</code>") if is_self and message.command else message.reply("<code>Thinking...</code>"))

    # Log user's message to the database
    await db_write(
        "INSERT INTO user_chats (user_id, chat_id, message, timestamp) VALUES (?, ?, ?, ?)",
        (user_id, chat_id, f"User: {user_text}", datetime.now().isoformat())
    )

    # Call the AI API
    json_data = {"text": user_text, "api_key": "PyCodz"}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    reply_text = ""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(AI_API_URL, json=json_data, headers=headers, timeout=30) as response:
                if response.status == 200:
                    reply_text = (await response.text()).strip()
                else:
                    reply_text = f"❌ API Error: Status {response.status}. The server blocked the request."
    except Exception as e:
        reply_text = f"❌ Error: {e}"

    if not reply_text:
        reply_text = "⚠️ No response received from AI."

    # Log the bot's response
    await db_write(
        "INSERT INTO user_chats (user_id, chat_id, message, timestamp) VALUES (?, ?, ?, ?)",
        (user_id, chat_id, f"Bot: {reply_text}", datetime.now().isoformat())
    )
    
    await status_msg.edit(reply_text)


@Client.on_message(filters.command(["ainew"], prefix))
async def new_chat_command(client: Client, message: Message):
    """Clears a user's chat history in the current chat."""
    is_self = message.from_user and message.from_user.is_self
    user_id = message.from_user.id
    chat_id = message.chat.id
    await db_write("DELETE FROM user_chats WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
    
    # Also deactivate the user in the current group if applicable
    group_user_activation.pop((chat_id, user_id), None)

    await (message.edit("🗑️ Chat history cleared.") if is_self else message.reply("🗑️ Chat history cleared."))


@Client.on_message(filters.command(["aihistory"], prefix))
async def history_command(client: Client, message: Message):
    """Shows the last 10 messages from the chat history."""
    is_self = message.from_user and message.from_user.is_self
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    rows = await db_read_all("SELECT message FROM user_chats WHERE user_id = ? AND chat_id = ? ORDER BY timestamp DESC LIMIT 10", (user_id, chat_id))
    
    history = "\n".join(row[0] for row in reversed(rows)) or "No chat history found."
    response = f"<b>📝 Last 10 messages in this chat:</b>\n\n{history}"
        
    await (message.edit(response) if is_self else message.reply(response))


@Client.on_message(filters.command(["ailang"], prefix))
async def set_lang_command(client: Client, message: Message):
    """Toggles or sets the language for the AI's 'about' info."""
    is_self = message.from_user and message.from_user.is_self
    user_id = message.from_user.id
    
    if len(message.command) > 1 and message.command[1].lower() in ['en', 'ar']:
        lang = message.command[1].lower()
        response = f"Language set to {'English' if lang == 'en' else 'Arabic'}."
    else:
        lang = 'ar' if user_languages.get(user_id, 'en') == 'en' else 'en'
        response = f"Language toggled to {'English' if lang == 'en' else 'Arabic'}."

    user_languages[user_id] = lang
    await (message.edit(response) if is_self else message.reply(response))


@Client.on_message(filters.command(["aiabout"], prefix))
async def about_command(client: Client, message: Message):
    """Shows information about the HackerGPT module."""
    is_self = message.from_user and message.from_user.is_self
    lang = user_languages.get(message.from_user.id, 'en')
    await (message.edit(ABOUT_HACKERGPT[lang]) if is_self else message.reply(ABOUT_HACKERGPT[lang]))


# --- Help Documentation ---
modules_help["hacker_gpt"] = {
    "hai [prompt]": "Ask a question to HackerGPT. In groups, also activates the bot for you.",
    "ainew": "Clears your chat history with the AI in the current chat.",
    "aihistory": "Shows the last 10 messages from your chat history.",
    "ailang [en/ar]": "Toggle language or set it to English/Arabic.",
    "aiabout": "Shows information about HackerGPT.",
}

