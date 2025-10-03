# -*- coding: utf-8 -*-

#   .d8888b. 88888888888 8888888b.   .d8888b.  8888888b.
#  d88P  Y88b    888     888   Y88b d88P  Y88b 888   Y88b
#  Y88b.         888     888    888 888    888 888    888
#   "Y888b.      888     888   d88P 888    888 888   d88P
#      "Y88b.    888     8888888P"  888    888 8888888P"
#        "888    888     888 T88b   888    888 888 T88b
#  Y88b  d88P    888     888  T88b  Y88b  d88P 888  T88b
#   "Y8888P"     888     888   T88b  "Y8888P"  888   T88b

# STICKER STORY | [v1.1] - Weave a tale from digital expressions.
# A Moon Userbot Module for generating stories based on a user's stickers.

import asyncio
import io
import random
from pyrogram import Client, filters
from pyrogram.raw import functions
from pyrogram.types import Message
from PIL import Image

from utils.misc import modules_help, prefix
from utils.scripts import format_exc

# --- Configuration ---
ANIMATION_DELAY = 0.3
ANIMATION_FRAMES_TEXT = ["📖", "📜", "✒️", "✨"]


async def animate_status(message: Message, text: str):
    """Animates the status message."""
    for frame in ANIMATION_FRAMES_TEXT * 2:
        await message.edit(f"<i>{text} {frame}</i>")
        await asyncio.sleep(ANIMATION_DELAY)


def analyze_sticker_vibes(sticker_files):
    """
    A simple 'AI' to determine personality vibes from sticker images.
    This is a fun, simplified analysis based on color brightness.
    """
    brightness_scores = []
    total_pixels = 0
    for sticker_file in sticker_files:
        try:
            image = Image.open(sticker_file).convert("L")  # Convert to grayscale
            pixels = image.getdata()
            brightness = sum(pixels) / len(pixels)
            brightness_scores.append(brightness)
        except Exception:
            continue

    if not brightness_scores:
        return "Enigmatic", "A mysterious figure whose secrets are well-kept."

    avg_brightness = sum(brightness_scores) / len(brightness_scores)

    if avg_brightness > 150:
        return "Ray of Sunshine", "A cheerful soul who lights up any room."
    elif avg_brightness > 100:
        return "Chill Adventurer", "A cool and collected individual, always ready for fun."
    elif avg_brightness > 60:
        return "Master of Sass", "Witty, sharp, and unapologetically clever."
    else:
        return "Creature of the Night", "A mysterious and cool character with a love for the dramatic."


def generate_story(user_name, personality_trait, description):
    """Generates a short, mad-libs style story."""
    
    plots = [
        (
            f"In a world powered by memes, {user_name}, known as the '{personality_trait}', "
            f"discovered a legendary lost sticker pack. It was said that this pack contained the ultimate reaction GIF, "
            f"capable of winning any online argument. Their quest began, armed with nothing but their wits and {description.lower()}."
        ),
        (
            f"{user_name}, the kingdom's renowned '{personality_trait}', was summoned by the Emoji King. "
            f"A rogue AI was turning every chat into cringey boomer-tier jokes. It was up to {user_name} "
            f"to venture into the Digital Sea and restore balance, a task perfectly suited for {description.lower()}."
        ),
        (
            f"One day, while scrolling through their DMs, {user_name} found a cryptic message. It was a map, leading to the "
            f"mythical 'Fountain of Unlimited Wi-Fi'. As the local '{personality_trait}', they knew this was a destiny they had to follow. "
            f"After all, a hero like {description.lower()} can't turn down such a call to adventure."
        ),
    ]
    return random.choice(plots)


@Client.on_message(filters.command("stickerstory", prefix) & filters.me)
async def create_sticker_story(client: Client, message: Message):
    """Generates a personality analysis and story from a user's stickers."""
    target_user = None
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            target_user = await client.get_users(message.command[1])
        except Exception:
            await message.edit("<b>User not found.</b>")
            return
    else:
        await message.edit("<b>Please reply to a user or provide a username/ID.</b>")
        return

    await message.edit("<code>[ACCESSING STICKER ARCHIVES...]</code>")
    try:
        # The correct way to get a user's recently used stickers.
        # The previous attempt to get a specific sticker set was incorrect and has been removed.
        recent_stickers = await client.invoke(functions.messages.GetRecentStickers(hash=0))
        
        if not recent_stickers.stickers:
            await message.edit(f"<b>Could not access the sticker soul of {target_user.first_name}. They are a mystery.</b>")
            return

        await animate_status(message, "Analyzing digital expressions...")

        sticker_files = []
        # Analyze the top 5 most recent stickers as a proxy for their favorites.
        for sticker in recent_stickers.stickers[:5]:
            # We need to construct a proper file reference to download the sticker.
            if hasattr(sticker, 'file_reference'):
                 sticker_data = await client.download_media(sticker, in_memory=True)
                 sticker_files.append(sticker_data)

        if not sticker_files:
            await message.edit(f"<b>Could not download any stickers for {target_user.first_name}. Their essence is protected.</b>")
            return

        personality, description = analyze_sticker_vibes(sticker_files)
        story = generate_story(target_user.first_name, personality, description)

        await animate_status(message, "Weaving a narrative...")

        result_text = f"""
<code>--==[ STICKER SOUL ANALYSIS ]==--</code>

<b>Subject:</b> <code>{target_user.first_name}</code>
<b>Personality Profile:</b> <code>{personality}</code>
<i>"{description}"</i>

📜 <b>Your Story Begins...</b>
<i>{story}</i>
"""
        await message.edit(result_text)

    except Exception as e:
        await message.edit(
            f"<b>[A NARRATIVE ANOMALY OCCURRED]</b>\n\n"
            f"<b>The story could not be written.</b>\n"
            f"<code>ERROR: {format_exc(e)}</code>"
        )


modules_help["sticker_story"] = {
    "stickerstory [reply/username]": "Analyzes a user's recent stickers to determine their 'vibe' and writes a short, fun story about them."
}