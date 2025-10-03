# -*- coding: utf-8 -*-

#   .o88b.  .d88b.  .88b  d88.  .d88b.  d8888b. db    db
#  d8P  Y8 .8P  Y8. 88'YbdP`88 .8P  Y8. 88  `8D `8b  d8'
#  8P      88    88 88  88  88 88    88 88oodD'  `8bd8'
#  8b      88    88 88  88  88 88    88 88~~~      88
#  Y8b  d8 `8b  d8' 88  88  88 `8b  d8' 88         88
#   `Y88P'  `Y88P'  YP  YP  YP  `Y88P'  88         YP
#
#   DIGITAL ORACLE | [v1.0] - Gaze into the digital soul.
#   A Moon Userbot Module for Divination.

import asyncio
import random
from pyrogram import Client, filters
from pyrogram.raw import functions
from pyrogram.types import Message

from utils.misc import modules_help, prefix
from utils.scripts import format_exc

# --- Configuration ---
ANIMATION_DELAY = 0.3
ANIMATION_FRAMES = ["◢", "◣", "◤", "◥"]

# --- Mystical Data Pools (Expand these for more variety!) ---
AURA_COLORS = [
    "a shimmering aura of <b>Cerulean Blue</b>, signifying deep wisdom",
    "a vibrant energy pulsating with <b>Emerald Green</b>, indicating profound growth",
    "a gentle glow of <b>Amethyst Purple</b>, revealing a creative spirit",
    "a fierce flicker of <b>Crimson Red</b>, a sign of unstoppable passion",
    "a steady warmth of <b>Golden Yellow</b>, symbolizing pure optimism",
    "a mysterious shimmer of <b>Silver Light</b>, hinting at hidden potential",
]

SPIRIT_ANIMALS = [
    "The <b>Eagle</b>; a master of perspective and spiritual connection",
    "The <b>Wolf</b>; a creature of sharp instinct and loyalty",
    "The <b>Fox</b>; a symbol of cunning intellect and adaptability",
    "The <b>Owl</b>; a keeper of ancient knowledge and intuition",
    "The <b>Serpent</b>; an icon of transformation and creative life force",
    "The <b>Stag</b>; a beacon of leadership and quiet strength",
]

CORE_TRAITS = [
    "a spirit of <b>unyielding creativity</b> that shapes the world around them",
    "an intellect as sharp as <b>obsidian glass</b>, cutting through deception",
    "a heart filled with <b>boundless curiosity</b>, forever seeking the unknown",
    "a foundation of <b>quiet strength</b>, an anchor in any storm",
    "a soul that dances with <b>chaotic, brilliant energy</b>",
]

PROPHECIES = [
    "walks a path towards an <b>unexpected discovery</b> that will change everything",
    "is destined to forge a <b>connection of profound importance</b>",
    "will soon encounter a <b>challenge that will forge them into a legend</b>",
    "is a catalyst for change, destined to <b>inspire a great shift</b>",
    "holds the key to a <b>long-forgotten secret</b>",
]


async def animate_divination(message: Message, text: str):
    """Animates the text to build suspense."""
    for frame in ANIMATION_FRAMES * 2:
        await message.edit(f"<i>{text} {frame}</i>")
        await asyncio.sleep(ANIMATION_DELAY)


@Client.on_message(filters.command("oracle", prefix) & filters.me)
async def divine_fatum(client: Client, message: Message):
    """Gazes into the user's digital soul to reveal their fate."""
    await message.edit("`[AWAKENING THE ORACLE...]`")
    try:
        if len(message.command) >= 2:
            target_id = message.command[1]
        elif message.reply_to_message:
            target_id = message.reply_to_message.from_user.id
        else:
            target_id = "me"

        await animate_divination(message, "Gazing into the digital ether...")
        peer = await client.resolve_peer(target_id)
        response = await client.invoke(functions.users.GetFullUser(id=peer))
        user = response.users[0]

        # Use user data as a "seed" for consistent, personalized results
        seed = user.id
        first_name_seed = ord(user.first_name[0]) if user.first_name else 0

        await animate_divination(message, "Decoding the user's aura...")
        
        # Handle special cases for a more "intelligent" oracle
        if user.bot:
            reading = (
                f"👁️ <b>TARGET:</b> <code>{user.first_name}</code>\n\n"
                f"<b>AURA:</b> This entity is woven from pure logic. Its aura is a complex, shimmering <b>matrix of code</b>.\n\n"
                f"<b>ANALYSIS:</b> It is a being of service and computation. It follows the path laid by its creator, its destiny intertwined with its core programming.\n\n"
                f"<code>--==[ THE ORACLE HAS SPOKEN ]==--</code>"
            )
        elif user.scam:
            reading = (
                f"👁️ <b>TARGET:</b> <code>{user.first_name}</code>\n\n"
                f"<b>AURA:</b> A <b>shadowy, distorted miasma</b> clings to this one's digital trail. Caution is advised.\n\n"
                f"<b>ANALYSIS:</b> Deception clouds this spirit's intent. Their path is shrouded in mist and misdirection.\n\n"
                f"<code>--==[ THE ORACLE HAS SPOKEN ]==--</code>"
            )
        else:
            # Generate a standard, mystical reading
            aura = AURA_COLORS[seed % len(AURA_COLORS)]
            animal = SPIRIT_ANIMALS[(seed // 1000) % len(SPIRIT_ANIMALS)]
            trait = CORE_TRAITS[first_name_seed % len(CORE_TRAITS)]
            prophecy = PROPHECIES[(seed % 100) % len(PROPHECIES)]
            
            await animate_divination(message, "Weaving the threads of fate...")

            reading = f"""
<code>--==[ DIGITAL DIVINATION ]==--</code>

👁️ <b>TARGET:</b> <code>{user.first_name}</code>
🆔 <b>ESSENCE ID:</b> <code>{user.id}</code>

🔮 <b>AURA ANALYSIS:</b>
This user is surrounded by {aura}.

🐾 <b>SPIRITUAL SYMBOL:</b>
Their digital spirit resonates with that of {animal}.

✨ <b>CORE TRAIT:</b>
At their very core, the Oracle sees {trait}.

📜 <b>THE PROPHECY:</b>
The threads of fate show that this user {prophecy}.

<code>--==[ THE ORACLE HAS SPOKEN ]==--</code>
            """
        
        await message.edit(reading)

    except Exception as e:
        await message.edit(
            f"<b>[THE VISION IS CLOUDED]</b>\n\n"
            f"<b>The Oracle cannot see this user's fate clearly.</b>\n"
            f"<code>ERROR: {format_exc(e)}</code>"
        )


modules_help["oracle"] = {
    "oracle [reply|id|username]": "Gaze into the digital soul of a user to reveal their aura, spirit animal, and a prophecy about their fate."
}