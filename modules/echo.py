# -*- coding: utf-8 -*-

#   .d8888b.  888          888    .d8888b.
#  d88P  Y88b 888          888   d88P  Y88b
#  888    888 888          888   888    888
#  888        888  .d88b.  888   888
#  888        888 d88""88b 888   888  88888
#  888    888 888 888  888 888   888    888
#  Y88b  d88P 888 Y88..88P 888   Y88b  d88P
#   "Y8888P"  888  "Y88P"  888    "Y8888P"

# DIGITAL ECHO | [v1.1] - Visualize the resonance between two souls.
# A Moon Userbot Module for generating dynamic waveform GIFs.

import asyncio
import io
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pyrogram import Client, filters
from pyrogram.types import Message

from utils.misc import modules_help, prefix
from utils.scripts import format_exc

# --- Configuration ---
ANIMATION_DELAY = 0.3
ANIMATION_FRAMES_TEXT = ["✦", "✧", "★", "☆"]
IMG_SIZE = 512  # Keep it reasonable for faster generation
NUM_FRAMES = 45  # Number of frames in the GIF
TEXT_COLOR = (255, 255, 255)
WAVE_LENGTH = 30.0
SPEED = 4.0


def get_font(size: int) -> ImageFont:
    """Tries to load a common font, falls back to default."""
    common_fonts = ["DejaVuSans.ttf", "Arial.ttf", "Verdana.ttf"]
    for font_name in common_fonts:
        try:
            return ImageFont.truetype(font_name, size)
        except IOError:
            continue
    return ImageFont.load_default()


async def animate_status(message: Message, text: str):
    """Animates the status message."""
    for frame in ANIMATION_FRAMES_TEXT * 2:
        await message.edit(f"<i>{text} {frame}</i>")
        await asyncio.sleep(ANIMATION_DELAY)


def generate_echo_gif(user1_name, user1_id, user2_name, user2_id):
    """Generates a mesmerizing GIF of two interfering waveforms."""
    # Correctly seed the randomness for consistent but unique patterns.
    # The modulo operator ensures the seed is within the valid 32-bit range.
    seed_value = (user1_id + user2_id) % (2**32)
    np.random.seed(seed_value)

    # --- Setup coordinates and colors ---
    x = np.arange(0, IMG_SIZE, 1)
    y = np.arange(0, IMG_SIZE, 1)
    xx, yy = np.meshgrid(x, y)
    
    # Generate unique colors based on user IDs
    color1 = tuple(np.random.randint(100, 256, 3))
    color2 = tuple(np.random.randint(100, 256, 3))
    
    # Determine wave source positions
    padding = 100
    x1 = padding + (user1_id % (IMG_SIZE - 2 * padding))
    y1 = padding + ((user1_id // 1000) % (IMG_SIZE - 2 * padding))
    x2 = IMG_SIZE - x1 # Symmetrical placement
    y2 = IMG_SIZE - y1
    
    frames = []
    font = get_font(24)

    # --- Generate each frame of the GIF ---
    for t in range(NUM_FRAMES):
        # Calculate distance from each pixel to each source
        dist1 = np.sqrt((xx - x1)**2 + (yy - y1)**2)
        dist2 = np.sqrt((xx - x2)**2 + (yy - y2)**2)

        # Create the wave interference pattern using sine waves
        wave = (np.sin(dist1 / WAVE_LENGTH - t / SPEED) + 
                np.sin(dist2 / WAVE_LENGTH - t / SPEED))
        
        # Normalize the wave to color channels
        r = (np.sin(wave * np.pi) + 1) / 2 * color1[0] + (np.cos(wave * np.pi) + 1) / 2 * color2[0]
        g = (np.sin(wave * np.pi) + 1) / 2 * color1[1] + (np.cos(wave * np.pi) + 1) / 2 * color2[1]
        b = (np.sin(wave * np.pi) + 1) / 2 * color1[2] + (np.cos(wave * np.pi) + 1) / 2 * color2[2]

        # Combine channels into an image
        img_array = np.stack([r, g, b], axis=-1).astype(np.uint8)
        img = Image.fromarray(img_array, 'RGB')
        
        # Add names to the image
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), user1_name, font=font, fill=TEXT_COLOR)
        text_width, text_height = font.getbbox(user2_name)[2:4]
        draw.text((IMG_SIZE - 10 - text_width, IMG_SIZE - 10 - text_height),
                  user2_name, font=font, fill=TEXT_COLOR, align="right")

        frames.append(img)

    # --- Save frames to a byte buffer as a GIF ---
    gif_buffer = io.BytesIO()
    frames[0].save(
        gif_buffer,
        format='GIF',
        save_all=True,
        append_images=frames[1:],
        duration=50,  # Milliseconds per frame
        loop=0  # Loop forever
    )
    gif_buffer.name = 'digital_echo.gif'
    gif_buffer.seek(0)
    
    return gif_buffer


@Client.on_message(filters.command("echo", prefix) & filters.me)
async def create_digital_echo(client: Client, message: Message):
    """Generates a Digital Echo GIF and analysis."""
    if not message.reply_to_message:
        await message.edit("<b>Please reply to a user to generate your Digital Echo.</b>")
        return

    await message.edit("<code>[ANALYZING DIGITAL RESONANCE...]</code>")
    try:
        user1 = message.from_user
        user2 = message.reply_to_message.from_user

        await animate_status(message, "Calculating harmonic frequencies...")

        # --- Generate Compatibility Reading ---
        resonance_score = 100 - (abs(user1.id - user2.id) % 10000) / 100
        sync_wave = (user1.id % 100 + user2.id % 100) / 2
        
        reading = f"""
<code>--==[ DIGITAL ECHO SIGNATURE ]==--</code>

<b>Source A:</b> <code>{user1.first_name}</code>
<b>Source B:</b> <code>{user2.first_name}</code>

Their digital signatures have intertwined to create this unique resonance pattern.

🌊 <b>Resonance Score:</b> <code>{resonance_score:.2f}%</code>
<i>The degree of similarity in your digital frequencies.</i>

🌀 <b>Sync Wave:</b> <code>{sync_wave:.2f} nm</code>
<i>The characteristic wavelength of your combined digital echo.</i>
"""

        await animate_status(message, "Generating interference pattern...")
        echo_gif = generate_echo_gif(user1.first_name, user1.id, user2.first_name, user2.id)

        # Send the GIF. Note: send_animation is used for GIFs.
        await client.send_animation(
            chat_id=message.chat.id,
            animation=echo_gif,
            caption=reading,
            reply_to_message_id=message.reply_to_message.id
        )
        await message.delete()

    except Exception as e:
        await message.edit(
            f"<b>[A TEMPORAL ANOMALY OCCURRED]</b>\n\n"
            f"<b>The echo could not be rendered.</b>\n"
            f"<code>ERROR: {format_exc(e)}</code>"
        )


modules_help["digital_echo"] = {
    "echo [reply]": "Generates a beautiful, animated GIF of your 'Digital Echo' with another user, visualizing your digital resonance as interfering waves."
}