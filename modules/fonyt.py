import asyncio
import random
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from utils.misc import modules_help, prefix

# --- Font Mappings ---
FONTS = {
    "bubbles": {'a': 'ⓐ', 'b': 'ⓑ', 'c': 'ⓒ', 'd': 'ⓓ', 'e': 'ⓔ', 'f': 'ⓕ', 'g': 'ⓖ', 'h': 'ⓗ', 'i': 'ⓘ', 'j': 'ⓙ', 'k': 'ⓚ', 'l': 'ⓛ', 'm': 'ⓜ', 'n': 'ⓝ', 'o': 'ⓞ', 'p': 'ⓟ', 'q': 'ⓠ', 'r': 'ⓡ', 's': 'ⓢ', 't': 'ⓣ', 'u': 'ⓤ', 'v': 'ⓥ', 'w': 'ⓦ', 'x': 'ⓧ', 'y': 'ⓨ', 'z': 'ⓩ'},
    "currency": {'a': '₳', 'b': '฿', 'c': '₵', 'd': 'Đ', 'e': 'Ɇ', 'f': '₣', 'g': '₲', 'h': 'Ⱨ', 'i': 'ł', 'j': 'J', 'k': '₭', 'l': 'Ⱡ', 'm': '₥', 'n': '₦', 'o': 'Ø', 'p': '₱', 'q': 'Q', 'r': 'Ɽ', 's': '₴', 't': '₮', 'u': 'Ʉ', 'v': 'V', 'w': '₩', 'x': 'Ӿ', 'y': 'Ɏ', 'z': 'Ⱬ'},
    "bold": {'a': '𝗮', 'b': '𝗯', 'c': '𝗰', 'd': '𝗱', 'e': '𝗲', 'f': '𝗳', 'g': '𝗴', 'h': '𝗵', 'i': '𝗶', 'j': '𝗷', 'k': '𝗸', 'l': '𝗹', 'm': '𝗺', 'n': '𝗻', 'o': '𝗼', 'p': '𝗽', 'q': '𝗾', 'r': '𝗿', 's': '𝘀', 't': '𝘁', 'u': '𝘂', 'v': '𝘃', 'w': '𝘄', 'x': '𝘅', 'y': '𝘆', 'z': '𝘇'},
    "italic": {'a': '𝘢', 'b': '𝘣', 'c': '𝘤', 'd': '𝘥', 'e': '𝘦', 'f': '𝘧', 'g': '𝘨', 'h': '𝘩', 'i': '𝘪', 'j': '𝘫', 'k': '𝘬', 'l': '𝘭', 'm': '𝘮', 'n': '𝘯', 'o': '𝘰', 'p': '𝘱', 'q': '𝘲', 'r': '𝘳', 's': '𝘴', 't': '𝘵', 'u': '𝘶', 'v': '𝘷', 'w': '𝘸', 'x': '𝘹', 'y': '𝘺', 'z': '𝘻'},
    "script": {'a': '𝒶', 'b': '𝒷', 'c': '𝒸', 'd': '𝒹', 'e': 'ℯ', 'f': '𝒻', 'g': 'ℊ', 'h': '𝒽', 'i': '𝒾', 'j': '𝒿', 'k': '𝓀', 'l': '𝓁', 'm': '𝓂', 'n': '𝓃', 'o': 'ℴ', 'p': '𝓅', 'q': '𝓆', 'r': '𝓇', 's': '𝓈', 't': '𝓉', 'u': '𝓊', 'v': '𝓋', 'w': '𝓌', 'x': '𝓍', 'y': '𝓎', 'z': '𝓏'},
    "gothic": {'a': '𝖆', 'b': '𝖇', 'c': '𝖈', 'd': '𝖉', 'e': '𝖊', 'f': '𝖋', 'g': '𝖌', 'h': '𝖍', 'i': '𝖎', 'j': '𝖏', 'k': '𝖐', 'l': '𝖑', 'm': '𝖒', 'n': '𝖓', 'o': '𝖔', 'p': '𝖕', 'q': '𝖖', 'r': '𝖗', 's': '𝖘', 't': '𝖙', 'u': '𝖚', 'v': '𝖛', 'w': '𝖜', 'x': '𝖝', 'y': '𝖞', 'z': '𝖟'},
    "monospace": {'a': '𝚊', 'b': '𝚋', 'c': '𝚌', 'd': '𝚍', 'e': '𝚎', 'f': '𝚏', 'g': '𝚐', 'h': '𝚑', 'i': '𝚒', 'j': '𝚓', 'k': '𝚔', 'l': '𝚕', 'm': '𝚖', 'n': '𝚗', 'o': '𝚘', 'p': '𝚙', 'q': '𝚚', 'r': '𝚛', 's': '𝚜', 't': '𝚝', 'u': '𝚞', 'v': '𝚟', 'w': '𝚠', 'x': '𝚡', 'y': '𝚢', 'z': '𝚣'},
    "upside_down": {'a': 'ɐ', 'b': 'q', 'c': 'ɔ', 'd': 'p', 'e': 'ǝ', 'f': 'ɟ', 'g': 'ƃ', 'h': 'ɥ', 'i': 'ı', 'j': 'ɾ', 'k': 'ʞ', 'l': 'l', 'm': 'ɯ', 'n': 'u', 'o': 'o', 'p': 'd', 'q': 'b', 'r': 'ɹ', 's': 's', 't': 'ʇ', 'u': 'n', 'v': 'ʌ', 'w': 'ʍ', 'x': 'x', 'y': 'ʎ', 'z': 'z'},
    "wide": {'a': 'ａ', 'b': 'ｂ', 'c': 'ｃ', 'd': 'ｄ', 'e': 'ｅ', 'f': 'ｆ', 'g': 'ｇ', 'h': 'ｈ', 'i': 'ｉ', 'j': 'ｊ', 'k': 'ｋ', 'l': 'ｌ', 'm': 'ｍ', 'n': 'ｎ', 'o': 'ｏ', 'p': 'ｐ', 'q': 'ｑ', 'r': 'ｒ', 's': 'ｓ', 't': 'ｔ', 'u': 'ｕ', 'v': 'ｖ', 'w': 'ｗ', 'x': 'ｘ', 'y': 'ｙ', 'z': 'ｚ'},
    "small_caps": {'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ꜰ', 'g': 'ɢ', 'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ', 's': 's', 't': 'ᴛ', 'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ'},
    "blue": {'a': '🇦', 'b': '🇧', 'c': '🇨', 'd': '🇩', 'e': '🇪', 'f': '🇫', 'g': '🇬', 'h': '🇭', 'i': '🇮', 'j': '🇯', 'k': '🇰', 'l': '🇱', 'm': '🇲', 'n': '🇳', 'o': '🇴', 'p': '🇵', 'q': '🇶', 'r': '🇷', 's': '🇸', 't': '🇹', 'u': '🇺', 'v': '🇻', 'w': '🇼', 'x': '🇽', 'y': '🇾', 'z': '🇿'},
    "squares": {'a': '🄰', 'b': '🄱', 'c': '🄲', 'd': '🄳', 'e': '🄴', 'f': '🄵', 'g': '🄶', 'h': '🄷', 'i': '🄸', 'j': '🄹', 'k': '🄺', 'l': '🄻', 'm': '🄼', 'n': '🄽', 'o': '🄾', 'p': '🄿', 'q': '🅀', 'r': '🅁', 's': '🅂', 't': '🅃', 'u': '🅄', 'v': '🅅', 'w': '🅆', 'x': '🅇', 'y': '🅈', 'z': '🅉'},
    "black_squares": {'a': '🅰', 'b': '🅱', 'c': '🅲', 'd': '🅳', 'e': '🅴', 'f': '🅵', 'g': '🅶', 'h': '🅷', 'i': '🅸', 'j': '🅹', 'k': '🅺', 'l': '🅻', 'm': '🅼', 'n': '🅽', 'o': '🅾', 'p': '🅿', 'q': '🆀', 'r': '🆁', 's': '🆂', 't': '🆃', 'u': '🆄', 'v': '🆅', 'w': '🆆', 'x': '🆇', 'y': '🆈', 'z': '🆉'},
    "wavy": {'a': 'ᗩ', 'b': 'ᗷ', 'c': 'ᑕ', 'd': 'ᗪ', 'e': 'E', 'f': 'ᖴ', 'g': 'G', 'h': 'ᕼ', 'i': 'I', 'j': 'ᒍ', 'k': 'K', 'l': 'ᒪ', 'm': 'ᗰ', 'n': 'ᑎ', 'o': 'O', 'p': 'ᑭ', 'q': 'ᑫ', 'r': 'ᖇ', 's': 'ᔕ', 't': 'T', 'u': 'ᑌ', 'v': 'ᐯ', 'w': 'ᗯ', 'x': '᙭', 'y': 'Y', 'z': 'ᘔ'},
    "double_struck": {'a': '𝕒', 'b': '𝕓', 'c': '𝕔', 'd': '𝕕', 'e': '𝕖', 'f': '𝕗', 'g': '𝕘', 'h': '𝕙', 'i': '𝕚', 'j': '𝕛', 'k': '𝕜', 'l': '𝕝', 'm': '𝕞', 'n': '𝕟', 'o': '𝕠', 'p': '𝕡', 'q': '𝕢', 'r': '𝕣', 's': '𝕤', 't': '𝕥', 'u': '𝕦', 'v': '𝕧', 'w': '𝕨', 'x': '𝕩', 'y': '𝕪', 'z': '𝕫'},
    "parenthesized": {'a': '⒜', 'b': '⒝', 'c': '⒞', 'd': '⒟', 'e': '⒠', 'f': '⒡', 'g': '⒢', 'h': '⒣', 'i': '⒤', 'j': '⒥', 'k': '⒦', 'l': '⒧', 'm': '⒨', 'n': '⒩', 'o': '⒪', 'p': '⒫', 'q': '⒬', 'r': '⒭', 's': '⒮', 't': '⒯', 'u': '⒰', 'v': '⒱', 'w': '⒲', 'x': '⒳', 'y': '⒴', 'z': '⒵'},
    "circled_negative": {'a': '🅐', 'b': '🅑', 'c': '🅒', 'd': '🅓', 'e': '🅔', 'f': '🅕', 'g': '🅖', 'h': '🅗', 'i': '🅘', 'j': '🅙', 'k': '🅚', 'l': '🅛', 'm': '🅜', 'n': '🅝', 'o': '🅞', 'p': '🅟', 'q': '🅠', 'r': '🅡', 's': '🅢', 't': '🅣', 'u': '🅤', 'v': '🅥', 'w': '🅦', 'x': '🅧', 'y': '🅨', 'z': '🅩'},
    "fraktur_bold": {'a': '𝕬', 'b': '𝕭', 'c': '𝕮', 'd': '𝕯', 'e': '𝕰', 'f': '𝕱', 'g': '𝕲', 'h': '𝕳', 'i': '𝕴', 'j': '𝕵', 'k': '𝕶', 'l': '𝕷', 'm': '𝕸', 'n': '𝕹', 'o': '𝕺', 'p': '𝕻', 'q': '𝕼', 'r': '𝕽', 's': '𝕾', 't': '𝕿', 'u': '𝖀', 'v': '𝖁', 'w': '𝖂', 'x': '𝖃', 'y': '𝖄', 'z': '𝖅'},
    "hacker": {'a': '4', 'b': '8', 'c': '[', 'd': ')', 'e': '3', 'f': '|=', 'g': '6', 'h': '#', 'i': '1', 'j': ',_|', 'k': '|<', 'l': '1', 'm': '/\\/\\', 'n': '^/', 'o': '0', 'p': '|*', 'q': '(_,)', 'r': '|2', 's': '5', 't': '7', 'u': '(_)', 'v': '\\/', 'w': '\\/\\/', 'x': '><', 'y': 'j', 'z': '2'},
    "knight": {'a': 'Λ', 'b': 'ß', 'c': 'ㄈ', 'd': 'D', 'e': 'Σ', 'f': 'F', 'g': 'G', 'h': 'H', 'i': 'I', 'j': 'J', 'k': 'K', 'l': 'L', 'm': 'M', 'n': 'N', 'o': 'Ө', 'p': 'P', 'q': 'Q', 'r': 'Я', 's': 'S', 't': 'T', 'u': 'Ц', 'v': 'V', 'w': 'W', 'x': 'X', 'y': 'Y', 'z': 'Z'},
}

