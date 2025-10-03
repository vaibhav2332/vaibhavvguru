# -*- coding: utf-8 -*-

#      .o.       .o8        .o8   o8o      .
#     .888.     "888       "888   `"'    .o8
#    .8"888.     888oooo.   888oooo.   oooo  .o88b. .o88b.
#   .8' `888.    d88' `88b  d88' `88b  `888 d88""88 d8P  Y8
#  .88ooo8888.   888   888  888   888   888 888  888 88888888
# .8'     `888.  888   888  888   888   888 Y88..88 Y8b.
#.8'       `888. `Y8bod8P'  `Y8bod8P'   888  `Y88P'  `Y8888
#                                      888
#                                  .o. 88P
#                                  `Y888P

# CELESTIAL BOND | [v1.0] - Map the stars of your connection.
# A Moon Userbot Module for creating digital constellations.

import asyncio
import io
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pyrogram import Client, filters
from pyrogram.types import Message

from utils.misc import modules_help, prefix
from utils.scripts import format_exc

# --- Configuration ---
ANIMATION_DELAY = 0.3
ANIMATION_FRAMES = ["✦", "✧", "★", "☆"]
IMG_WIDTH = 1080
IMG_HEIGHT = 1080
BG_COLOR = "#0a0a1a"
STAR_COLOR = "#FFFFFF"
MAIN_STAR_COLOR = "#FFFF00"
LINE_COLOR = "#ADD8E6"
TEXT_COLOR = "#FFFFFF"


async def animate_celestial_mapping(message: Message, text: str):
    """Animates the message to build anticipation."""
    for frame in ANIMATION_FRAMES * 2:
        await message.edit(f"<i>{text} {frame}</i>")
        await asyncio.sleep(ANIMATION_DELAY)


def generate_constellation_image(user1_name, user1_id, user2_name, user2_id):
    """Generates a constellation image based on two user IDs."""
    img = Image.new('RGB', (IMG_WIDTH, IMG_HEIGHT), color=BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Use a basic font if a specific one isn't found
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except IOError:
        font = ImageFont.load_default()

    # Generate background stars
    for _ in range(150):
        x = random.randint(0, IMG_WIDTH)
        y = random.randint(0, IMG_HEIGHT)
        size = random.randint(1, 4)
        draw.ellipse((x, y, x + size, y + size), fill=STAR_COLOR)

    # Determine main star positions using a deterministic hash of user IDs
    padding = 150
    x1 = padding + (user1_id % (IMG_WIDTH - 2 * padding))
    y1 = padding + ((user1_id // 1000) % (IMG_HEIGHT - 2 * padding))
    x2 = padding + (user2_id % (IMG_WIDTH - 2 * padding))
    y2 = padding + ((user2_id // 1000) % (IMG_HEIGHT - 2 * padding))

    # Ensure stars are not too close to each other
    if np.sqrt((x1 - x2)**2 + (y1 - y2)**2) < 200:
        x2 = IMG_WIDTH - x2

    # Draw connection line
    draw.line((x1, y1, x2, y2), fill=LINE_COLOR, width=2)

    # Draw main stars
    star_size = 12
    draw.ellipse((x1 - star_size, y1 - star_size, x1 + star_size, y1 + star_size), fill=MAIN_STAR_COLOR, outline=BG_COLOR)
    draw.ellipse((x2 - star_size, y2 - star_size, x2 + star_size, y2 + star_size), fill=MAIN_STAR_COLOR, outline=BG_COLOR)
    
    # Add user names
    draw.text((x1 + 20, y1), user1_name, font=font, fill=TEXT_COLOR)
    draw.text((x2 + 20, y2), user2_name, font=font, fill=TEXT_COLOR)

    # Save image to a byte buffer
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.name = 'constellation.png'
    img_buffer.seek(0)
    
    return img_buffer


@Client.on_message(filters.command("couple", prefix) & filters.me)
async def map_celestial_bond(client: Client, message: Message):
    """Generates a cosmic compatibility reading and constellation."""
    if not message.reply_to_message:
        await message.edit("<b>Please reply to a user to map your celestial bond.</b>")
        return

    await message.edit("<code>[INITIALIZING COSMIC SCANNER...]</code>")
    try:
        user1 = message.from_user
        user2 = message.reply_to_message.from_user

        await animate_celestial_mapping(message, "Aligning digital destinies...")

        # --- Generate Compatibility Reading ---
        id_diff = abs(user1.id - user2.id)
        sync_score = 100 - (id_diff % 10000) / 100
        resonance = (user1.id + user2.id) % 100
        
        reading = f"""
<code>--==[ CELESTIAL BOND ANALYSIS ]==--</code>

<b>FROM:</b> <code>{user1.first_name}</code>
<b>TO:</b> <code>{user2.first_name}</code>

✨ <b>Cosmic Sync:</b> <code>{sync_score:.2f}%</code>
<i>A measure of digital harmony. High scores indicate a deep, unspoken alignment.</i>

💫 <b>Resonance Frequency:</b> <code>{resonance} MHz</code>
<i>The unique vibrational energy of your connection.</i>

📜 <b>Cosmic Summary:</b>
<i>The stars suggest a bond of significant potential. The unique constellation formed by your digital essences is a testament to a connection written in the cosmos.</i>
"""

        await animate_celestial_mapping(message, "Mapping cosmic connection...")
        constellation_img = generate_constellation_image(user1.first_name, user1.id, user2.first_name, user2.id)

        await client.send_photo(
            chat_id=message.chat.id,
            photo=constellation_img,
            caption=reading,
            reply_to_message_id=message.reply_to_message.id
        )
        await message.delete()

    except Exception as e:
        await message.edit(
            f"<b>[A COSMIC ANOMALY OCCURRED]</b>\n\n"
            f"<b>The bond could not be mapped.</b>\n"
            f"<code>ERROR: {format_exc(e)}</code>"
        )


modules_help["celestial_bond"] = {
    "couple [reply]": "Generates a beautiful constellation image and a 'Cosmic Compatibility' reading based on your and a replied-to user's digital IDs."
}