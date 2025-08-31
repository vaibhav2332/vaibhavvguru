import asyncio
import random
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import UserNotParticipant, FloodWait

# This script assumes 'prefix' and 'modules_help' are defined elsewhere.
# A fallback is provided for standalone testing.
try:
    from utils.misc import modules_help, prefix
except ImportError:
    modules_help = {}
    prefix = "."

# A dictionary to store chat IDs and their corresponding list of emojis
# Format: {chat_id: [emoji1, emoji2, ...]}
ACTIVE_CHATS = {}

@Client.on_message(filters.command("react", prefix) & filters.me)
async def manage_autoreact(client: Client, message: Message):
    """Command to enable, disable, or modify auto-reactions in a chat."""
    chat_id = message.chat.id
    
    # Check if there are any arguments after the command
    if len(message.command) > 1:
        # Check for the "stop" command
        if message.command[1].lower() == "stop":
            if chat_id in ACTIVE_CHATS:
                del ACTIVE_CHATS[chat_id]
                await message.edit_text("<b>✅ Auto-reactions stopped for this chat.</b>")
            else:
                await message.edit_text("<b>❕ Auto-reactions were not active in this chat.</b>")
            return
        
        # If not "stop", treat all arguments as emojis
        emojis = message.command[1:]
        ACTIVE_CHATS[chat_id] = emojis
        await message.edit_text(
            f"<b>✅ Auto-reacting with random emojis from <code>{' '.join(emojis)}</code> in this chat.</b>"
            f"\n\nTo stop, use <code>.react stop</code>."
        )

    else:
        # Default behavior if only ".react" is sent (no arguments)
        ACTIVE_CHATS[chat_id] = ["👍"]
        await message.edit_text(
            f"<b>✅ Auto-reacting with '👍' in this chat.</b>"
            f"\n\nTo specify emojis, use, for example: <code>.react 👍 ❤️ 😂</code>"
        )


@Client.on_message(filters.all & ~filters.me, group=1)
async def auto_reactor(client: Client, message: Message):
    """The main handler that reacts to new messages with a random emoji."""
    # Check if the current chat is in our active list
    if message.chat.id in ACTIVE_CHATS:
        try:
            # Get the list of emojis for the current chat
            emoji_list = ACTIVE_CHATS.get(message.chat.id)
            if not emoji_list:
                return
            
            # Choose a random emoji from the provided list
            reaction_emoji = random.choice(emoji_list)

            # Add a small delay to feel more natural and avoid rate limits
            await asyncio.sleep(.1)
            
            # Send the reaction
            await client.send_reaction(
                chat_id=message.chat.id,
                message_id=message.id,
                emoji=reaction_emoji
            )
        except UserNotParticipant:
            # If the bot is no longer in the chat, remove it from the active list
            if message.chat.id in ACTIVE_CHATS:
                del ACTIVE_CHATS[message.chat.id]
            print(f"Left chat {message.chat.id}, stopping auto-reactions.")
        except FloodWait as e:
            # Handle Telegram's rate limiting by waiting
            print(f"FloodWait for {e.value} seconds. Pausing reactions.")
            await asyncio.sleep(e.value + 1)
        except Exception as e:
            # Catch any other unexpected errors to prevent crashes
            print(f"An error occurred in auto_reactor for chat {message.chat.id}: {e}")


# --- Update Help Menu ---
modules_help["autoreact"] = {
    "react [emojis]": "Start auto-reacting with space-separated emojis (e.g., .react 👍 ❤️ 😂). If no emojis are given, defaults to 👍.",
    "react stop": "Stop auto-reacting in that chat.",
}