#
# A Pyrogram module to enhance images sent as photos in a chat.
# This module integrates the ImageEnhancer class for various photo editing tasks.
#
# Installation:
# pip install Pillow
# pip install opencv-python
# pip install numpy
#
# For blur_bg command, you need to download the Haar Cascade XML file for face detection.
# Download from: https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml
# And save it in the same directory as this script.
#

from pyrogram import Client, filters, enums
from pyrogram.types import Message
from utils.misc import modules_help, prefix
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np
import os
import io
import tempfile
import asyncio

# Utility function to install libraries if they are not already installed
def import_library(name: str):
    """
    Imports a library and provides a user-friendly error message if it's not found.
    Args:
        name (str): The name of the library to import.
    Returns:
        module: The imported module.
    Raises:
        ImportError: If the library cannot be imported.
    """
    try:
        if name == 'opencv-python':
            return __import__('cv2')
        else:
            return __import__(name)
    except ImportError:
        print(f"The library '{name}' is not installed. Please install it with 'pip install {name}' and try again.")
        raise

# Import necessary libraries using the utility function
try:
    np = import_library('numpy')
    cv2 = import_library('opencv-python')
except ImportError:
    # Exit gracefully if a critical library is missing
    print("Cannot proceed without required libraries.")
    raise

class ImageEnhancer:
    """
    A class to perform various image enhancement and editing operations.
    This version is adapted to work with images from memory (io.BytesIO).
    """
    def __init__(self, image_stream: io.BytesIO):
        """
        Initializes the ImageEnhancer with an image from an in-memory byte stream.
        Args:
            image_stream (io.BytesIO): The in-memory stream of the image data.
        """
        self.pil_image = self.load_image_from_stream(image_stream)
        self.np_image = None
        if self.pil_image:
            self.np_image = self._pil_to_cv2(self.pil_image)

    def load_image_from_stream(self, image_stream: io.BytesIO) -> Image.Image:
        """
        Loads an image from an in-memory byte stream using Pillow.
        Returns:
            Image.Image: The loaded PIL image object, or None if an error occurs.
        """
        try:
            image_stream.seek(0)
            return Image.open(image_stream).convert('RGB')
        except Exception as e:
            print(f"Error loading image from stream: {e}")
            return None

    def _pil_to_cv2(self, pil_image: Image.Image) -> np.ndarray:
        """
        Converts a Pillow image to an OpenCV/NumPy array.
        Args:
            pil_image (Image.Image): The input PIL image.
        Returns:
            np.ndarray: The image as a NumPy array (BGR format).
        """
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    def _cv2_to_pil(self, cv2_image: np.ndarray) -> Image.Image:
        """
        Converts an OpenCV/NumPy array back to a Pillow image.
        Args:
            cv2_image (np.ndarray): The input OpenCV image.
        Returns:
            Image.Image: The image as a PIL object.
        """
        return Image.fromarray(cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB))

    def enhance_image(self, denoise_strength=10, sharpen_amount=0.5, contrast_factor=1.2, brightness_factor=1.1, saturation_factor=1.2):
        """
        Applies a series of enhancements to the image in a single call.
        This is a high-level function for a "one-click" enhancement.
        Args:
            denoise_strength (int): Strength of the denoising filter.
            sharpen_amount (float): Amount of sharpening to apply.
            contrast_factor (float): Factor to increase contrast (e.g., 1.2 is 20% increase).
            brightness_factor (float): Factor to increase brightness.
            saturation_factor (float): Factor to increase color saturation.
        """
        if self.np_image is None:
            print("Image not loaded. Cannot enhance.")
            return

        print("Applying enhancements...")
        # 1. Denoising
        self.np_image = self.apply_denoising(self.np_image, strength=denoise_strength)

        # 2. Sharpening
        self.np_image = self.apply_sharpening(self.np_image, amount=sharpen_amount)

        # 3. Color and Tone adjustments
        self.pil_image = self._cv2_to_pil(self.np_image)
        self.pil_image = self.adjust_contrast_and_brightness(self.pil_image, contrast_factor, brightness_factor)
        self.pil_image = self.apply_saturation_boost(self.pil_image, saturation_factor)
        self.np_image = self._pil_to_cv2(self.pil_image)
        
        print("Enhancements complete.")

    def apply_denoising(self, image_np: np.ndarray, strength: int = 10) -> np.ndarray:
        """
        Applies a non-local means denoising filter to the image.
        This is particularly effective for removing Gaussian noise without blurring edges.
        Args:
            image_np (np.ndarray): The input image as a NumPy array.
            strength (int): The strength of the denoising filter.
        Returns:
            np.ndarray: The denoised image.
        """
        print("Applying denoising...")
        h_param = float(strength)
        h_color_param = float(strength/2)
        
        denoised_image = cv2.fastNlMeansDenoisingColored(
            image_np,
            None,
            h_param,
            h_color_param,
            templateWindowSize=7,
            searchWindowSize=21
        )
        return denoised_image

    def adjust_contrast_and_brightness(self, image_pil: Image.Image, contrast_factor: float, brightness_factor: float) -> Image.Image:
        """
        Adjusts the contrast and brightness of a PIL image.
        Args:
            image_pil (Image.Image): The input PIL image.
            contrast_factor (float): Factor to increase contrast.
            brightness_factor (float): Factor to increase brightness.
        Returns:
            Image.Image: The adjusted PIL image.
        """
        print("Adjusting contrast and brightness...")
        enhancer = ImageEnhance.Contrast(image_pil)
        image_pil = enhancer.enhance(contrast_factor)
        
        enhancer = ImageEnhance.Brightness(image_pil)
        image_pil = enhancer.enhance(brightness_factor)
        return image_pil

    def apply_sharpening(self, image_np: np.ndarray, amount: float = 0.5) -> np.ndarray:
        """
        Applies a sharpening filter to the image using a convolution kernel.
        Args:
            image_np (np.ndarray): The input image as a NumPy array.
            amount (float): The strength of the sharpening effect.
        Returns:
            np.ndarray: The sharpened image.
        """
        print("Applying sharpening...")
        sharpening_kernel = np.array([
            [-1, -1, -1],
            [-1, 9, -1],
            [-1, -1, -1]
        ]) * amount
        
        sharpened_image = cv2.filter2D(image_np, -1, sharpening_kernel)
        return sharpened_image

    def apply_saturation_boost(self, image_pil: Image.Image, factor: float = 1.2) -> Image.Image:
        """
        Boosts the color saturation of a PIL image.
        Args:
            image_pil (Image.Image): The input PIL image.
            factor (float): The saturation boost factor.
        Returns:
            Image.Image: The image with increased saturation.
        """
        print("Boosting saturation...")
        enhancer = ImageEnhance.Color(image_pil)
        return enhancer.enhance(factor)

    def apply_grayscale(self) -> None:
        """Converts the image to grayscale (black and white)."""
        if self.np_image is None:
            print("Image not loaded.")
            return

        print("Converting to grayscale...")
        gray_image_np = cv2.cvtColor(self.np_image, cv2.COLOR_BGR2GRAY)
        # Convert back to BGR for consistency with other functions
        self.np_image = cv2.cvtColor(gray_image_np, cv2.COLOR_GRAY2BGR)
        self.pil_image = self._cv2_to_pil(self.np_image)
        print("Grayscale conversion complete.")

    def apply_sepia(self) -> None:
        """Applies a sepia tone effect to the image."""
        if self.np_image is None:
            print("Image not loaded.")
            return

        print("Applying sepia tone...")
        sepia_kernel = np.array([
            [0.272, 0.534, 0.131],
            [0.349, 0.686, 0.168],
            [0.393, 0.769, 0.189]
        ])
        sepia_image = cv2.transform(self.np_image, sepia_kernel)
        sepia_image[np.where(sepia_image > 255)] = 255
        self.np_image = sepia_image
        self.pil_image = self._cv2_to_pil(self.np_image)
        print("Sepia tone complete.")

    def rotate_image(self, degrees: int) -> None:
        """Rotates the image by a specified number of degrees."""
        if self.pil_image is None:
            print("Image not loaded.")
            return

        print(f"Rotating image by {degrees} degrees...")
        self.pil_image = self.pil_image.rotate(degrees, expand=True)
        self.np_image = self._pil_to_cv2(self.pil_image)
        print("Rotation complete.")

    def invert_colors(self) -> None:
        """Inverts the colors of the image to create a negative effect."""
        if self.np_image is None:
            print("Image not loaded.")
            return

        print("Inverting colors...")
        self.np_image = cv2.bitwise_not(self.np_image)
        self.pil_image = self._cv2_to_pil(self.np_image)
        print("Inversion complete.")

    def resize_image(self, width: int, height: int) -> None:
        """Resizes the image to the specified width and height."""
        if self.pil_image is None:
            print("Image not loaded.")
            return

        print(f"Resizing image to {width}x{height}...")
        self.pil_image = self.pil_image.resize((width, height), Image.LANCZOS)
        self.np_image = self._pil_to_cv2(self.pil_image)
        print("Resizing complete.")

    def save_image_to_stream(self) -> io.BytesIO:
        """
        Saves the current state of the image to a new in-memory byte stream.
        Returns:
            io.BytesIO: The in-memory stream of the enhanced image.
        """
        if self.pil_image:
            try:
                img_stream = io.BytesIO()
                self.pil_image.save(img_stream, format='PNG')
                img_stream.seek(0)
                return img_stream
            except Exception as e:
                print(f"Error saving image to stream: {e}")
                return None
        else:
            print("No image to save.")
            return None

    # --- New Functions for User Request ---

    def apply_filter(self, filter_name: str) -> None:
        """Applies a named filter to the image."""
        if self.pil_image is None:
            print("Image not loaded.")
            return
        
        print(f"Applying filter: {filter_name}...")
        filter_name = filter_name.lower()
        
        if filter_name == "contour":
            self.pil_image = self.pil_image.filter(ImageFilter.CONTOUR)
        elif filter_name == "emboss":
            self.pil_image = self.pil_image.filter(ImageFilter.EMBOSS)
        elif filter_name == "smooth":
            self.pil_image = self.pil_image.filter(ImageFilter.SMOOTH)
        else:
            print(f"Unknown filter: {filter_name}")
            return
            
        self.np_image = self._pil_to_cv2(self.pil_image)
        print(f"Filter '{filter_name}' applied.")

    def blur_background(self) -> None:
        """Blurs the background of an image while keeping faces in focus."""
        if self.np_image is None:
            print("Image not loaded.")
            return

        print("Blurring background...")
        # Load the pre-trained Haar Cascade for face detection
        # Note: This file needs to be in the same directory as the script.
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        if face_cascade.empty():
            print("Haar Cascade XML file not found. Cannot blur background.")
            return

        # Convert to grayscale for face detection
        gray_image = cv2.cvtColor(self.np_image, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray_image, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        # Create a mask for the faces
        mask = np.zeros(self.np_image.shape[:2], dtype="uint8")
        for (x, y, w, h) in faces:
            cv2.rectangle(mask, (x, y), (x + w, y + h), 255, -1)

        # Apply a Gaussian blur to the whole image
        blurred_image = cv2.GaussianBlur(self.np_image, (21, 21), 0)

        # Combine the original image with the blurred image using the mask
        self.np_image = np.where(mask[..., None] == 255, self.np_image, blurred_image)
        self.pil_image = self._cv2_to_pil(self.np_image)
        print("Background blurred.")

    def colorize_image(self) -> None:
        """
        Applies a sepia-like color tint to the image.
        Note: Full-blown AI colorization requires a complex pre-trained model.
        """
        if self.np_image is None:
            print("Image not loaded.")
            return

        print("Colorizing image...")
        # Convert to grayscale first for a consistent effect
        gray = cv2.cvtColor(self.np_image, cv2.COLOR_BGR2GRAY)
        
        # Apply a simple color map for a colorized effect
        colorized_image = cv2.applyColorMap(gray, cv2.COLORMAP_JET)
        
        self.np_image = colorized_image
        self.pil_image = self._cv2_to_pil(self.np_image)
        print("Image colorized.")

    def face_swap(self, target_image_stream: io.BytesIO, source_image_stream: io.BytesIO) -> io.BytesIO:
        """
        A placeholder function to demonstrate face swap logic.
        This function loads both images but cannot perform a real face swap.
        It simply returns a copy of the target image with a message.
        """
        print("Attempting to perform face swap...")
        
        # Load the target image
        self.pil_image = self.load_image_from_stream(target_image_stream)
        if not self.pil_image:
            print("Failed to load target image.")
            return None
        
        # Load the source face image
        source_image = self.load_image_from_stream(source_image_stream)
        if not source_image:
            print("Failed to load source image.")
            return None
            
        print("Target and source images loaded. Note: Actual face swapping is a complex task.")
        
        # This is where a complex deep learning model would be used.
        # Since we don't have that, we return the original target image as a placeholder.
        # A real implementation would involve:
        # 1. Face detection on both images.
        # 2. Facial landmark detection.
        # 3. Warping the source face to fit the target face's shape.
        # 4. Seamless cloning to blend the new face into the target image.
        
        return self.save_image_to_stream()

    def restore_image(self) -> None:
        """
        Restores an image by applying denoising and sharpening filters.
        This mimics a basic restoration process for old or low-quality photos.
        """
        if self.np_image is None:
            print("Image not loaded.")
            return

        print("Restoring image...")
        # Apply denoising to remove noise
        self.np_image = self.apply_denoising(self.np_image, strength=20)
        # Apply sharpening to bring back detail
        self.np_image = self.apply_sharpening(self.np_image, amount=1.0)
        self.pil_image = self._cv2_to_pil(self.np_image)
        print("Image restoration complete.")

    def remove_text(self) -> None:
        """
        This is a placeholder for a complex function.
        Automated text removal requires a combination of OCR (to find text)
        and inpainting (to fill the area). This is a difficult task.
        We will simulate it by applying a heavy blur to a region of the image.
        """
        if self.np_image is None:
            print("Image not loaded.")
            return
        
        print("Simulating text removal by blurring a region...")
        # This is a basic simulation. Real text removal is much more complex.
        
        # Get image dimensions
        h, w, _ = self.np_image.shape
        # Define a random rectangular region to blur
        x1 = w // 4
        y1 = h // 4
        x2 = w * 3 // 4
        y2 = h * 3 // 4
        
        # Create a copy of the image to apply blur to a specific region
        temp_image = self.np_image.copy()
        
        # Apply a heavy blur to the selected region
        temp_image[y1:y2, x1:x2] = cv2.GaussianBlur(temp_image[y1:y2, x1:x2], (15, 15), 0)
        
        self.np_image = temp_image
        self.pil_image = self._cv2_to_pil(self.np_image)
        print("Text removal simulated.")


async def download_image_to_stream(client: Client, message: Message):
    """
    Downloads a replied-to photo to an in-memory stream using a temporary file
    as an intermediary to avoid path-related errors.
    """
    temp_file = None
    try:
        # Create a temporary file to save the image to
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        
        if message.photo:
            # For photos, use the file_id to download
            await client.download_media(message, file_name=temp_file.name)
        elif message.document:
            # For documents (attached images), use the file_id
            await client.download_media(message, file_name=temp_file.name)
        else:
            return None # Handle other media types if needed

        # Read the content from the temporary file into an in-memory stream
        with open(temp_file.name, "rb") as f:
            image_stream = io.BytesIO(f.read())
        return image_stream
    finally:
        # Ensure the temporary file is deleted
        if temp_file and os.path.exists(temp_file.name):
            os.remove(temp_file.name)

# --- Command Handlers ---

@Client.on_message(filters.command("enhance", prefix) & filters.me)
async def enhance_image_command(client: Client, message: Message):
    """
    Enhances a replied-to photo by applying denoising, sharpening, and color correction.
    Usage:
    /enhance [reply to a photo]
    """
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.edit("<code>Please reply to a photo to enhance it.</code>", parse_mode=enums.ParseMode.HTML)
        return

    try:
        await client.send_chat_action(message.chat.id, enums.ChatAction.UPLOAD_PHOTO)
        image_stream = await download_image_to_stream(client, message.reply_to_message)
        
        if image_stream:
            enhancer = ImageEnhancer(image_stream)
            await message.edit("<code>Enhancing photo... this may take a moment.</code>", parse_mode=enums.ParseMode.HTML)
            enhancer.enhance_image()
            enhanced_image_stream = enhancer.save_image_to_stream()
            
            if enhanced_image_stream:
                await client.send_photo(
                    chat_id=message.chat.id,
                    photo=enhanced_image_stream,
                    caption="Photo enhanced successfully!",
                    reply_to_message_id=message.reply_to_message.id
                )
            else:
                await message.edit("<code>Failed to save the enhanced photo.</code>", parse_mode=enums.ParseMode.HTML)
        else:
            await message.edit("<code>Failed to load the photo. Please try again.</code>", parse_mode=enums.ParseMode.HTML)
        
        await message.delete()

    except Exception as e:
        await message.edit(f"<code>An error occurred: {e}</code>", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("bw", prefix) & filters.me)
async def apply_bw_command(client: Client, message: Message):
    """Converts a replied-to photo to black and white."""
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.edit("<code>Please reply to a photo to convert to black and white.</code>", parse_mode=enums.ParseMode.HTML)
        return
    
    try:
        await client.send_chat_action(message.chat.id, enums.ChatAction.UPLOAD_PHOTO)
        image_stream = await download_image_to_stream(client, message.reply_to_message)
        
        if image_stream:
            enhancer = ImageEnhancer(image_stream)
            await message.edit("<code>Converting to black and white...</code>", parse_mode=enums.ParseMode.HTML)
            enhancer.apply_grayscale()
            enhanced_stream = enhancer.save_image_to_stream()
            if enhanced_stream:
                await client.send_photo(
                    chat_id=message.chat.id,
                    photo=enhanced_stream,
                    caption="Photo converted to black and white.",
                    reply_to_message_id=message.reply_to_message.id
                )
        await message.delete()
    except Exception as e:
        await message.edit(f"<code>An error occurred: {e}</code>", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("sepia", prefix) & filters.me)
async def apply_sepia_command(client: Client, message: Message):
    """Applies a sepia tone to a replied-to photo."""
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.edit("<code>Please reply to a photo to apply a sepia tone.</code>", parse_mode=enums.ParseMode.HTML)
        return
    
    try:
        await client.send_chat_action(message.chat.id, enums.ChatAction.UPLOAD_PHOTO)
        image_stream = await download_image_to_stream(client, message.reply_to_message)
        
        if image_stream:
            enhancer = ImageEnhancer(image_stream)
            await message.edit("<code>Applying sepia tone...</code>", parse_mode=enums.ParseMode.HTML)
            enhancer.apply_sepia()
            enhanced_stream = enhancer.save_image_to_stream()
            if enhanced_stream:
                await client.send_photo(
                    chat_id=message.chat.id,
                    photo=enhanced_stream,
                    caption="Sepia tone applied.",
                    reply_to_message_id=message.reply_to_message.id
                )
        await message.delete()
    except Exception as e:
        await message.edit(f"<code>An error occurred: {e}</code>", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("rotate", prefix) & filters.me)
async def rotate_image_command(client: Client, message: Message):
    """Rotates a replied-to photo by a specified number of degrees."""
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.edit("<code>Please reply to a photo to rotate.</code>", parse_mode=enums.ParseMode.HTML)
        return
    
    try:
        args = message.text.split(None, 1)
        if len(args) < 2 or not args[1].isdigit():
            await message.edit("<code>Please specify the degrees to rotate. E.g., /rotate 90</code>", parse_mode=enums.ParseMode.HTML)
            return

        degrees = int(args[1])

        await client.send_chat_action(message.chat.id, enums.ChatAction.UPLOAD_PHOTO)
        image_stream = await download_image_to_stream(client, message.reply_to_message)
        
        if image_stream:
            enhancer = ImageEnhancer(image_stream)
            await message.edit(f"<code>Rotating by {degrees} degrees...</code>", parse_mode=enums.ParseMode.HTML)
            enhancer.rotate_image(degrees)
            enhanced_stream = enhancer.save_image_to_stream()
            if enhanced_stream:
                await client.send_photo(
                    chat_id=message.chat.id,
                    photo=enhanced_stream,
                    caption=f"Photo rotated by {degrees} degrees.",
                    reply_to_message_id=message.reply_to_message.id
                )
        await message.delete()
    except Exception as e:
        await message.edit(f"<code>An error occurred: {e}</code>", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("invert", prefix) & filters.me)
async def invert_colors_command(client: Client, message: Message):
    """Inverts the colors of a replied-to photo."""
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.edit("<code>Please reply to a photo to invert colors.</code>", parse_mode=enums.ParseMode.HTML)
        return
    
    try:
        await client.send_chat_action(message.chat.id, enums.ChatAction.UPLOAD_PHOTO)
        image_stream = await download_image_to_stream(client, message.reply_to_message)
        
        if image_stream:
            enhancer = ImageEnhancer(image_stream)
            await message.edit("<code>Inverting colors...</code>", parse_mode=enums.ParseMode.HTML)
            enhancer.invert_colors()
            enhanced_stream = enhancer.save_image_to_stream()
            if enhanced_stream:
                await client.send_photo(
                    chat_id=message.chat.id,
                    photo=enhanced_stream,
                    caption="Colors inverted.",
                    reply_to_message_id=message.reply_to_message.id
                )
        await message.delete()
    except Exception as e:
        await message.edit(f"<code>An error occurred: {e}</code>", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("resize", prefix) & filters.me)
async def resize_image_command(client: Client, message: Message):
    """Resizes a replied-to photo."""
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.edit("<code>Please reply to a photo to resize it.</code>", parse_mode=enums.ParseMode.HTML)
        return
    
    try:
        args = message.text.split()
        if len(args) != 3 or not args[1].isdigit() or not args[2].isdigit():
            await message.edit("<code>Please specify the width and height. E.g., /resize 800 600</code>", parse_mode=enums.ParseMode.HTML)
            return

        width = int(args[1])
        height = int(args[2])

        await client.send_chat_action(message.chat.id, enums.ChatAction.UPLOAD_PHOTO)
        image_stream = await download_image_to_stream(client, message.reply_to_message)
        
        if image_stream:
            enhancer = ImageEnhancer(image_stream)
            await message.edit(f"<code>Resizing image to {width}x{height}...</code>", parse_mode=enums.ParseMode.HTML)
            enhancer.resize_image(width, height)
            enhanced_stream = enhancer.save_image_to_stream()
            if enhanced_stream:
                await client.send_photo(
                    chat_id=message.chat.id,
                    photo=enhanced_stream,
                    caption=f"Image resized to {width}x{height}.",
                    reply_to_message_id=message.reply_to_message.id
                )
        await message.delete()
    except Exception as e:
        await message.edit(f"<code>An error occurred: {e}</code>", parse_mode=enums.ParseMode.HTML)

# --- New Command Handlers from User Request ---

@Client.on_message(filters.command("filters", prefix) & filters.me)
async def apply_filter_command(client: Client, message: Message):
    """Applies a specific filter to a replied-to photo."""
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.edit("<code>Please reply to a photo and specify a filter (e.g., /filter emboss).</code>", parse_mode=enums.ParseMode.HTML)
        return

    try:
        args = message.text.split()
        if len(args) < 2:
            await message.edit("<code>Please specify a filter to apply. Available: emboss, contour, smooth.</code>", parse_mode=enums.ParseMode.HTML)
            return
        
        filter_name = args[1]
        
        await client.send_chat_action(message.chat.id, enums.ChatAction.UPLOAD_PHOTO)
        image_stream = await download_image_to_stream(client, message.reply_to_message)
        
        if image_stream:
            enhancer = ImageEnhancer(image_stream)
            await message.edit(f"<code>Applying {filter_name} filter...</code>", parse_mode=enums.ParseMode.HTML)
            enhancer.apply_filter(filter_name)
            enhanced_stream = enhancer.save_image_to_stream()
            if enhanced_stream:
                await client.send_photo(
                    chat_id=message.chat.id,
                    photo=enhanced_stream,
                    caption=f"Filter '{filter_name}' applied.",
                    reply_to_message_id=message.reply_to_message.id
                )
        await message.delete()
    except Exception as e:
        await message.edit(f"<code>An error occurred: {e}</code>", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("blur_bg", prefix) & filters.me)
async def blur_background_command(client: Client, message: Message):
    """Blurs the background of a photo while keeping faces in focus."""
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.edit("<code>Please reply to a photo with a face to blur the background.</code>", parse_mode=enums.ParseMode.HTML)
        return
    
    try:
        await client.send_chat_action(message.chat.id, enums.ChatAction.UPLOAD_PHOTO)
        image_stream = await download_image_to_stream(client, message.reply_to_message)
        
        if image_stream:
            enhancer = ImageEnhancer(image_stream)
            await message.edit("<code>Blurring background... This may take a moment.</code>", parse_mode=enums.ParseMode.HTML)
            enhancer.blur_background()
            enhanced_stream = enhancer.save_image_to_stream()
            if enhanced_stream:
                await client.send_photo(
                    chat_id=message.chat.id,
                    photo=enhanced_stream,
                    caption="Background blurred successfully.",
                    reply_to_message_id=message.reply_to_message.id
                )
        await message.delete()
    except Exception as e:
        await message.edit(f"<code>An error occurred: {e}</code>", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("colorize", prefix) & filters.me)
async def colorize_command(client: Client, message: Message):
    """Applies a color tint to a replied-to photo."""
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.edit("<code>Please reply to a photo to colorize it.</code>", parse_mode=enums.ParseMode.HTML)
        return
    
    try:
        await client.send_chat_action(message.chat.id, enums.ChatAction.UPLOAD_PHOTO)
        image_stream = await download_image_to_stream(client, message.reply_to_message)
        
        if image_stream:
            enhancer = ImageEnhancer(image_stream)
            await message.edit("<code>Colorizing image...</code>", parse_mode=enums.ParseMode.HTML)
            enhancer.colorize_image()
            enhanced_stream = enhancer.save_image_to_stream()
            if enhanced_stream:
                await client.send_photo(
                    chat_id=message.chat.id,
                    photo=enhanced_stream,
                    caption="Image colorized.",
                    reply_to_message_id=message.reply_to_message.id
                )
        await message.delete()
    except Exception as e:
        await message.edit(f"<code>An error occurred: {e}</code>", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("swap_face", prefix) & filters.me)
async def face_swap_command(client: Client, message: Message):
    """
    Demonstrates face swapping by requesting two images and showing a placeholder effect.
    Usage:
    - Reply to the photo you want to change (the target).
    - In your reply message, include the /swap_face command and attach the photo with the face you want to use (the source).
    """
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.edit("<code>Please reply to the target photo.</code>", parse_mode=enums.ParseMode.HTML)
        return
    if not message.photo and not (message.document and "image" in message.document.mime_type):
        await message.edit("<code>Please attach the source photo with the face you want to use.</code>", parse_mode=enums.ParseMode.HTML)
        return
    
    try:
        await client.send_chat_action(message.chat.id, enums.ChatAction.UPLOAD_PHOTO)
        
        # Download the target image (the one we replied to)
        target_stream = await download_image_to_stream(client, message.reply_to_message)
        
        # Download the source image (the one in the current message)
        source_stream = await download_image_to_stream(client, message)
        
        if not target_stream or not source_stream:
            await message.edit("<code>Failed to load both images. Please ensure both are valid photos or image documents.</code>", parse_mode=enums.ParseMode.HTML)
            return

        enhancer = ImageEnhancer(target_stream)
        await message.edit("<code>Attempting to swap faces...</code>", parse_mode=enums.ParseMode.HTML)
        
        enhanced_stream = enhancer.face_swap(target_stream, source_stream)
        
        if enhanced_stream:
            await client.send_photo(
                chat_id=message.chat.id,
                photo=enhanced_stream,
                caption="Face swap logic completed. Note: The effect is a placeholder as real face swapping requires complex AI models.",
                reply_to_message_id=message.reply_to_message.id
            )
        else:
            await message.edit("<code>Failed to process images for face swap.</code>", parse_mode=enums.ParseMode.HTML)
            
        await message.delete()
    except Exception as e:
        await message.edit(f"<code>An error occurred: {e}</code>", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("restore", prefix) & filters.me)
async def restore_image_command(client: Client, message: Message):
    """Restores a replied-to photo by applying denoising and sharpening."""
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.edit("<code>Please reply to a photo to restore it.</code>", parse_mode=enums.ParseMode.HTML)
        return

    try:
        await client.send_chat_action(message.chat.id, enums.ChatAction.UPLOAD_PHOTO)
        image_stream = await download_image_to_stream(client, message.reply_to_message)
        
        if image_stream:
            enhancer = ImageEnhancer(image_stream)
            await message.edit("<code>Restoring image...</code>", parse_mode=enums.ParseMode.HTML)
            enhancer.restore_image()
            enhanced_stream = enhancer.save_image_to_stream()
            if enhanced_stream:
                await client.send_photo(
                    chat_id=message.chat.id,
                    photo=enhanced_stream,
                    caption="Image restored using noise reduction and sharpening.",
                    reply_to_message_id=message.reply_to_message.id
                )
        await message.delete()
    except Exception as e:
        await message.edit(f"<code>An error occurred: {e}</code>", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("remove_text", prefix) & filters.me)
async def remove_text_command(client: Client, message: Message):
    """Simulates text removal by blurring a region of the image."""
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.edit("<code>Please reply to a photo to simulate text removal.</code>", parse_mode=enums.ParseMode.HTML)
        return
    
    try:
        await client.send_chat_action(message.chat.id, enums.ChatAction.UPLOAD_PHOTO)
        image_stream = await download_image_to_stream(client, message.reply_to_message)
        
        if image_stream:
            enhancer = ImageEnhancer(image_stream)
            await message.edit("<code>Simulating text removal...</code>", parse_mode=enums.ParseMode.HTML)
            enhancer.remove_text()
            enhanced_stream = enhancer.save_image_to_stream()
            if enhanced_stream:
                await client.send_photo(
                    chat_id=message.chat.id,
                    photo=enhanced_stream,
                    caption="Text removal simulated by blurring a region. Real text removal requires complex AI.",
                    reply_to_message_id=message.reply_to_message.id
                )
        await message.delete()
    except Exception as e:
        await message.edit(f"<code>An error occurred: {e}</code>", parse_mode=enums.ParseMode.HTML)


# Add instructions for your module
modules_help["image_enhancer"] = {
    "enhance": "Enhances a replied-to photo by applying denoising, sharpening, and color correction.",
    "bw": "Converts a replied-to photo to black and white.",
    "sepia": "Applies a sepia tone to a replied-to photo.",
    "rotate [degrees]": "Rotates a replied-to photo by a specified number of degrees (e.g., /rotate 90).",
    "invert": "Inverts the colors of a replied-to photo.",
    "resize [width] [height]": "Resizes a replied-to photo to the specified dimensions (e.g., /resize 800 600).",
    "filters [name]": "Applies a named filter (emboss, contour, smooth).",
    "blur_bg": "Blurs the background of a photo while keeping faces in focus.",
    "colorize": "Applies a color tint to a photo.",
    "swap_face": "<b>Reply to a photo with the command and attach a photo with the new face.</b> Note: This is a placeholder effect as real face swapping requires complex AI.",
    "restore": "Restores an image using denoising and sharpening.",
    "remove_text": "Simulates text removal by blurring a region of the image. Note: Real text removal requires complex AI.",
}
