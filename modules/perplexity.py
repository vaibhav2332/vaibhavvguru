# =========================================================================================
#               ADVANCED TELEGRAM BOT FORWARDER WITH DYNAMIC ANIMATIONS
# =========================================================================================
# This script provides a userbot functionality to forward prompts to another bot
# and retrieve the response, displaying a variety of engaging animations
# to the user while they wait.
#
# Features:
# - Forwards prompts for both text (.pi) and photo (.pic) generation.
# - A rich library of randomly selected, "mindblowing" status animations.
# - Robust polling mechanism to handle bots that edit their messages.
# - Clean, refactored code with helper functions for readability and maintenance.
# - Detailed error handling and user feedback.
# - Comprehensive docstrings and comments explaining the functionality.
# - MODIFIED: Edits the owner's message with the response, but replies to other users.
# - MODIFIED: Reacts to messages from other users to acknowledge the command.
# =========================================================================================

import asyncio
import random
import math
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from pyrogram.errors import PeerIdInvalid

# Assuming these are part of your userbot framework which defines 'prefix'
# and the 'modules_help' dictionary.
try:
    from utils.misc import modules_help, prefix
except ImportError:
    # Define dummy variables if the framework is not available, for standalone testing
    prefix = "."
    modules_help = {}

# =========================================================================================
#                                     CONFIGURATION
# =========================================================================================

class ModuleConfig:
    """
    Centralized configuration for the bot forwarder module.
    Edit these values to change the bot's behavior.
    """
    # The username of the bot you want to forward messages to.
    BOT_USERNAME = '@askplexbot'

    # Maximum time in seconds to wait for a complete response from the bot.
    OVERALL_TIMEOUT_SECONDS = 500

    # How long to wait for a new message from the bot before assuming it's done (for multi-message responses).
    SILENCE_TIMEOUT_SECONDS = 30

    # How often to check the bot's chat history for new messages.
    POLL_INTERVAL_SECONDS = 2

    # Keywords that indicate the bot is still processing a request.
    PROCESSING_KEYWORDS = ["processing", "thinking", "generating", "typing", "...", "⏳"]


# =========================================================================================
#                         MIND-BLOWING ANIMATION EFFECTS LIBRARY
# =========================================================================================
# This section contains all the animation functions. Each function takes a
# status message and a stop event, and it will loop its animation until
# the stop event is set by the main logic.

async def animate_progress_bar(status_message: Message, stop_event: asyncio.Event):
    """Effect 1: A dynamic, back-and-forth progress bar."""
    base_text = "<b>Thinking...</b>"
    emojis = ["🤔", "🤖", "💡", "✨", "✅"]
    
    while not stop_event.is_set():
        # Animate forwards
        for i in range(11):
            if stop_event.is_set(): break
            progress = "▓" * i
            spaces = "░" * (10 - i)
            emoji = emojis[i % len(emojis)]
            text = f"{base_text} {emoji}\n`[{progress}{spaces}]`"
            try:
                await status_message.edit_text(text)
                await asyncio.sleep(0.2)
            except Exception: return
        
        await asyncio.sleep(0.5)

        # Animate backwards
        for i in range(10, -1, -1):
            if stop_event.is_set(): break
            progress = "▓" * i
            spaces = "░" * (10 - i)
            emoji = emojis[i % len(emojis)]
            text = f"{base_text} {emoji}\n`[{progress}{spaces}]`"
            try:
                await status_message.edit_text(text)
                await asyncio.sleep(0.2)
            except Exception: return

async def animate_emoji_cycle(status_message: Message, stop_event: asyncio.Event):
    """Effect 2: A cycling sequence of emojis and status texts."""
    states = [
        ("<b>Processing</b>", "🤔"),
        ("<b>Analyzing Query</b>", "🤖"),
        ("<b>Generating Content</b>", "💡"),
        ("<b>Finalizing</b>", "✨")
    ]
    while not stop_event.is_set():
        for text, emoji in states:
            if stop_event.is_set(): break
            try:
                await status_message.edit_text(f"{text} {emoji}")
                await asyncio.sleep(0.8)
            except Exception: return

async def animate_loading_dots(status_message: Message, stop_event: asyncio.Event):
    """Effect 3: Classic animated loading dots."""
    base_text = "<b>Generating Response</b>"
    while not stop_event.is_set():
        for i in range(4):
            if stop_event.is_set(): break
            dots = "." * i
            try:
                await status_message.edit_text(f"{base_text}{dots}")
                await asyncio.sleep(0.5)
            except Exception: return

