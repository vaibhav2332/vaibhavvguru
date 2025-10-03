# -*- coding: utf-8 -*-

#   .d8888b.  .d8888b.  .d8888b. d8b   db d888888b d88888b .d8888b.
#   88  `8D  88  `8D  88  `8D 888o  88 `~~88~~' 88'     88  `8D
#   `88888b. `88888b. `88888b. 88V8o 88    88    88ooooo `88888b.
#       `8b     `8b     `8b 88 V8o88    88    88~~~~~     `8b
#   db   8D db   8D db   8D 88  V888    88    88.     db   8D
#   `8888Y'  `8888Y'  `8888Y' VP   V8P    YP    Y88888P `8888Y'

# POCKET PET | [v1.0] - Your very own adorable chat companion.
# A Moon Userbot Module for adopting and caring for a virtual pet.

import asyncio
import random
import time
from pyrogram import Client, filters
from pyrogram.types import Message

from utils.misc import modules_help, prefix

# --- Pet Data Store (simple in-memory dictionary) ---
# This will reset if the bot restarts, making the pet ephemeral and low-maintenance.
pet_data = {}

# --- ASCII Art for our cute pet ---
PET_ART = {
    "happy": """
      /\_/\\
     ( ^.^ )
     / > < \\
    """,
    "neutral": """
      /\_/\\
     ( o.o )
     / > < \\
    """,
    "hungry": """
      /\_/\\
     ( >.< )
     / > < \\
    """,
    "sleeping": """
      /\_/\\
     ( -.- ) zZz
     / > < \\
    """
}

# --- Helper Functions ---
def get_pet_status_text(user_id):
    """Generates the status text and art for the pet."""
    if user_id not in pet_data:
        return None

    pet = pet_data[user_id]
    art = PET_ART["neutral"]
    mood = "Content"

    if pet["happiness"] > 7:
        art = PET_ART["happy"]
        mood = "Joyful!"
    if pet["hunger"] < 3:
        art = PET_ART["hungry"]
        mood = "Grumpy and Hungry"
    if pet["happiness"] < 3:
        mood = "A little sad"
    if time.time() - pet.get("last_action_time", 0) > 1800: # Sleeps after 30 mins of inactivity
        art = PET_ART["sleeping"]
        mood = "Sleeping"


    status_text = f"<b>~ {pet['name']}'s Corner ~</b>\n"
    status_text += f"<code>{art}</code>\n"
    status_text += f"<b>Mood:</b> {mood}\n"
    status_text += f"<b>Happiness:</b> {'❤️' * pet['happiness']}{'🖤' * (10 - pet['happiness'])}\n"
    status_text += f"<b>Fullness:</b>  {'🍖' * pet['hunger']}{'🦴' * (10 - pet['hunger'])}"
    return status_text


async def update_pet_state(user_id):
    """Periodically degrade stats to make the pet feel alive."""
    if user_id not in pet_data:
        return

    # Small chance to degrade stats over time if not sleeping
    if time.time() - pet_data[user_id].get("last_action_time", 0) < 1800:
        if random.random() < 0.3:
            pet_data[user_id]["happiness"] = max(0, pet_data[user_id]["happiness"] - 1)
        if random.random() < 0.5:
            pet_data[user_id]["hunger"] = max(0, pet_data[user_id]["hunger"] - 1)


@Client.on_message(filters.command("adopt", prefix) & filters.me)
async def adopt_pet(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id in pet_data:
        await message.edit(f"<b>You already have a pet named {pet_data[user_id]['name']}!</b>")
        return

    if len(message.command) < 2:
        await message.edit("<b>Please give your new pet a name!</b>\n<code>.adopt [PetName]</code>")
        return

    pet_name = message.command[1]
    pet_data[user_id] = {
        "name": pet_name,
        "happiness": 7,
        "hunger": 7,
        "last_action_time": time.time(),
    }
    await message.edit(f"🎉 <b>Congratulations!</b> 🎉\n\nYou've adopted a new pocket pet named <b>{pet_name}</b>!\n\nUse <code>.petstatus</code> to check on them.")


@Client.on_message(filters.command(["petstatus", "pstatus"], prefix) & filters.me)
async def pet_status(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in pet_data:
        await message.edit("<b>You don't have a pet yet!</b>\nAdopt one with <code>.adopt [PetName]</code>")
        return

    await update_pet_state(user_id)
    status_text = get_pet_status_text(user_id)
    await message.edit(status_text)


@Client.on_message(filters.command("feed", prefix) & filters.me)
async def feed_pet(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in pet_data:
        await message.edit("<b>You don't have a pet to feed!</b>")
        return

    pet = pet_data[user_id]
    if pet["hunger"] >= 10:
        await message.edit(f"<b>{pet['name']} is already full and pushes the food away.</b>")
        return

    pet["hunger"] = min(10, pet["hunger"] + 3)
    pet["happiness"] = min(10, pet["happiness"] + 1)
    pet["last_action_time"] = time.time()

    await message.edit(f"You give <b>{pet['name']}</b> a tasty treat! 🍖\n\n{get_pet_status_text(user_id)}")


@Client.on_message(filters.command("pet", prefix) & filters.me)
async def pet_the_pet(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in pet_data:
        await message.edit("<b>You don't have a pet to give affection to!</b>")
        return

    pet = pet_data[user_id]
    if pet["happiness"] >= 10:
        await message.edit(f"<b>{pet['name']} is overjoyed with affection already!</b>")
        return
        
    pet["happiness"] = min(10, pet["happiness"] + 2)
    pet["last_action_time"] = time.time()

    await message.edit(f"You gently pet <b>{pet['name']}</b>. They purr happily! ❤️\n\n{get_pet_status_text(user_id)}")


modules_help["pocket_pet"] = {
    "adopt [name]": "Adopt a new virtual pet and give it a name.",
    "petstatus": "Check on your pet's mood and stats.",
    "feed": "Feed your pet to keep it happy and full.",
    "pet": "Give your pet some affection to raise its happiness.",
}