# --- Glitch / Crash Effects ---
def advanced_glitch(text):
    """Applies a more complex and varied glitch effect."""
    glitched_text = ""
    for char in text:
        if random.random() < 0.3:
            glitched_text += char
            num_diacritics = random.randint(3, 8)
            for _ in range(num_diacritics):
                glitched_text += chr(random.randint(0x0300, 0x036F))
            if random.random() < 0.5:
                glitched_text += random.choice("!@#$%^&*()_+-=[]{}|;:,.<>?/`~")
        else:
            glitched_text += char
    return glitched_text

def crash_effect(text):
    """Applies a heavy, multi-layered crash effect."""
    crashed_text = ""
    for char in text:
        crashed_text += char
        for _ in range(random.randint(3, 7)):
            crashed_text += chr(random.randint(0x0300, 0x036F))
        for _ in range(random.randint(2, 5)):
            crashed_text += chr(random.randint(0x0300, 0x036F))
        if random.random() < 0.4:
            crashed_text += random.choice("̷̴̸" * 10)
    return crashed_text

# ############################################################### #
# #################### HIGHLIGHTED CHANGE START ################### #
# ############################################################### #
def zalgo(text):
    """Applies a heavy zalgo/crash effect to text."""
    result = ""
    for char in text:
        result += char
        for _ in range(random.randint(5, 15)):
            result += chr(random.randint(0x0300, 0x036F))
    return result