async def animate_rocket_launch(status_message: Message, stop_event: asyncio.Event):
    """Effect 4: A rocket launching towards a goal."""
    base_text = "<b>Sending Request to AI...</b>"
    track_length = 10
    while not stop_event.is_set():
        for i in range(track_length + 1):
            if stop_event.is_set(): break
            rocket_pos = i
            trail = "~" * (i - 1) if i > 0 else ""
            sky = " " * (track_length - rocket_pos)
            text = f"{base_text}\n`[{trail}🚀{sky}]` 🌍"
            try:
                await status_message.edit_text(text)
                await asyncio.sleep(0.3)
            except Exception: return
        await asyncio.sleep(1)

async def animate_matrix_rain(status_message: Message, stop_event: asyncio.Event):
    """Effect 5: A cool 'Matrix' style digital rain effect."""
    base_text = "<b>Accessing Neural Network...</b>"
    chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    while not stop_event.is_set():
        if stop_event.is_set(): break
        line1 = "".join(random.choice(chars) for _ in range(15))
        line2 = "".join(random.choice(chars) for _ in range(15))
        text = f"{base_text}\n`{line1}`\n`{line2}`"
        try:
            await status_message.edit_text(text)
            await asyncio.sleep(0.2)
        except Exception: return

async def animate_clock(status_message: Message, stop_event: asyncio.Event):
    """Effect 6: A spinning clock emoji."""
    base_text = "<b>Awaiting Response...</b>"
    clock_faces = ["🕛", "🕐", "🕑", "🕒", "🕓", "🕔", "🕕", "🕖", "🕗", "🕘", "🕙", "🕚"]
    while not stop_event.is_set():
        for face in clock_faces:
            if stop_event.is_set(): break
            try:
                await status_message.edit_text(f"{base_text} {face}")
                await asyncio.sleep(0.5)
            except Exception: return

# List of all available animation effects. The script will randomly pick one.
ANIMATION_EFFECTS = [
    animate_progress_bar, 
    animate_emoji_cycle, 
    animate_loading_dots,
    animate_rocket_launch,
    animate_matrix_rain,
    animate_clock
]

# =========================================================================================
#                                     HELPER FUNCTIONS
# =========================================================================================
# These functions break down the main logic into smaller, reusable pieces.

def get_prompt_from_message(message: Message) -> str:
    """
    Extracts the text prompt from a user's message, whether it's a new
    command or a reply to another message.
    """
    text_to_send = ""
    if message.reply_to_message:
        # If replying, use the text or caption of the replied-to message.
        text_to_send = message.reply_to_message.text or message.reply_to_message.caption
    elif len(message.command) > 1:
        # If not a reply, use the text that follows the command.
        text_to_send = " ".join(message.command[1:])
    
    return text_to_send.strip() if text_to_send else ""

async def setup_bot_interaction(client: Client, bot_username: str) -> tuple:
    """
    Gets the bot's user object and the ID of the last message in its history.
    Handles potential errors like an invalid username.
    """
    try:
        bot = await client.get_users(bot_username)
        last_message_id = 0
        async for msg in client.get_chat_history(bot.id, limit=1):
            last_message_id = msg.id
        return bot, last_message_id, None
    except (PeerIdInvalid, ValueError):
        error = f"`Error: Bot username '{bot_username}' is invalid or not found.`"
        return None, None, error
    except Exception as e:
        error = f"`An unexpected error occurred during setup: {e}`"
        return None, None, error

