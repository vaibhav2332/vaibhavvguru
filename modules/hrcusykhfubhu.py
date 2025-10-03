import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import (
    PeerFlood, UserPrivacyRestricted, UserNotMutualContact,
    UserChannelsTooMuch, UserBot, UserBannedInChannel
)
from utils.misc import modules_help, prefix
from utils.scripts import format_exc

@Client.on_message(filters.command("addall", prefix) & filters.me)
async def add_all_members(client: Client, message: Message):
    """Scrapes members from a source group and adds them to a target group."""
    if len(message.command) != 3:
        await message.edit(
            "<b>Usage:</b> <code>.addall [source_group_username] [target_group_username]</code>\n"
            "<i>Usernames should start with @ or be public links.</i>"
        )
        return

    source_group = message.command[1]
    target_group = message.command[2]
    
    status_message = await message.edit(f"<code>Processing...</code>")

    try:
        # --- Scrape members from the source group ---
        await status_message.edit(f"<code>Scraping members from {source_group}...</code>")
        scraped_members = []
        async for member in client.get_chat_members(source_group):
            # Only add real users who are not bots and have not deleted their accounts
            if not member.user.is_bot and not member.user.is_deleted:
                scraped_members.append(member.user)
        
        if not scraped_members:
            await status_message.edit(f"<b>Error:</b> Could not find any members to scrape from {source_group}.")
            return

        total_scraped = len(scraped_members)
        await status_message.edit(f"<code>Found {total_scraped} members. Starting to add...</code>")
        await asyncio.sleep(1)

        # --- Add members to the target group ---
        added_count = 0
        failed_count = 0
        
        for i, user in enumerate(scraped_members, 1):
            if i % 10 == 0: # Update status every 10 users
                await status_message.edit(
                    f"<b>Progress:</b> {i}/{total_scraped}\n"
                    f"<b>Added:</b> <code>{added_count}</code>\n"
                    f"<b>Failed:</b> <code>{failed_count}</code>"
                )

            try:
                await client.add_chat_members(target_group, user.id)
                added_count += 1
                # A delay is crucial to avoid being flagged for spam
                await asyncio.sleep(random.randint(3, 6))
            
            except PeerFlood:
                await status_message.edit(
                    "<b>Flood Wait Error!</b>\n"
                    "Telegram is limiting my actions. Stopping for now.\n\n"
                    f"<b>Final Report:</b>\n"
                    f" - Added: <code>{added_count}</code>\n"
                    f" - Failed: <code>{failed_count}</code>"
                )
                return
            
            except UserPrivacyRestricted:
                failed_count += 1
            except UserNotMutualContact:
                failed_count += 1
            except UserChannelsTooMuch:
                failed_count += 1
            except UserBot:
                failed_count += 1 # Should be filtered already, but just in case
            except UserBannedInChannel:
                failed_count += 1
            except Exception as e:
                failed_count += 1
                print(f"An unexpected error occurred for user {user.id}: {e}") # Log for debugging
            
        # --- Final Report ---
        await status_message.edit(
            f"✅ <b>Member Adding Complete!</b>\n\n"
            f"<b>Total Scraped:</b> <code>{total_scraped}</code>\n"
            f"<b>Successfully Added:</b> <code>{added_count}</code>\n"
            f"<b>Failed (due to privacy, etc.):</b> <code>{failed_count}</code>"
        )

    except Exception as e:
        await status_message.edit(format_exc(e))

modules_help["member_adder"] = {
    "addall [source] [target]": "Adds all members from the source group to the target group."
}