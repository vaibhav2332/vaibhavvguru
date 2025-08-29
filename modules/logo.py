#
# A Pyrogram module to generate a PNG logo with different styles and templates.
# This module requires the 'Pillow' and 'requests' libraries.
#
# Installation:
# pip install Pillow
# pip install requests
#
# This version dynamically fetches fonts from Google Fonts, so no local font files are needed.
#

from pyrogram import Client, filters, enums
from pyrogram.types import Message
from utils.misc import modules_help, prefix
import os
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import random
from utils.scripts import import_library
import math
import numpy as np

# This utility function will automatically install 'requests' if it's not present.
requests = import_library("requests")

class LogoGenerator:
    """
    A class to encapsulate all the logic for generating a logo.
    This version dynamically fetches fonts from Google Fonts and supports different templates.
    """
    # A list of font families from Google Fonts.
    FONT_FAMILIES = [
        'Roboto',
        'Open Sans',
        'Lato',
        'Montserrat',
        'Poppins',
        'Oswald',
        'Playfair Display',
        'Merriweather',
        'Anton',
        'Lobster',
        'Pacifico',
        'Permanent Marker',
        'Bebas Neue',
        'Dancing Script',
        'Exo 2'
    ]

    # A list of color palettes as tuples (background_color, text_color).
    COLOR_PALETTES = [
        ("#1f2937", "#f3f4f6"),  # Dark Gray & White
        ("#3b82f6", "#ffffff"),  # Blue & White
        ("#ef4444", "#ffffff"),  # Red & White
        ("#10b981", "#ffffff"),  # Green & White
        ("#f59e0b", "#1f2937"),  # Amber & Dark Gray
        ("#ec4899", "#ffffff"),  # Pink & White
        ("#8b5cf6", "#ffffff"),  # Purple & White
        ("#60a5fa", "#0c4a6e"),  # Light Blue & Dark Blue
        ("#a3e635", "#1f2937"),  # Lime & Dark Gray
        ("#fca5a5", "#b91c1c"),  # Light Red & Dark Red
        ("#9ca3af", "#1f2937"),  # Gray & Dark Gray
        ("#c084fc", "#4c0519"),  # Light Purple & Dark Brown
        ("#fdba74", "#9a3412"),  # Light Orange & Dark Brown
        ("#4ade80", "#064e3b"),  # Light Green & Dark Green
        ("#a78bfa", "#312e81")   # Lavender & Indigo
    ]

    # A list of simple borders as tuples (top, right, bottom, left)
    BORDERS = [
        (0, 0, 0, 0),    # No border
        (5, 5, 5, 5),    # Small border
        (10, 10, 10, 10) # Medium border
    ]

    def __init__(self, text: str, template: str = 'default', style_id: int = None):
        """Initializes the LogoGenerator with text, template, and an optional style ID."""
        self.text = text
        self.template = template
        self.style_id = style_id

    def generate(self) -> BytesIO:
        """
        Generates the logo image based on the selected template and returns it as a BytesIO buffer.
        """
        # Use style_id as a seed for consistent results
        if self.style_id is not None:
            random.seed(self.style_id)
        else:
            random.seed(os.urandom(10))

        if self.template == 'classic':
            font = self._get_font(font_size=80)
            bg_color, text_color = random.choice(self.COLOR_PALETTES)
            border = random.choice(self.BORDERS)
            return self._generate_classic_logo(font, bg_color, text_color, border)
        elif self.template == 'frame':
            return self._generate_framed_logo()
        elif self.template == 'rounded_frame':
            return self._generate_rounded_frame_logo()
        elif self.template == 'stacked_text':
            return self._generate_stacked_text_logo()
        elif self.template == 'water_effect':
            return self._generate_water_effect_logo()
        elif self.template == 'glitch':
            return self._generate_glitch_logo()
        elif self.template == 'vintage_badge':
            return self._generate_vintage_badge_logo()
        else:
            # Default template is the classic text-only one
            font = self._get_font(font_size=80)
            bg_color, text_color = random.choice(self.COLOR_PALETTES)
            border = random.choice(self.BORDERS)
            return self._generate_classic_logo(font, bg_color, text_color, border)

    def _get_font(self, font_size=80, font_weight="regular"):
        """Attempts to load a font dynamically from Google Fonts, with specified weight."""
        font_family = random.choice(self.FONT_FAMILIES)
        font_url = f"https://fonts.googleapis.com/css2?family={font_family.replace(' ', '+')}:wght@400;700"
        
        try:
            response = requests.get(font_url)
            response.raise_for_status()
            
            # Extract the font file URL from the CSS
            font_file_url = response.text.split('url(')[1].split(')')[0]
            
            font_response = requests.get(font_file_url)
            font_response.raise_for_status()

            font_bytes = BytesIO(font_response.content)
            return ImageFont.truetype(font_bytes, size=font_size)

        except (requests.exceptions.RequestException, IndexError, IOError) as e:
            print(f"Warning: Failed to fetch font from Google Fonts. Error: {e}")
            try:
                return ImageFont.truetype("Arial.ttf", size=font_size)
            except IOError:
                raise IOError("Could not find any font files. Please check your internet connection or install a default font like Arial.")

    def _generate_classic_logo(self, font, bg_color, text_color, border):
        """Generates the classic text-only logo."""
        temp_img = Image.new("RGB", (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        text_bbox = temp_draw.textbbox((0, 0), self.text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        img_width = text_width + border[1] + border[3] + 40
        img_height = text_height + border[0] + border[2] + 40

        img = Image.new("RGB", (img_width, img_height), color=bg_color)
        draw = ImageDraw.Draw(img)

        text_position = (
            (img_width - text_width) / 2,
            (img_height - text_height) / 2
        )
        draw.text(text_position, self.text, fill=text_color, font=font)
        
        img_buffer = BytesIO()
        img.save(img_buffer, format="PNG")
        img_buffer.seek(0)
        return img_buffer

    def _generate_framed_logo(self):
        """Generates the framed logo with an icon and two text elements."""
        bg_color = "#2072f5"  # A solid blue
        text_color = "#ffffff" # A solid white
        frame_color = "#ffffff"

        # Define dimensions
        main_text = self.text.upper()
        sub_text = self.text.lower()
        frame_height = 120
        frame_width = 400
        icon_size = 80
        padding = 20

        # Create the main image canvas
        img_width = frame_width + 2 * padding
        img_height = frame_height + 2 * padding + 30
        img = Image.new("RGB", (img_width, img_height), color=bg_color)
        draw = ImageDraw.Draw(img)

        # Draw the main white frame
        frame_box = [padding, padding, padding + frame_width, padding + frame_height]
        draw.rectangle(frame_box, outline=frame_color, width=3)

        # Draw the square for the icon
        icon_box = [
            frame_box[0] + padding,
            frame_box[1] + padding,
            frame_box[0] + padding + icon_size,
            frame_box[1] + padding + icon_size
        ]
        draw.rectangle(icon_box, outline=frame_color, width=3)

        # Draw the spiral icon inside the icon box
        spiral_center_x = icon_box[0] + icon_size / 2
        spiral_center_y = icon_box[1] + icon_size / 2
        
        # Draw a proper spiral using math
        num_points = 200
        radius_increment = (icon_size / 2 - 5) / num_points # 5 is for margin
        angle_increment = 3.14159 * 2 * 3 # 3 rotations
        
        points = []
        for i in range(num_points + 1):
            angle = i * angle_increment / num_points
            radius = i * radius_increment
            x = spiral_center_x + radius * math.cos(angle)
            y = spiral_center_y + radius * math.sin(angle)
            points.append((x, y))
        
        draw.line(points, fill=text_color, width=2)
            
        # Draw the vertical divider line
        divider_x = icon_box[2] + padding
        draw.line(
            (divider_x, frame_box[1], divider_x, frame_box[3]),
            fill=frame_color,
            width=3
        )

        # Draw the main text
        main_font_size = 50
        main_font = self._get_font(font_size=main_font_size, font_weight="bold")
        main_text_position = (
            divider_x + padding,
            frame_box[1] + (frame_height - main_font_size) / 2
        )
        draw.text(main_text_position, main_text, fill=text_color, font=main_font)

        # Draw the sub-text
        sub_font_size = 20
        sub_font = self._get_font(font_size=sub_font_size)
        sub_text_position = (
            img_width / 2 - sub_font.getlength(sub_text) / 2,
            frame_box[3] + 10
        )
        draw.text(sub_text_position, sub_text, fill=text_color, font=sub_font)
        
        img_buffer = BytesIO()
        img.save(img_buffer, format="PNG")
        img_buffer.seek(0)
        return img_buffer

    def _generate_rounded_frame_logo(self):
        """Generates a modern logo with a rounded rectangular frame and a simple abstract icon."""
        bg_color, text_color = random.choice(self.COLOR_PALETTES)
        frame_color = text_color
        
        img_width = 500
        img_height = 250
        img = Image.new("RGB", (img_width, img_height), color=bg_color)
        draw = ImageDraw.Draw(img)

        # Draw the main rounded frame
        frame_radius = 20
        frame_box = [40, 40, img_width - 40, img_height - 40]
        self._draw_rounded_rectangle(draw, frame_box, frame_radius, frame_color, width=3)

        # Draw the abstract icon (e.g., a simple curve)
        icon_offset_x = 70
        icon_offset_y = 70
        draw.arc(
            (icon_offset_x, icon_offset_y, icon_offset_x + 60, icon_offset_y + 60),
            start=45, end=270, fill=frame_color, width=4
        )
        
        # Draw the main text next to the icon
        main_font = self._get_font(font_size=60)
        text_bbox = draw.textbbox((0, 0), self.text, font=main_font)
        text_width = text_bbox[2] - text_bbox[0]
        
        text_x = icon_offset_x + 80
        text_y = frame_box[1] + (frame_box[3] - frame_box[1] - main_font.size) / 2
        draw.text((text_x, text_y), self.text, fill=text_color, font=main_font)

        img_buffer = BytesIO()
        img.save(img_buffer, format="PNG")
        img_buffer.seek(0)
        return img_buffer

    def _generate_stacked_text_logo(self):
        """Generates a logo with stacked text and a horizontal divider line."""
        bg_color, text_color = random.choice(self.COLOR_PALETTES)
        divider_color = text_color
        
        # Define text elements
        upper_text = self.text.upper()
        lower_text = self.text.lower()
        
        # Get fonts
        upper_font = self._get_font(font_size=60)
        lower_font = self._get_font(font_size=30)
        
        # Calculate dimensions based on text
        temp_img = Image.new("RGB", (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        upper_bbox = temp_draw.textbbox((0, 0), upper_text, font=upper_font)
        lower_bbox = temp_draw.textbbox((0, 0), lower_text, font=lower_font)
        
        img_width = max(upper_bbox[2] - upper_bbox[0], lower_bbox[2] - lower_bbox[0]) + 100
        img_height = (upper_bbox[3] - upper_bbox[1]) + (lower_bbox[3] - lower_bbox[1]) + 100
        
        img = Image.new("RGB", (img_width, img_height), color=bg_color)
        draw = ImageDraw.Draw(img)
        
        # Draw upper text
        upper_text_x = (img_width - (upper_bbox[2] - upper_bbox[0])) / 2
        upper_text_y = (img_height / 2 - (upper_bbox[3] - upper_bbox[1])) / 2
        draw.text((upper_text_x, upper_text_y), upper_text, fill=text_color, font=upper_font)

        # Draw horizontal divider
        line_start = (img_width * 0.25, img_height / 2)
        line_end = (img_width * 0.75, img_height / 2)
        draw.line([line_start, line_end], fill=divider_color, width=3)
        
        # Draw lower text
        lower_text_x = (img_width - (lower_bbox[2] - lower_bbox[0])) / 2
        lower_text_y = (img_height / 2 + (lower_bbox[3] - lower_bbox[1])) / 2
        draw.text((lower_text_x, lower_text_y), lower_text, fill=text_color, font=lower_font)
        
        img_buffer = BytesIO()
        img.save(img_buffer, format="PNG")
        img_buffer.seek(0)
        return img_buffer

    def _draw_rounded_rectangle(self, draw, xy, corner_radius, fill=None, outline=None, width=1):
        """
        Draws a rounded rectangle using the draw object.
        Pillow does not have a native rounded rectangle function.
        """
        x1, y1, x2, y2 = xy
        draw.rectangle([x1 + corner_radius, y1, x2 - corner_radius, y2], fill=fill, outline=outline, width=width)
        draw.rectangle([x1, y1 + corner_radius, x2, y2 - corner_radius], fill=fill, outline=outline, width=width)
        draw.pieslice([x1, y1, x1 + 2 * corner_radius, y1 + 2 * corner_radius], 180, 270, fill=fill, outline=outline, width=width)
        draw.pieslice([x2 - 2 * corner_radius, y1, x2, y1 + 2 * corner_radius], 270, 360, fill=fill, outline=outline, width=width)
        draw.pieslice([x1, y2 - 2 * corner_radius, x1 + 2 * corner_radius, y2], 90, 180, fill=fill, outline=outline, width=width)
        draw.pieslice([x2 - 2 * corner_radius, y2 - 2 * corner_radius, x2, y2], 0, 90, fill=fill, outline=outline, width=width)

    def _generate_water_effect_logo(self):
        """Generates a logo with a water ripple effect on the text."""
        img_width, img_height = 800, 400
        bg_color = "#3498db" # A blue color for water
        
        # Create a base image for the text
        text_img = Image.new("RGBA", (img_width, img_height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(text_img)
        font = self._get_font(font_size=100)
        
        # Get text size for centering
        text_bbox = draw.textbbox((0, 0), self.text, font=font)
        text_x = (img_width - (text_bbox[2] - text_bbox[0])) / 2
        text_y = (img_height - (text_bbox[3] - text_bbox[1])) / 2
        
        # Draw the text on the base image
        draw.text((text_x, text_y), self.text, fill="white", font=font)
        
        # Create a water ripple effect using a displacement map
        ripple_img = Image.new("L", (img_width, img_height))
        draw_ripple = ImageDraw.Draw(ripple_img)
        
        # Simulate ripples by drawing concentric circles
        for i in range(10, 100, 10):
            draw_ripple.ellipse([img_width/2-i, img_height/2-i, img_width/2+i, img_height/2+i], fill=str(i*2))
        
        # Create the displacement map
        pix = np.array(ripple_img)
        x_map, y_map = np.meshgrid(np.arange(img_width), np.arange(img_height))
        
        # Apply the ripple effect
        distort_amount = 20
        new_x = x_map + (pix - 128) * distort_amount / 255
        new_y = y_map + (pix - 128) * distort_amount / 255
        
        distorted_img = text_img.transform(
            (img_width, img_height),
            Image.AFFINE,
            (1, 0, 0, 0, 1, 0),
            resample=Image.BICUBIC,
            data=(new_x.flatten(), new_y.flatten())
        )
        
        final_img = Image.new("RGB", (img_width, img_height), bg_color)
        final_img.paste(distorted_img, (0, 0), distorted_img)
        
        # Add a reflection for more realism
        reflection = final_img.crop((0, img_height/2, img_width, img_height))
        reflection = reflection.transpose(Image.FLIP_TOP_BOTTOM)
        final_img.paste(reflection, (0, int(img_height/2)))
        
        img_buffer = BytesIO()
        final_img.save(img_buffer, format="PNG")
        img_buffer.seek(0)
        return img_buffer

    def _generate_glitch_logo(self):
        """Generates a logo with a cool glitch effect."""
        img_width, img_height = 600, 300
        bg_color, text_color = random.choice(self.COLOR_PALETTES)
        
        img = Image.new("RGB", (img_width, img_height), color=bg_color)
        draw = ImageDraw.Draw(img)
        font = self._get_font(font_size=70)
        
        # Draw the text multiple times with slight offsets
        glitch_offsets = [-5, -2, 0, 2, 5]
        colors = ["#ff0000", "#00ff00", "#0000ff"]
        
        for offset in glitch_offsets:
            color = random.choice(colors)
            draw.text((30 + offset, 100 + offset), self.text.upper(), fill=color, font=font)
        
        # Randomly shift and cut parts of the image
        pix = img.load()
        for y in range(img_height):
            if random.random() < 0.1: # 10% chance to glitch a row
                shift = random.randint(-50, 50)
                row_slice = list(pix[x, y] for x in range(img_width))
                shifted_row = row_slice[shift:] + row_slice[:shift]
                for x in range(img_width):
                    pix[x, y] = shifted_row[x]
        
        img_buffer = BytesIO()
        img.save(img_buffer, format="PNG")
        img_buffer.seek(0)
        return img_buffer
    
    def _generate_vintage_badge_logo(self):
        """Generates a vintage-style badge logo with a circular frame."""
        img_width, img_height = 500, 500
        bg_color = "#f4f3f2" # Off-white background
        frame_color = "#3e2723" # Dark brown for a rustic look
        text_color = "#3e2723"
        
        img = Image.new("RGB", (img_width, img_height), color=bg_color)
        draw = ImageDraw.Draw(img)
        
        # Draw the outer circle
        draw.ellipse([50, 50, img_width - 50, img_height - 50], outline=frame_color, width=5)
        
        # Draw the text along the curve (simplified)
        main_font = self._get_font(font_size=60)
        text_bbox = draw.textbbox((0, 0), self.text.upper(), font=main_font)
        text_width = text_bbox[2] - text_bbox[0]
        
        text_x = (img_width - text_width) / 2
        text_y = (img_height - (text_bbox[3] - text_bbox[1])) / 2
        draw.text((text_x, text_y), self.text.upper(), fill=text_color, font=main_font)
        
        # Add a small inner circle or decorative element
        draw.ellipse([200, 200, 300, 300], outline=frame_color, width=3)
        
        # Add a simple star inside the inner circle
        draw.line([250, 220, 260, 280], fill=frame_color, width=2)
        draw.line([240, 250, 270, 250], fill=frame_color, width=2)

        img_buffer = BytesIO()
        img.save(img_buffer, format="PNG")
        img_buffer.seek(0)
        return img_buffer


@Client.on_message(filters.command("logo", prefix) & filters.me)
async def generate_logo_command(client: Client, message: Message):
    """
    Generates a custom logo based on the provided text and template.
    Usage:
    /logo <text> [style_id]           - Generates a classic logo.
    /logo <text> frame [style_id]     - Generates a framed logo with an icon.
    /logo <text> rounded_frame [style_id] - Generates a modern logo with a rounded frame.
    /logo <text> stacked_text [style_id]  - Generates a typographic logo with stacked text.
    /logo <text> water_effect [style_id]  - Generates a logo with a water effect.
    /logo <text> glitch [style_id]    - Generates a glitch-style logo.
    /logo <text> vintage_badge [style_id] - Generates a vintage badge-style logo.
    """
    try:
        args = message.text.split(None, 3)
        if len(args) < 2:
            await message.edit("<code>Please provide text for the logo.</code>", parse_mode=enums.ParseMode.HTML)
            return

        logo_text = args[1]
        template = 'classic'
        style_id = None

        if len(args) > 2:
            template_arg = args[2].lower()
            if template_arg == 'frame':
                template = 'frame'
            elif template_arg == 'rounded_frame':
                template = 'rounded_frame'
            elif template_arg == 'stacked_text':
                template = 'stacked_text'
            elif template_arg == 'water_effect':
                template = 'water_effect'
            elif template_arg == 'glitch':
                template = 'glitch'
            elif template_arg == 'vintage_badge':
                template = 'vintage_badge'
            elif args[2].isdigit():
                style_id = int(args[2])

            if len(args) > 3 and args[3].isdigit():
                style_id = int(args[3])

        # Use the new LogoGenerator class
        generator = LogoGenerator(text=logo_text, template=template, style_id=style_id)
        img_buffer = generator.generate()

        # Send the generated photo
        await client.send_photo(
            chat_id=message.chat.id,
            photo=img_buffer,
            caption=f"Here is your logo for '{logo_text}'.",
            parse_mode=enums.ParseMode.HTML
        )
        await message.delete()

    except Exception as e:
        await message.edit(f"<code>An error occurred: {e}</code>", parse_mode=enums.ParseMode.HTML)
        
# Add instructions for your module
modules_help["logo_generator"] = {
    "logo [text]": "Generates a simple, classic text-based logo.",
    "logo [text] frame": "Generates a logo with an icon and text, like the example provided.",
    "logo [text] rounded_frame": "Generates a modern logo with a rounded frame and a simple icon.",
    "logo [text] stacked_text": "Generates a typographic logo with stacked text and a divider.",
    "logo [text] water_effect": "Generates a logo with a water ripple effect.",
    "logo [text] glitch": "Generates a modern glitch-style logo.",
    "logo [text] vintage_badge": "Generates a vintage badge-style logo.",
    "logo [text] [style_id]": "Optionally, use a style ID (a number) to get a specific style.",
}
