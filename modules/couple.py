import random
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from utils.misc import modules_help, prefix

# --- Main Command ---
@Client.on_message(filters.command("couple", prefix) & filters.me & filters.group)
async def couple_of_the_day(client: Client, message: Message):
    """Selects two random members from a group and announces them as a couple."""
    await message.edit("<code>Searching for today's lucky couple...</code>")
    
    try:
        members = []
        # Asynchronously iterate through all members of the chat
        async for member in client.get_chat_members(message.chat.id):
            # We only want to include real users, not bots
            if not member.user.is_bot:
                members.append(member.user)

        if len(members) < 2:
            await message.edit("<b>Not enough members in this group to choose a couple!</b>")
            return

        # Randomly select two unique members from the list
        chosen_ones = random.sample(members, 2)
        
        user1 = chosen_ones[0]
        user2 = chosen_ones[1]

        # Create mentions for the selected users
        mention1 = f"<a href='tg://user?id={user1.id}'>{user1.first_name}</a>"
        mention2 = f"<a href='tg://user?id={user2.id}'>{user2.first_name}</a>"

        # A list of fun announcement messages to choose from
        couple_messages = [
            f"💖 Today's Chosen Couple is 💖\n\n{mention1} 💞 {mention2}\n\nA match made in heaven (or at least, in this group)!",
            f"✨ The stars have aligned! ✨\n\nAnnouncing today's power couple:\n{mention1} and {mention2}!",
            f"💘 Cupid has been busy! 💘\n\nThe couple of the day is...\n{mention1} + {mention2} = ❤️",
            f"🎉 Congratulations! 🎉\n\nThe randomly selected couple for today is:\n{mention1} & {mention2}!",
        ]
        
        # --- Animate the announcement for a bit of fun ---
        await message.edit("<code>Finding the perfect match...</code>")
        await asyncio.sleep(1)
        await message.edit("<code>Aligning the stars...</code>")
        await asyncio.sleep(1)
        
        # Send the final announcement
        await message.edit(random.choice(couple_messages), disable_web_page_preview=True)

    except Exception as e:
        await message.edit(f"<b>An error occurred:</b> <code>{e}</code>")

# --- Add to modules_help ---
modules_help["couple_game"] = {
    "couple": "Randomly selects two users in a group to be the 'couple of the day'."
}
