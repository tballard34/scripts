#!/usr/bin/env python3
"""
Trivia Speed Assistant

This script takes a screenshot of the right third of the screen,
sends it to GPT-4o and/or Mistral AI for analysis, and returns the answer to the trivia question.
It can also use Gemini 2.0 for OCR to extract text from the image.
"""

import os
import argparse
from datetime import datetime
import asyncio
from dotenv import load_dotenv
from pathlib import Path
import logging
from PIL import Image

# Import screenshot module
from screenshot import (
    take_right_third_screenshot,
    shutdown as screenshot_shutdown
)

# Import chatgpt module
from chatgpt import (
    analyze_trivia_with_gpt4o,
    TriviaAnalysis as GPTTriviaAnalysis,
    set_api_timeout as set_gpt_api_timeout,
    shutdown as chatgpt_shutdown
)

# Import mistral module
from mistral import (
    analyze_trivia_with_mistral,
    TriviaAnalysis as MistralTriviaAnalysis,
    set_api_timeout as set_mistral_api_timeout,
    shutdown as mistral_shutdown
)

# Import Gemini OCR module
from ocr_and_gemini import (
    extract_text_with_gemini,
    OCRResult,
    set_api_timeout as set_gemini_api_timeout,
    shutdown as gemini_shutdown
)

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Default to WARNING to suppress INFO logs
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('trivia-speed')

# Load environment variables from .env file
load_dotenv()

# Default API timeout
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "15"))  # Timeout for API calls in seconds

# Create screenshots directory path once
SCRIPT_DIR = Path(__file__).parent.absolute()
SCREENSHOTS_DIR = SCRIPT_DIR / ".." / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

async def process_with_gpt(image, args):
    """Process the image with GPT-4o"""
    try:
        # Use structured output with Pydantic model
        result = await analyze_trivia_with_gpt4o(image, args.debug)
        
        if args.debug:
            logger.info("\n=== GPT-4o Analysis ===")
            logger.info(f"Rationale: {result.rationale}")
            logger.info(f"Answer: {result.answer}")
            logger.info("==========================\n")
        else:
            # In non-debug mode, only print the answer
            print(f"{result.answer}")
            
    except TimeoutError as e:
        logger.error(f"GPT-4o API request timed out: {e}")
        if args.debug:
            print(f"Error: GPT-4o API request timed out after {API_TIMEOUT} seconds")
        else:
            print("Error: GPT-4o API request timed out")
    except Exception as e:
        if args.debug:
            logger.error(f"Error analyzing trivia with GPT-4o: {e}")
            print(f"Error analyzing trivia with GPT-4o: {e}")
        else:
            print("Error: Failed to analyze trivia with GPT-4o")

async def process_with_mistral(image, args):
    """Process the image with Mistral AI"""
    try:
        # Always use structured output with Pydantic model
        result = await analyze_trivia_with_mistral(image, args.debug)
        
        if args.debug:
            logger.info("\n=== Mistral Analysis ===")
            logger.info(f"Rationale: {result.rationale}")
            logger.info(f"Answer: {result.answer}")
            logger.info("==========================\n")
        else:
            # In non-debug mode, only print the answer
            print(f"\033[38;5;208m{result.answer}\033[0m")
            
    except TimeoutError as e:
        logger.error(f"Mistral API request timed out: {e}")
        if args.debug:
            print(f"Error: Mistral API request timed out after {API_TIMEOUT} seconds")
        else:
            print("Error: Mistral API request timed out")
    except Exception as e:
        if args.debug:
            logger.error(f"Error analyzing trivia with Mistral: {e}")
            print(f"Error analyzing trivia with Mistral: {e}")
        else:
            print("Error: Failed to analyze trivia with Mistral")

async def process_with_gemini_ocr(image, args):
    """Process the image with Gemini for OCR and answer"""
    try:
        # Use structured output with Pydantic model
        result = await extract_text_with_gemini(image, args.debug)
        
        if args.debug:
            logger.info("\n=== Gemini OCR Analysis ===")
            logger.info(f"Question: {result.question}")
            logger.info(f"Options: {result.options}")
            logger.info(f"Rationale: {result.rationale}")
            logger.info(f"Answer: {result.answer}")
            logger.info("==========================\n")
        else:
            # In non-debug mode, print the extracted text and answer in a formatted way
            print(f"\033[38;5;34m=== Gemini Analysis ===\033[0m")
            print(f"\033[38;5;34mQuestion: {result.question}\033[0m")
            if result.options:
                print(f"\033[38;5;34mOptions:\033[0m")
                for i, option in enumerate(result.options):
                    print(f"\033[38;5;34m  {chr(65+i)}. {option}\033[0m")
            print(f"\033[38;5;34mRationale: {result.rationale}\033[0m")
            print(f"\033[38;5;34mAnswer: {result.answer}\033[0m")
            print(f"\033[38;5;34m====================\033[0m")
        
    except TimeoutError as e:
        logger.error(f"Gemini OCR API request timed out: {e}")
        if args.debug:
            print(f"Error: Gemini OCR API request timed out after {API_TIMEOUT} seconds")
        else:
            print("Error: Gemini OCR API request timed out")
    except Exception as e:
        if args.debug:
            logger.error(f"Error extracting text with Gemini OCR: {e}")
            print(f"Error extracting text with Gemini OCR: {e}")
        else:
            print("Error: Failed to extract text with Gemini OCR")

