#!/usr/bin/env python3
"""
Screenshot utilities for Trivia Speed Assistant.

This module contains functions for taking screenshots and processing them.
"""

import os
import time
import mss
import mss.tools
from PIL import Image
from datetime import datetime
import concurrent.futures
from pathlib import Path
from typing import Optional, Tuple, Union
import logging
import io
import base64
import functools

# Configure logging
logger = logging.getLogger('trivia-speed')

# Create screenshots directory path once
SCRIPT_DIR = Path(__file__).parent.absolute()
SCREENSHOTS_DIR = SCRIPT_DIR / ".." / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

# Thread pool for CPU-bound tasks
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

def take_right_third_screenshot(
    output_path: Optional[str] = None, 
    quality: int = 60, 
    resize_factor: float = 0.5, 
    debug: bool = False, 
    save_copy: Optional[Union[bool, str]] = None
) -> Tuple[str, Image.Image]:
    """
    Take a screenshot of the right third of the screen.
    
    Args:
        output_path: Path to save the screenshot. If None, saves to 'screenshots' folder with timestamp.
        quality: JPEG quality (1-100). Default is 60.
        resize_factor: Factor to resize the image. Default is 0.5 (50%).
        debug: Whether to print debug information.
        save_copy: Path to save an unmodified copy of the screenshot.
    
    Returns:
        Tuple[str, Image.Image]: Path to the saved screenshot and the PIL Image object.
    """
    start_time = time.time()
    
    # Get screen dimensions
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # Primary monitor
        screen_width = monitor["width"]
        screen_height = monitor["height"]
        
        # Calculate the right third of the screen
        right_third_width = screen_width * .29
        right_third_x = screen_width - right_third_width

        left_padding = 30
        right_padding = 30
        top_padding = 430
        bottom_padding = 80
        
        # Define the region to capture
        region = {
            "top": 0 + top_padding,
            "left": right_third_x + left_padding,
            "width": right_third_width - left_padding - right_padding,
            "height": screen_height - top_padding - bottom_padding
        }
        
        if debug:
            logger.info(f"Taking screenshot of region: {region}")
        
        # Capture the screenshot
        screenshot = sct.grab(region)
        
        # Convert to PIL Image
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        
        # Save an unmodified copy if requested
        if save_copy:
            if save_copy is True:  # If no path provided, use default
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                original_path = str(SCREENSHOTS_DIR / f"original_{timestamp}.png")
            else:
                original_path = save_copy
                
            img.save(original_path)
            if debug:
                logger.info(f"Saved original screenshot to {original_path}")
    
    # Resize the image if requested
    if resize_factor != 1.0:
        new_width = int(img.width * resize_factor)
        new_height = int(img.height * resize_factor)
        img = img.resize((new_width, new_height), Image.LANCZOS)
        if debug:
            logger.info(f"Resized image to {new_width}x{new_height}")
    
    # Save the processed image
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = str(SCREENSHOTS_DIR / f"screenshot_{timestamp}.jpg")
    
    # Save as JPEG with specified quality
    img.save(output_path, "JPEG", quality=quality)
    
    if debug:
        elapsed = time.time() - start_time
        logger.info(f"Screenshot taken and saved to {output_path} in {elapsed:.3f} seconds")
        logger.info(f"Image dimensions: {img.width}x{img.height}, Quality: {quality}")
    
    return output_path, img

@functools.lru_cache(maxsize=8)
def encode_image_to_base64(image_bytes):
    """
    Encode image bytes to base64.
    
    Args:
        image_bytes: Image bytes to encode
        
    Returns:
        str: Base64 encoded image
    """
    return base64.b64encode(image_bytes).decode('utf-8')

def prepare_image_for_api(image):
    """
    Prepare an image for the OpenAI API by converting it to base64.
    
    Args:
        image (PIL.Image): The image to prepare
        
    Returns:
        str: Base64 encoded image
    """
    # Convert to JPEG in memory
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=85)
    buffer.seek(0)
    
    # Encode to base64
    return encode_image_to_base64(buffer.getvalue())

def shutdown():
    """Shutdown the thread pool"""
    thread_pool.shutdown(wait=False) 