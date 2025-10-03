# -*- coding: utf-8 -*-

#   `7MMF'  `7MMF'                    `7MM"""YMM
#     MM      MM                        MM    `7
#     MM      MM  ,pW"Wq.`7MMpMMp.      MM   d `7MMpMMp.
#     MM      MM 6W'   `Wb MM a `7      MMmmMM   MM a `7
#     MM      MM 8M     M8 MM          MM   Y  , MM
#     MM      MM YA.   ,A9 MM          MM     ,d MM
#   .JMML.  .JMML.`Ybmd9'.JMML.      .JMMmmmmmd .JMML.

# VIBE CHECK | [v1.0] - Analyze the sentiment of your connection.
# A Moon Userbot Module for creating a relationship dashboard from chat history.

import asyncio
from collections import Counter
from pyrogram import Client, filters
from pyrogram.types import Message

from utils.misc import modules_help, prefix
from utils.scripts import format_exc

# --- Simple Sentiment & Affection Lexicon (No external libraries needed) ---
AFFECTION_WORDS = {
    'love', 'adore', 'cute', 'sweet', 'honey', 'baby', 'darling',
    'beautiful', 'handsome', 'gorgeous', 'lovely', 'miss', 'hugs', 'kisses'
}
POSITIVE_EMOJIS = {'❤️', '😍', '😘', '🥰', '😊', '💕', '💖', '✨', '😂', '♥️'}

async def animate_status(message: Message, text: str):
    """Animates the status message."""
    frames = ["🔬", "⚗️", "📈", "💞"]
    for frame in frames * 2:
        await message.edit(f"<i>{text} {frame}</i>")
        await asyncio.sleep(0.3)


@Client.on_message(filters.command("vibecheck", prefix) & filters.me)
async def analyze_vibe(client: Client, message: Message):
    """Analyzes the chat history between two users and generates a report."""
    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.edit("<b>Please reply to your partner's message to run a Vibe Check.</b>")
        return

    user1 = message.from_user
    user2 = message.reply_to_message.from_user

    await animate_status(message, "Analyzing your conversational dynamics...")

    try:
        user1_messages = 0
        user2_messages = 0
        affection_score = 0
        emoji_counts = Counter()
        total_messages_analyzed = 0

        # Fetch last 100 messages in the current chat
        async for msg in client.get_chat_history(message.chat.id, limit=100):
            if not msg.from_user or not msg.text:
                continue

            # Filter for messages from only the two users
            if msg.from_user.id not in [user1.id, user2.id]:
                continue
            
            total_messages_analyzed += 1
            text_lower = msg.text.lower()
            words = text_lower.split()

            # Tally messages
            if msg.from_user.id == user1.id:
                user1_messages += 1
            else:
                user2_messages += 1

            # Calculate affection score
            for word in words:
                if word in AFFECTION_WORDS:
                    affection_score += 1

            # Count positive emojis
            for char in msg.text:
                if char in POSITIVE_EMOJIS:
                    emoji_counts[char] += 1
        
        if total_messages_analyzed < 10:
             await message.edit(f"<b>Not enough recent chat history between you and {user2.first_name} to perform a vibe check.</b>")
             return

        # --- Generate the Report ---
        vibe = "Warm & Fuzzy"
        if affection_score > 20:
            vibe = "Super Sweet! 🥰"
        elif affection_score > 10:
            vibe = "Playful & Cute 😊"

        # Create Talk-o-Meter
        total_talk = user1_messages + user2_messages
        user1_perc = round((user1_messages / total_talk) * 10) if total_talk > 0 else 5
        user2_perc = 10 - user1_perc
        talk_o_meter = f"[{'█' * user1_perc}{'░' * user2_perc}]"

        # Find top emoji
        top_emoji = emoji_counts.most_common(1)[0][0] if emoji_counts else "None"

        report = f"""
<code>--==[   OUR VIBE REPORT   ]==--</code>

<b>Connection:</b> <code>{user1.first_name} & {user2.first_name}</code>
<b>Analysis Period:</b> Last {total_messages_analyzed} messages.

💞 <b>Overall Vibe:</b> {vibe}
<i>A sentiment analysis suggests a positive and affectionate dynamic. Keep it up!</i>

🗣️ <b>Talk-o-Meter:</b>
<code>You {talk_o_meter} Them</code>
<i>A summary of your chat participation.</i>

💖 <b>Affection Score:</b> <code>{affection_score}</code>
<i>Calculated based on the frequency of affectionate terms.</i>

✨ <b>Top Emoji:</b> {top_emoji}
<i>The most-used positive emoji in your recent chats.</i>
"""
        await message.edit(report)

    except Exception as e:
        await message.edit(f"<b>[VIBE ANALYSIS FAILED]</b>\n<code>{format_exc(e)}</code>")


modules_help["vibecheck"] = {
    "vibecheck [reply]": "Analyzes the recent chat history with a user to generate a 'Vibe Report'."
}