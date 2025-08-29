import os
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from utils.misc import modules_help, prefix
from utils.scripts import import_library

# --- Import and check for FPDF library ---
try:
    FPDF = import_library("fpdf").FPDF
except Exception:
    FPDF = None

# --- .txt command ---
@Client.on_message(filters.command("txt", prefix) & filters.me & filters.reply)
async def text_to_txt(client: Client, message: Message):
    """Converts a text message to a .txt file."""
    if not message.reply_to_message.text:
        await message.edit("<b>Error:</b> Please reply to a message with text.", parse_mode=enums.ParseMode.HTML)
        return

    await message.edit("<code>Processing...</code>")

    file_path = f"text_file_{message.id}.txt"
    replied_text = message.reply_to_message.text

    try:
        # Write the text to a file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(replied_text)

        # Upload the file
        await client.send_document(
            chat_id=message.chat.id,
            document=file_path,
            caption="Here is your .txt file."
        )
        await message.delete()

    except Exception as e:
        await message.edit(f"<b>An error occurred:</b> <code>{e}</code>", parse_mode=enums.ParseMode.HTML)
    finally:
        # Clean up the created file
        if os.path.exists(file_path):
            os.remove(file_path)

# --- .pdf command ---
@Client.on_message(filters.command("pdf", prefix) & filters.me & filters.reply)
async def text_to_pdf(client: Client, message: Message):
    """Converts a text message to a .pdf file."""
    if FPDF is None:
        await message.edit(
            "<b>Error: Dependency missing!</b>\n\n"
            "The <code>fpdf</code> library is not installed.\n"
            "Please add it to your <b>requirements.txt</b> and restart/redeploy the bot.",
            parse_mode=enums.ParseMode.HTML
        )
        return
        
    if not message.reply_to_message.text:
        await message.edit("<b>Error:</b> Please reply to a message with text.", parse_mode=enums.ParseMode.HTML)
        return

    await message.edit("<code>Creating PDF...</code>")
    
    file_path = f"pdf_file_{message.id}.pdf"
    replied_text = message.reply_to_message.text

    try:
        pdf = FPDF()
        pdf.add_page()
        # Add a font that supports a wide range of characters
        pdf.add_font('DejaVu', '', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', uni=True)
        pdf.set_font('DejaVu', '', 12)
        
        # Write the text to the PDF
        pdf.multi_cell(0, 10, replied_text)
        pdf.output(file_path)

        # Upload the file
        await client.send_document(
            chat_id=message.chat.id,
            document=file_path,
            caption="Here is your .pdf file."
        )
        await message.delete()

    except Exception as e:
        # Provide a helpful error if the font file is missing
        if "No such file or directory" in str(e) and "DejaVuSans.ttf" in str(e):
             await message.edit(
                "<b>Error: Font not found!</b>\n\n"
                "This module requires the DejaVu font. If on Debian/Ubuntu, install it with:\n"
                "<code>sudo apt-get install ttf-dejavu</code>",
                parse_mode=enums.ParseMode.HTML
            )
        else:
            await message.edit(f"<b>An error occurred:</b> <code>{e}</code>", parse_mode=enums.ParseMode.HTML)
    finally:
        # Clean up the created file
        if os.path.exists(file_path):
            os.remove(file_path)

# ############################################################### #
# #################### HIGHLIGHTED CHANGE START ################### #
# ############################################################### #
# --- .py command ---
@Client.on_message(filters.command("py", prefix) & filters.me & filters.reply)
async def text_to_py(client: Client, message: Message):
    """Converts a text message to a .py file."""
    if not message.reply_to_message.text:
        await message.edit("<b>Error:</b> Please reply to a message with text.", parse_mode=enums.ParseMode.HTML)
        return

    await message.edit("<code>Creating .py file...</code>")

    file_path = f"python_file_{message.id}.py"
    replied_text = message.reply_to_message.text

    try:
        # Write the text to a file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(replied_text)

        # Upload the file
        await client.send_document(
            chat_id=message.chat.id,
            document=file_path,
            caption="Here is your .py file."
        )
        await message.delete()

    except Exception as e:
        await message.edit(f"<b>An error occurred:</b> <code>{e}</code>", parse_mode=enums.ParseMode.HTML)
    finally:
        # Clean up the created file
        if os.path.exists(file_path):
            os.remove(file_path)
# ############################################################### #
# #################### HIGHLIGHTED CHANGE END ##################### #
# ############################################################### #


# --- Add to modules_help ---
modules_help["fileconverter"] = {
    "txt (reply to text)": "Converts the replied text message into a .txt document.",
    "pdf (reply to text)": "Converts the replied text message into a .pdf document.",
    # #################### HIGHLIGHTED CHANGE ################### #
    "py (reply to text)": "Converts the replied text message into a .py document.",
}
