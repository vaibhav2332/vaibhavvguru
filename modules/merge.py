import os
import asyncio
from PyPDF2 import PdfMerger
from pyrogram import Client, filters
from pyrogram.types import Message

from utils.misc import modules_help, prefix
from utils.scripts import format_exc

@Client.on_message(filters.command("merge", prefix) & filters.me & filters.reply)
async def merge_pdfs(client: Client, message: Message):
    """Merges multiple PDF files into a single document."""
    
    # --- 1. Validate Input ---
    if not (message.reply_to_message and message.reply_to_message.document):
        return await message.edit_text("<b>Error:</b> Please reply to a PDF file to mark the end of the sequence.")

    if message.reply_to_message.document.mime_type != "application/pdf":
        return await message.edit_text("<b>Error:</b> You must reply to a PDF file.")

    status_msg = await message.edit_text("<b>Initializing PDF merger...</b>")

    # --- 2. Gather All PDFs in the Range ---
    try:
        await status_msg.edit_text("<b>🔎 Searching for PDF files to merge...</b>")
        
        # Get all messages between the command and the replied-to message
        message_ids = range(message.reply_to_message.id, message.id + 1)
        messages_in_range = await client.get_messages(message.chat.id, message_ids)
        
        pdf_messages = []
        for msg in messages_in_range:
            if msg.document and msg.document.mime_type == "application/pdf":
                pdf_messages.append(msg)
        
        if len(pdf_messages) < 2:
            return await status_msg.edit_text("<b>Error:</b> Found fewer than 2 PDFs to merge.")
            
        # The messages are fetched newest-first, so we reverse to get chronological order
        pdf_messages.reverse()
        
        await status_msg.edit_text(f"<b>✅ Found {len(pdf_messages)} PDF files. Starting download...</b>")

    except Exception as e:
        return await status_msg.edit_text(f"<b>Error while gathering files:</b>\n<code>{format_exc(e)}</code>")

    # --- 3. Download, Merge, and Upload ---
    downloaded_paths = []
    output_filename = "merged.pdf"
    # Allow user to specify a filename, e.g., .merge my_notes.pdf
    if len(message.command) > 1:
        output_filename = message.command[1]
        if not output_filename.lower().endswith(".pdf"):
            output_filename += ".pdf"

    try:
        # Download all the identified PDFs
        for i, doc_msg in enumerate(pdf_messages):
            await status_msg.edit_text(f"<b>Downloading file {i + 1}/{len(pdf_messages)}...</b>\n<code>{doc_msg.document.file_name}</code>")
            path = await client.download_media(doc_msg)
            downloaded_paths.append(path)

        # Merge the downloaded PDFs
        await status_msg.edit_text("<b>Merging all downloaded PDFs...</b>")
        merger = PdfMerger()
        for pdf_path in downloaded_paths:
            merger.append(pdf_path)
        
        merger.write(output_filename)
        merger.close()

        # Upload the final merged file
        await status_msg.edit_text("<b>Uploading the final merged document...</b>")
        await client.send_document(
            message.chat.id,
            document=output_filename,
            caption=f"<b>Successfully merged {len(pdf_messages)} PDFs into:</b>\n<code>{output_filename}</code>"
        )
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"<b>An error occurred during the process:</b>\n<code>{format_exc(e)}</code>")
    
    finally:
        # --- 4. Cleanup ---
        # Clean up all downloaded and merged files
        for path in downloaded_paths:
            if os.path.exists(path):
                os.remove(path)
        if os.path.exists(output_filename):
            os.remove(output_filename)


# --- Help Section ---
modules_help["merge"] = {
    "merge [filename.pdf]": "Reply to the last PDF in a series to merge them all into a single file. The bot will gather all PDFs between your command and the replied-to message. The filename is optional."
}

