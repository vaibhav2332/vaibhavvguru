import asyncio
import os
import time
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from pyrogram.errors import MessageNotModified
from utils.misc import modules_help, prefix

# --- Import and check for required libraries using a standard method ---
try:
    from PIL import Image
except ImportError:
    Image = None

try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

# --- Main PDF Conversion Command ---
@Client.on_message(filters.command("ipdf", prefix) & filters.me & filters.reply)
async def images_to_pdf(client: Client, message: Message):
    """Downloads a sequence of images and converts them into a PDF."""
    # --- Dependency Check ---
    if Image is None or FPDF is None:
        missing_libs = []
        if Image is None:
            missing_libs.append("Pillow")
        if FPDF is None:
            missing_libs.append("fpdf")
        
        await message.edit(
            "<b>Error: Dependencies missing!</b>\n\n"
            f"Please add <code>{' '.join(missing_libs)}</code> to your "
            "<code>requirements.txt</code> file and restart the bot.",
            parse_mode=enums.ParseMode.HTML
        )
        return

    # --- Message Gathering Phase ---
    image_messages = []
    image_paths = []
    converted_image_paths = set()
    pdf_path = f"image_collection_{message.id}.pdf"

    try:
        start_message = message.reply_to_message
        chat_id = message.chat.id
        
        if not start_message.photo:
            await message.edit("<b>Error:</b> Please reply to the <u>first photo</u> of the sequence.", parse_mode=enums.ParseMode.HTML)
            return
            
        await message.edit("<code>Gathering consecutive images...</code>")
        
        # Start with the replied message
        image_messages.append(start_message)
        
        # ############################################################### #
        # #################### HIGHLIGHTED CHANGE START ################### #
        # ############################################################### #
        # Fetch subsequent messages sequentially and reliably
        current_id = start_message.id
        while len(image_messages) < 100:  # Safety limit of 100 images
            current_id += 1
            try:
                # Fetch the very next message
                next_message = await client.get_messages(chat_id, current_id)
                if next_message.photo:
                    image_messages.append(next_message)
                else:
                    # Stop if it's not a photo
                    break
            except Exception:
                # Stop if message doesn't exist or any other error
                break
        
        if not image_messages:
            await message.edit("<b>Error:</b> No images found to convert.")
            return

        # --- Download Phase ---
        for i, msg in enumerate(image_messages):
            await message.edit(f"<code>Downloading image {i+1}/{len(image_messages)}...</code>")
            path = await msg.download()
            image_paths.append(path)
            
        # --- Conversion Phase ---
        await message.edit(f"<code>Converting {len(image_paths)} images to PDF...</code>")
        
        pdf = FPDF()

        for i, image_path in enumerate(image_paths):
            try:
                with Image.open(image_path) as img:
                    if img.mode == 'RGBA':
                        img = img.convert('RGB')
                    
                    # Save the converted image to a temporary path to ensure compatibility
                    converted_path = f"converted_{message.id}_{i}.jpg"
                    img.save(converted_path, "JPEG")
                    converted_image_paths.add(converted_path)

                    width_px, height_px = img.size
                    aspect_ratio = height_px / width_px

                    # Determine orientation and page size
                    orientation = 'P' if height_px > width_px else 'L'
                    pdf.add_page(orientation=orientation)
                    
                    page_width = pdf.w - 20  # Page width with 10mm margins
                    page_height = pdf.h - 20 # Page height with 10mm margins

                    # Calculate image dimensions to fit within the page while maintaining aspect ratio
                    img_width_mm = page_width
                    img_height_mm = img_width_mm * aspect_ratio

                    if img_height_mm > page_height:
                        img_height_mm = page_height
                        img_width_mm = img_height_mm / aspect_ratio

                    # Center the image
                    x_pos = (pdf.w - img_width_mm) / 2
                    y_pos = (pdf.h - img_height_mm) / 2
                    
                    pdf.image(converted_path, x=x_pos, y=y_pos, w=img_width_mm)
            except Exception as e:
                print(f"Skipping image {image_path} due to error: {e}")
                continue
        # ############################################################### #
        # #################### HIGHLIGHTED CHANGE END ##################### #
        # ############################################################### #

        pdf.output(pdf_path)

        # --- Upload Phase ---
        await message.edit("<code>Uploading PDF...</code>")
        await client.send_document(
            chat_id=message.chat.id,
            document=pdf_path,
            caption=f"PDF created from {len(image_paths)} images."
        )
        await message.delete()

    except Exception as e:
        await message.edit(f"<b>An error occurred:</b> <code>{e}</code>", parse_mode=enums.ParseMode.HTML)
    finally:
        # --- Cleanup ---
        for path in image_paths:
            if os.path.exists(path):
                os.remove(path)
        for path in converted_image_paths: # Clean up converted images
            if os.path.exists(path):
                os.remove(path)
        if os.path.exists(pdf_path):
            os.remove(pdf_path)


# --- Add to modules_help ---
modules_help["img2pdf"] = {
    "ipdf (reply to first image)": "Downloads all consecutive images starting from the replied one and converts them to a PDF."
}
