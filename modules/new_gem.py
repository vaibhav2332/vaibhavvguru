import aiohttp
import os
import re
import json
import codecs
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from pyrogram.errors import MessageTooLong
from urllib.parse import quote

# Assuming these are part of your userbot framework
try:
    from utils.misc import modules_help, prefix
    from utils.scripts import format_exc
except ImportError:
    # Dummy variables for standalone testing
    prefix = "."
    modules_help = {}
    def format_exc(e):
        return str(e)

# --- Configuration ---
API_CONFIG = {
    "pro": {
        "url": "https://sii3.top/api/gemini-dark.php",
        "param": "gemini-pro",
        "method": "POST_JSON"
    },
    "deep": {
        "url": "https://sii3.top/api/gemini-dark.php",
        "param": "gemini-deep",
        "method": "POST_JSON"
    },
    "flash": {
        "url": "https://sii3.top/DARK/gemini.php",
        "param": "text",
        "method": "POST_FORM"
    }
}
DEFAULT_MODEL = "pro"
AVAILABLE_MODELS = list(API_CONFIG.keys())


# --- Constants ---
TELEGRAM_MAX_MSG_LENGTH = 4096
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
}

# --- Reusable function to query the Gemini APIs ---
async def query_gemini_api(prompt: str, model: str) -> str | None:
    """
    Queries the appropriate Gemini API based on the selected model.
    Returns the "response" text on success, otherwise an error message.
    """
    config = API_CONFIG.get(model)
    if not config:
        return "Invalid model specified."

    payload = {config["param"]: prompt}

    try:
        async with aiohttp.ClientSession() as session:
            if config["method"] == "POST_JSON":
                headers = {**BROWSER_HEADERS, "Content-Type": "application/json"}
                async with session.post(config["url"], json=payload, headers=headers, timeout=300) as response:
                    json_data = await response.json(content_type=None)
            else:  # POST_FORM
                headers = BROWSER_HEADERS
                async with session.post(config["url"], data=payload, headers=headers, timeout=300) as response:
                    json_data = await response.json(content_type=None)

            if response.status == 200 and json_data and json_data.get("response"):
                return json_data.get("response")
            else:
                error_text = await response.text()
                print(f"Gemini API Error ({model}): Status {response.status}, Response: {error_text}")
                return f"API request failed with status code {response.status}."
    except Exception as e:
        print(f"An exception occurred while querying the Gemini API ({model}): {format_exc(e)}")
        return f"An exception occurred: {str(e)}"