async def run_forwarder_with_animation(
    client: Client, 
    message: Message, 
    forwarding_logic: callable
):
    """
    A wrapper function that handles the entire process:
    1. Gets the user's prompt.
    2. Sets up and starts a random animation.
    3. Executes the main forwarding logic.
    4. Stops the animation and cleans up the status message.
    """
    prompt = get_prompt_from_message(message)
    if not prompt:
        await message.reply_text("`Please provide a prompt or reply to a message.`")
        return

    is_owner = message.from_user and message.from_user.is_self
    status_message = None

    if is_owner:
        # If owner, use the original message for animations and edits.
        status_message = message
        await status_message.edit_text("<b>Initializing...</b>")
    else:
        # If another user, create a new reply for status updates and react.
        status_message = await message.reply_text("<b>Initializing...</b>")
        try:
            await message.react("🤖")
        except Exception:
            # Bot may not have permission to react.
            pass

    # --- Random Animation Setup ---
    chosen_animation = random.choice(ANIMATION_EFFECTS)
    stop_animation = asyncio.Event()
    animation_task = asyncio.create_task(chosen_animation(status_message, stop_animation))
    
    try:
        # Execute the specific logic for pic or pi
        await forwarding_logic(client, message, prompt, status_message, stop_animation)
    except Exception as e:
        # Catch any unexpected errors from the main logic
        await client.send_message(message.chat.id, f"`A critical error occurred: {e}`")
    finally:
        # --- Stop Animation and Cleanup ---
        # This block ensures the animation always stops.
        stop_animation.set()
        await animation_task
        # If not the owner, delete the temporary status message.
        # Owner's message is either edited or deleted by the fetcher function.
        if not is_owner and status_message:
            try:
                await status_message.delete()
            except Exception:
                # Message might have already been deleted, which is fine.
                pass

# =========================================================================================
#                                 CORE FORWARDING LOGIC
# =========================================================================================
# These functions contain the specific logic for fetching photo and text responses.

async def fetch_pic_response(client: Client, message: Message, prompt: str, status_message: Message, stop_event: asyncio.Event):
    """
    The core logic for the .pic command.
    Sends the prompt, polls for a photo, and forwards it.
    """
    destination_chat_id = message.chat.id
    is_owner = message.from_user and message.from_user.is_self
    await client.send_chat_action(destination_chat_id, enums.ChatAction.UPLOAD_PHOTO)
    
    bot, last_message_id, error = await setup_bot_interaction(client, ModuleConfig.BOT_USERNAME)
    if error:
        await status_message.edit(error)
        await asyncio.sleep(3)
        return

    await client.send_message(bot.id, prompt)

    response_count = 0
    loop_start_time = asyncio.get_event_loop().time()
    last_bot_activity_time = loop_start_time

    # Poll until the bot is silent for a defined period.
    while asyncio.get_event_loop().time() - last_bot_activity_time < ModuleConfig.SILENCE_TIMEOUT_SECONDS:
        if asyncio.get_event_loop().time() - loop_start_time > ModuleConfig.OVERALL_TIMEOUT_SECONDS:
            break

        history = [msg async for msg in client.get_chat_history(bot.id, limit=20)]
        for response in reversed(history):
            if response.from_user and response.from_user.id == bot.id and response.id > last_message_id:
                last_bot_activity_time = asyncio.get_event_loop().time()
                last_message_id = response.id
                if response.photo:
                    caption = f"🎨 **Generated Image for:**\n`{prompt}`"
                    if is_owner:
                        # For owner, stop animation, delete original message, and send photo.
                        stop_event.set()
                        await asyncio.sleep(0.1) # Allow animation to stop gracefully
                        try:
                            await status_message.delete()
                        except Exception: pass
                        await client.send_photo(
                            chat_id=destination_chat_id,
                            photo=response.photo.file_id,
                            caption=caption
                        )
                        return # Exit as we have handled the response and cleanup.
                    else:
                        # For other users, reply to their command.
                        await client.send_photo(
                            chat_id=destination_chat_id,
                            photo=response.photo.file_id,
                            caption=caption,
                            reply_to_message_id=message.id
                        )
                    response_count += 1
        await asyncio.sleep(ModuleConfig.POLL_INTERVAL_SECONDS)

    if response_count == 0:
        await client.send_message(destination_chat_id, "<i>Bot did not provide a photo response in time.</i>")