def glitch_lines(text):
    """Applies a glitch effect with line symbols."""
    symbols = "̴̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷̸̷"
    result = ""
    for char in text:
        result += char + random.choice(symbols)
    return result
# ############################################################### #
# #################### HIGHLIGHTED CHANGE END ##################### #
# ############################################################### #

@Client.on_message(filters.command("font", prefix) & filters.me)
async def font_styler(client: Client, message: Message):
    """Generates text in multiple fancy fonts."""
    try:
        text_to_style = " ".join(message.command[1:])
        if not text_to_style:
            await message.edit("<b>Usage:</b> <code>.font [text]</code>")
            return

        response = f"<b>Original:</b> <code>{text_to_style}</code>\n\n"

        # --- Standard Fonts ---
        for name, font_map in FONTS.items():
            new_text = ""
            for char in text_to_style:
                lower_char = char.lower()
                if lower_char in font_map:
                    new_text += font_map[lower_char]
                else:
                    new_text += char
            response += f"<b>{name.replace('_', ' ').title()}:</b> <code>{new_text}</code>\n"

        # --- Special/Crash Fonts ---
        response += f"<b>Advanced Glitch:</b> <code>{advanced_glitch(text_to_style)}</code>\n"
        response += f"<b>Crash Effect:</b> <code>{crash_effect(text_to_style)}</code>\n"
        # #################### HIGHLIGHTED CHANGE ################### #
        response += f"<b>Zalgo:</b> <code>{zalgo(text_to_style)}</code>\n"
        response += f"<b>Glitch Lines:</b> <code>{glitch_lines(text_to_style)}</code>\n"
        response += f"<b>Strikethrough:</b> <code><del>{text_to_style}</del></code>\n"
        response += f"<b>Underline:</b> <code><u>{text_to_style}</u></code>\n"

        await message.edit(response, parse_mode=enums.ParseMode.HTML)

    except Exception as e:
        await message.edit(f"<b>An error occurred:</b> <code>{e}</code>")


# --- Add to modules_help ---
modules_help["fontstyler"] = {
    "font [text]": "Generates your text in 30+ different fancy and crash font styles."
}
