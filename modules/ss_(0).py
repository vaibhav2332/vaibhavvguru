import asyncio
import os
import time
import math
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from pyrogram.errors import MessageNotModified
from utils.misc import modules_help, prefix

# --- Import and check for required libraries using a standard method ---
try:
    import cv2
except ImportError:
    # If the library is not installed, cv2 will be None.
    # The command will then provide a clear error message to the user.
    cv2 = None

def format_size(size_bytes):
    """Formats size in bytes to a human-readable string."""
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

# --- Main Screenshot Command ---
@Client.on_message(filters.command("ss", prefix) & filters.me & filters.reply)
async def video_screenshot(client: Client, message: Message):
    """Takes a specified number of screenshots from a video."""
    if cv2 is None:
        await message.edit(
            "<b>Error: Dependency missing!</b>\n\n"
            "The <code>opencv-python-headless</code> library is not installed.\n"
            "Please add it to your <b>requirements.txt</b> and restart/redeploy the bot.",
            parse_mode=enums.ParseMode.HTML
        )
        return

    if not message.reply_to_message.video:
        await message.edit("<b>Error:</b> Please reply to a video file.", parse_mode=enums.ParseMode.HTML)
        return

    # --- Argument Parsing ---
    try:
        count = 1
        if len(message.command) > 1:
            count = int(message.command[1])
        if count <= 0:
            await message.edit("<b>Error:</b> Please provide a positive number for the count.", parse_mode=enums.ParseMode.HTML)
            return
    except (ValueError, IndexError):
        await message.edit("<b>Usage:</b> <code>.ss [count]</code> (reply to a video)", parse_mode=enums.ParseMode.HTML)
        return

    # --- Setup and Download ---
    last_update_time = time.time()
    async def progress(current, total):
        nonlocal last_update_time
        now = time.time()
        if now - last_update_time > 2:
            try:
                percent = (current / total) * 100
                await message.edit(f"<code>Downloading video... {percent:.1f}%</code>")
                last_update_time = now
            except MessageNotModified:
                pass
            except Exception:
                pass

    await message.edit("<code>Downloading video...</code>")
    video_path = await message.reply_to_message.download(progress=progress)
    
    if not video_path or not os.path.exists(video_path):
        await message.edit("<b>Error:</b> Failed to download the video file.")
        return

    # --- Video Processing ---
    try:
        await message.edit("<code>Processing video and taking screenshots...</code>")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            await message.edit("<b>Error:</b> Could not open video file.", parse_mode=enums.ParseMode.HTML)
            os.remove(video_path)
            return
            
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = total_frames / fps if fps > 0 else 0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        file_size = os.path.getsize(video_path)

        interval = duration / (count + 1)
        timestamps = [interval * (i + 1) for i in range(count)]
        
        screenshot_paths = []
        for i, ts in enumerate(timestamps):
            cap.set(cv2.CAP_PROP_POS_MSEC, ts * 1000)
            success, frame = cap.read()
            if success:
                screenshot_path = f"screenshot_{message.id}_{i+1}.jpg"
                cv2.imwrite(screenshot_path, frame)
                screenshot_paths.append(screenshot_path)

        cap.release()

        # --- Uploading Screenshots ---
        if not screenshot_paths:
            await message.edit("<b>Error:</b> Failed to capture any screenshots.", parse_mode=enums.ParseMode.HTML)
        else:
            await message.edit(f"<code>Uploading {len(screenshot_paths)} screenshots...</code>")
            
            stats_caption = (
                f"<b>Video Statistics:</b>\n"
                f"<b>Resolution:</b> <code>{width}x{height}</code>\n"
                f"<b>Duration:</b> <code>{int(duration)}s</code>\n"
                f"<b>FPS:</b> <code>{int(fps)}</code>\n"
                f"<b>Size:</b> <code>{format_size(file_size)}</code>"
            )

            # ############################################################### #
            # #################### HIGHLIGHTED CHANGE START ################### #
            # ############################################################### #
            # Send screenshots one by one instead of in a media group
            for i, path in enumerate(screenshot_paths):
                caption_to_send = stats_caption if i == 0 else None
                await client.send_photo(
                    chat_id=message.chat.id,
                    photo=path,
                    caption=caption_to_send
                )
                await asyncio.sleep(0.5) # Small delay between uploads
            # ############################################################### #
            # #################### HIGHLIGHTED CHANGE END ##################### #
            # ############################################################### #
            
            for path in screenshot_paths:
                os.remove(path)

    except Exception as e:
        await message.edit(f"<b>An error occurred:</b> <code>{e}</code>", parse_mode=enums.ParseMode.HTML)
    finally:
        if os.path.exists(video_path):
            os.remove(video_path)
        await message.delete()


# --- Add to modules_help ---
modules_help["screenshot"] = {
    "ss [count] (reply to video)": "Takes screenshots from a video and shows video stats."
}