async def fetch_pi_response(client: Client, message: Message, prompt: str, status_message: Message, stop_event: asyncio.Event):
    """
    The core logic for the .pi command.
    Sends the prompt, waits for a final text message (handles edited messages), and forwards it.
    """
    destination_chat_id = message.chat.id
    is_owner = message.from_user and message.from_user.is_self
    await client.send_chat_action(destination_chat_id, enums.ChatAction.TYPING)
    
    bot, last_message_id, error = await setup_bot_interaction(client, ModuleConfig.BOT_USERNAME)
    if error:
        await status_message.edit(error)
        await asyncio.sleep(3)
        return

    await client.send_message(bot.id, prompt)

    bot_response_message = None
    find_response_timeout = 30
    start_time = asyncio.get_event_loop().time()
    
    # First, find the initial response message from the bot.
    while asyncio.get_event_loop().time() - start_time < find_response_timeout:
        history = [msg async for msg in client.get_chat_history(bot.id, limit=5)]
        for response in reversed(history):
            if response.from_user and response.from_user.id == bot.id and response.id > last_message_id:
                bot_response_message = response
                break
        if bot_response_message:
            break
        await asyncio.sleep(1)

    if not bot_response_message:
        await client.send_message(destination_chat_id, "<i>Bot did not respond initially.</i>")
        return

    response_count = 0
    monitor_timeout = 270
    start_time = asyncio.get_event_loop().time()
    
    # Now, monitor that specific message for edits until it's a final answer.
    while asyncio.get_event_loop().time() - start_time < monitor_timeout:
        current_bot_message = await client.get_messages(bot.id, bot_response_message.id)
        if not current_bot_message:
            break

        is_final_answer = True
        if current_bot_message.text:
            if any(p_text in current_bot_message.text.lower() for p_text in ModuleConfig.PROCESSING_KEYWORDS):
                is_final_answer = False

        if is_final_answer:
            final_text = current_bot_message.text or current_bot_message.caption
            if is_owner:
                # For owner, stop animation and edit the original message with the final text.
                stop_event.set()
                await asyncio.sleep(0.1)
                await status_message.edit(final_text, parse_mode=enums.ParseMode.MARKDOWN)
            else:
                # For other users, send the final text as a reply.
                await client.send_message(
                    chat_id=destination_chat_id,
                    text=final_text,
                    reply_to_message_id=message.id,
                    parse_mode=enums.ParseMode.MARKDOWN
                )
            response_count += 1
            break
        await asyncio.sleep(2)

    if response_count == 0:
        await client.send_message(destination_chat_id, "<code>Bot response timed out. Please try again.</code>")

# =========================================================================================
#                                     COMMAND HANDLERS
# =========================================================================================
# These are the entry points that Pyrogram listens for. They call the main
# wrapper function with the appropriate logic.

@Client.on_message(filters.command("pic", prefix) & filters.me)
async def pic_command_handler(client: Client, message: Message):
    """Handles the .pic command by triggering the forwarder with the photo-fetching logic."""
    await run_forwarder_with_animation(client, message, fetch_pic_response)

@Client.on_message(filters.command("pi", prefix) & filters.me)
async def pi_command_handler(client: Client, message: Message):
    """Handles the .pi command by triggering the forwarder with the text-fetching logic."""
    await run_forwarder_with_animation(client, message, fetch_pi_response)

# =========================================================================================
#                                 FUTURE FEATURE STUBS
# =========================================================================================
# These are placeholders for future functionality to demonstrate how the script
# could be expanded further.

async def get_usage_stats():
    """
    Placeholder for a function to retrieve usage statistics.
    This could be implemented using a simple dictionary or a database.
    """
    # For example:
    # stats = {"pic_success": 10, "pic_fail": 2, "pi_success": 25, "pi_fail": 5}
    # return stats
    pass

@Client.on_message(filters.command("pstats", prefix) & filters.me)
async def stats_command_handler(client: Client, message: Message):
    """A command to show usage statistics for the forwarder."""
    await message.reply_text("`Statistics feature is not yet implemented.`")

@Client.on_message(filters.command("psetbot", prefix) & filters.me)
async def set_bot_command_handler(client: Client, message: Message):
    """A command to allow users to set a different target bot username."""
    await message.reply_text("`Bot configuration feature is not yet implemented.`")

# =========================================================================================
#                                     HELP MODULE
# =========================================================================================
# This section provides help text for the userbot's help command.

modules_help["animated_forwarder"] = {
    "pic [prompt]": "Forwards a prompt to get a photo response, with cool animations.",
    "pic [reply]": "Replies to a message to get a photo response, with cool animations.",
    "pi [prompt]": "Forwards a prompt to get a text response, with cool animations.",
    "pi [reply]": "Replies to a message to get a text response, with cool animations.",
    "pstats": "(Coming Soon) Shows usage statistics for the forwarder.",
    "psetbot [username]": "(Coming Soon) Sets a new target bot for forwarding.",
}