async def async_main(args):
    """Async version of main function to handle async API calls"""
    try:
        # Check if an image path was provided
        if hasattr(args, 'image_path') and args.image_path:
            # Load the image from the provided path
            try:
                image = Image.open(args.image_path)
                output_path = args.image_path
                if args.debug:
                    logger.info(f"Using provided image: {args.image_path}")
            except Exception as e:
                logger.error(f"Error loading image from path {args.image_path}: {e}")
                raise ValueError(f"Failed to load image from path: {e}")
        else:
            # Take screenshot
            output_path, image = take_right_third_screenshot(
                args.output, 
                args.quality, 
                args.resize, 
                args.debug,
                args.save_original
            )
        
        # Create tasks for GPT, Mistral, and Gemini OCR analysis if not disabled
        tasks = []
        
        # Run Gemini OCR first if enabled
        if not args.no_gemini_ocr:
            await process_with_gemini_ocr(image, args)
        elif args.debug:
            logger.info("Skipping Gemini OCR analysis as requested.")
        
        if not args.no_gpt:
            tasks.append(process_with_gpt(image, args))
        elif args.debug:
            logger.info("Skipping GPT-4o analysis as requested.")
            
        if not args.no_mistral:
            tasks.append(process_with_mistral(image, args))
        elif args.debug:
            logger.info("Skipping Mistral analysis as requested.")
            
        # If both models are disabled, just return
        if not tasks:
            if args.debug and args.no_gemini_ocr:
                logger.info("All analysis options are disabled. No analysis performed.")
            return
            
        # Run all tasks concurrently
        await asyncio.gather(*tasks)
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        if args.debug:
            print(f"Error: {e}")
        else:
            print("An error occurred. Run with --debug for more information.")

def main():
    # Declare global variable at the beginning of the function
    global API_TIMEOUT
    
    parser = argparse.ArgumentParser(description="Take a screenshot of the right third of the screen and analyze trivia questions")
    parser.add_argument("-o", "--output", help="Output file path (default: screenshots folder with timestamp)")
    parser.add_argument("-q", "--quality", type=int, default=60, 
                        help="JPEG quality (1-100, default: 60)")
    parser.add_argument("-r", "--resize", type=float, default=0.5,
                        help="Resize factor for the image (default: 0.5 = 50%%)")
    parser.add_argument("--save-original", nargs='?', const=True, default=None,
                        help="Save an unmodified copy of the screenshot. If no path is provided, saves to screenshots folder with timestamp.")
    parser.add_argument("--no-gpt", action="store_true", 
                        help="Skip sending to GPT-4o (just take screenshot)")
    parser.add_argument("--no-mistral", action="store_true", 
                        help="Skip sending to Mistral AI (just take screenshot)")
    parser.add_argument("--no-gemini-ocr", action="store_true", 
                        help="Skip sending to Gemini 2.0 for OCR (skip text extraction)")
    parser.add_argument("--debug", action="store_true",
                        help="Print debug information")
    parser.add_argument("--timeout", type=int, default=API_TIMEOUT,
                        help="Timeout for API calls in seconds (default: {})".format(API_TIMEOUT))
    parser.add_argument("image_path", nargs="?", help="Path to an image file to analyze instead of taking a screenshot")
    args = parser.parse_args()
    
    # Update timeout if specified
    API_TIMEOUT = args.timeout
    # Update timeout in modules
    set_gpt_api_timeout(API_TIMEOUT)
    set_mistral_api_timeout(API_TIMEOUT)
    set_gemini_api_timeout(API_TIMEOUT)
    
    # Configure logging level based on debug flag
    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        # Set to ERROR level to suppress INFO logs when not in debug mode
        logger.setLevel(logging.ERROR)
    
    try:
        # Run the async main function
        asyncio.run(async_main(args))
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        print(f"Error: {e}")
    finally:
        # Clean up thread pools
        chatgpt_shutdown()
        mistral_shutdown()
        gemini_shutdown()
        screenshot_shutdown()

if __name__ == "__main__":
    main()
