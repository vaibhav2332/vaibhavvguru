import aiohttp
from urllib.parse import quote_plus
from pyrogram import Client, filters
from pyrogram.types import Message
from utils.misc import modules_help, prefix

# --- API Configuration ---
BASE_URL = "https://allmodels.revangeapi.workers.dev/revangeapi/{model}/chat?prompt={prompt}"
AVAILABLE_MODELS = [
    "openai-gpt-oss-120b",
    "zai-org-GLM-4.5V",
    "openai-gpt-oss-20b",
    "moonshotai-Kimi-K2-Instruct",
    "allenai-olmOCR-7B-0725-FP8",
    "qwen3-coder",
]

# --- Helper Function ---
async def fetch_text(url):
    """Fetches plain text data from a URL."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.text()
    except aiohttp.ClientError:
        return None
    return None

# --- Command Handler ---
@Client.on_message(filters.command(["ask"], prefix))
async def ask_handler(client: Client, message: Message):
    """Handles the .ask command to query various AI models."""
    is_self = message.from_user and message.from_user.is_self
    
    args = message.text.split(maxsplit=2)
    numbered_models_list = "\n".join([f"<code>{i+1}. {model}</code>" for i, model in enumerate(AVAILABLE_MODELS)])
    
    if len(args) < 3:
        usage_text = (
            f"<b>Usage:</b> <code>{prefix}ask [model_number_or_name] [prompt]</code>\n\n"
            f"<b>Available Models:</b>\n{numbered_models_list}"
        )
        await (message.edit(usage_text) if is_self else message.reply(usage_text))
        return

    model_input = args[1]
    prompt = args[2]
    model = None

    # Try to resolve model by number first
    if model_input.isdigit():
        try:
            model_index = int(model_input) - 1
            if 0 <= model_index < len(AVAILABLE_MODELS):
                model = AVAILABLE_MODELS[model_index]
        except (ValueError, IndexError):
            pass  # Will be handled by the 'if not model' check

    # If not a valid number, try by name
    if model is None and model_input.lower() in AVAILABLE_MODELS:
        model = model_input.lower()

    if model is None:
        error_text = (
            f"<b>Invalid Model:</b> <code>{model_input}</code>\n\n"
            f"<b>Please choose from the available models by number or name:</b>\n{numbered_models_list}"
        )
        await (message.edit(error_text) if is_self else message.reply(error_text))
        return

    status_message = await (message.edit_text("<code>🤔 Thinking...</code>") if is_self else message.reply("<code>🤔 Thinking...</code>"))
    
    encoded_prompt = quote_plus(prompt)
    api_url = BASE_URL.format(model=model, prompt=encoded_prompt)

    response_text = await fetch_text(api_url)

    if response_text:
        try:
            final_response = f"<b>Model:</b> <code>{model}</code>\n\n<b>Response:</b>\n{response_text}"
            await status_message.edit_text(final_response)
        except Exception as e:
            await status_message.edit_text(f"<code>❌ An error occurred while processing the response: {e}</code>")
    else:
        await status_message.edit_text("<code>❌ Sorry, I couldn't get a response. The API might be down or the request timed out.</code>")

# --- Help Documentation ---
numbered_models_help = "\n" + "\n".join([f"• `{i+1}. {model}`" for i, model in enumerate(AVAILABLE_MODELS)])
modules_help["revange_ai"] = {
    "ask [model_number_or_name] [prompt]": "Ask a question to a specific AI model.",
    "Available Models": numbered_models_help,
}