# --- Formatted Viewer Link Generation ---
def create_viewer_link(raw_text: str) -> str:
    """
    Creates a self-contained, shareable Data URI that renders the text
    with Markdown and LaTeX in a browser.
    """
    # Use json.dumps to safely escape the text for JavaScript embedding
    js_safe_text = json.dumps(raw_text)

    # A minimal HTML template that includes Marked.js (for Markdown) and MathJax (for LaTeX)
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Formatted Text Viewer</title>
        <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
        <script>
            MathJax = {{
                tex: {{
                    inlineMath: [['$', '$'], ['\\(', '\\)']],
                    displayMath: [['$$', '$$'], ['\\[', '\\]']]
                }},
                svg: {{
                    fontCache: 'global'
                }}
            }};
        </script>
        <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; padding: 20px; max-width: 800px; margin: auto; background-color: #f8f9fa; color: #212529; }}
            code {{ background-color: #e9ecef; padding: 2px 4px; border-radius: 3px; font-family: monospace; }}
            pre {{ background-color: #e9ecef; padding: 15px; border-radius: 5px; overflow-x: auto; }}
            pre code {{ padding: 0; background-color: transparent; border: none; }}
            blockquote {{ border-left: 5px solid #ccc; margin-left: 0; padding-left: 15px; color: #666; }}
        </style>
    </head>
    <body>
        <div id="content"></div>
        <script>
            const rawText = {js_safe_text};
            // Use marked.js to parse markdown first
            document.getElementById('content').innerHTML = marked.parse(rawText);
            // Then, typeset the math with MathJax
            MathJax.typesetPromise();
        </script>
    </body>
    </html>
    """
    
    # URL-encode the entire minified HTML document
    encoded_html = quote(html_template.replace('\n', '').replace('    ', ''))
    
    # Create and return the Data URI
    return f"data:text/html;charset=utf-8,{encoded_html}"


# --- Advanced Formatting Engine for Telegram ---
def advanced_format(text: str) -> str:
    """
    Processes raw API text to handle escape sequences and convert
    Markdown-like notations to Telegram HTML.
    """
    try:
        processed_text = codecs.decode(text, 'unicode_escape')
    except Exception:
        processed_text = text.replace('\\n', '\n').replace('\\t', '\t')

    # Markdown to HTML conversions
    processed_text = re.sub(r'```(\w+)?\n(.*?)```', r'<pre><code class="\1">\2</code></pre>', processed_text, flags=re.DOTALL)
    processed_text = re.sub(r'```(.*?)```', r'<pre><code>\1</code></pre>', processed_text, flags=re.DOTALL)
    processed_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', processed_text)
    processed_text = re.sub(r'__(.*?)__', r'<b>\1</b>', processed_text)
    processed_text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', processed_text)
    processed_text = re.sub(r'(?<!\w)_(.*?)_(?!\w)', r'<i>\1</i>', processed_text)
    processed_text = re.sub(r'`(.*?)`', r'<code>\1</code>', processed_text)
    
    # We will NOT convert LaTeX to code tags so the viewer can render it.
    # The Telegram message will just show the raw LaTeX.
    
    return processed_text.strip()

# --- Main Gemini Command ---
@Client.on_message(filters.command("gemini", prefix) & filters.me)
async def gemini_command(client: Client, message: Message):
    """
    Interacts with various Gemini models using a single command and provides a viewer link.
    """
    parts = message.text.split(maxsplit=2)
    model = DEFAULT_MODEL
    prompt = ""

    if len(parts) < 2:
        return await message.edit_text(
            "<b>🎄 Unified Gemini AI</b>\n\n"
            "<b>Usage:</b> <code>.gemini [-model] &lt;prompt&gt;</code>\n\n"
            "<b>Available Models:</b>\n"
            f"• <code>-flash</code> (Gemini 2.5 Flash)\n"
            f"• <code>-pro</code> (Default: Gemini Pro)\n"
            f"• <code>-deep</code> (Gemini 2.5 Deep Search)\n\n"
            "<b>Example:</b> <code>.gemini -pro write a python script to list files</code>",
            parse_mode=enums.ParseMode.HTML
        )

    potential_flag = parts[1].replace("-", "")
    if potential_flag in AVAILABLE_MODELS:
        model = potential_flag
        if len(parts) > 2:
            prompt = parts[2]
        else:
            return await message.edit_text("<b>Error:</b> Please provide a prompt after the model flag.", parse_mode=enums.ParseMode.HTML)
    else:
        prompt = message.text.split(maxsplit=1)[1]

    status_msg = await message.edit_text(f"<b>🎄 Thinking with Gemini ({model})...</b>", parse_mode=enums.ParseMode.HTML)

    api_response = await query_gemini_api(prompt, model)

    if not api_response or "API request failed" in api_response:
        error_message = api_response if api_response else f"The Gemini API ({model}) did not return a valid response."
        return await status_msg.edit_text(f"<b>❗️ Error:</b> {error_message}", parse_mode=enums.ParseMode.HTML)

    formatted_text = advanced_format(api_response)
    viewer_link = create_viewer_link(api_response)

    response_header = f"<b>🎄 Gemini AI ({model})</b>\n\n"
    response_footer = f'\n\n<a href="{viewer_link}">View as Formatted Text</a>'
    
    full_response = response_header + formatted_text + response_footer

    try:
        await status_msg.edit_text(
            full_response,
            disable_web_page_preview=True,
            parse_mode=enums.ParseMode.HTML
        )
    except MessageTooLong:
        await status_msg.edit_text("<b>Response is too long, sending as a file...</b>", parse_mode=enums.ParseMode.HTML)
        file_path = f"gemini_{model}_response_{message.id}.txt"
        try:
            file_content = f"Formatted Viewer Link: {viewer_link}\n\n---\n\n{formatted_text}"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(file_content)

            await client.send_document(
                chat_id=message.chat.id,
                document=file_path,
                caption=f"<b>🎄 Gemini AI ({model}) Response</b>\n\n<b>Prompt:</b> <code>{prompt[:100]}...</code>",
                reply_to_message_id=message.id,
                parse_mode=enums.ParseMode.HTML
            )
            await status_msg.delete()
        except Exception as e:
            await status_msg.edit_text(f"<b>Error sending file:</b>\n<code>{format_exc(e)}</code>", parse_mode=enums.ParseMode.HTML)
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

# --- Help Section ---
modules_help["gemini"] = {
    "gemini [-model] <prompt>": "Ask questions to various Gemini models. Includes a link to view the response with proper formatting."
}

