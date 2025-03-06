#!/usr/bin/env python3
"""
Trivia Speed Assistant

This script takes a screenshot of the right third of the screen,
sends it to GPT-4o for analysis, and returns the answer to the trivia question.
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
    analyze_trivia_raw,
    TriviaAnalysis,
    set_api_timeout,
    shutdown as chatgpt_shutdown
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
        
        # Skip GPT analysis if requested
        if args.no_gpt:
            if args.debug:
                logger.info("Skipping GPT-4o analysis as requested.")
            return
        
        # Send to GPT-4o for analysis
        try:
            if args.raw:
                # Use raw output without JSON structure
                result = await analyze_trivia_raw(image, args.debug)
                if args.debug:
                    logger.info("\n=== GPT-4o Raw Analysis ===")
                    logger.info(result)
                    logger.info("==========================\n")
                else:
                    print(result)
            else:
                # Use structured output with Pydantic model
                result = await analyze_trivia_with_gpt4o(image, args.debug)
                
                if args.debug:
                    logger.info("\n=== GPT-4o Analysis ===")
                    logger.info(f"Rationale: {result.rationale}")
                    logger.info(f"Answer: {result.answer}")
                    logger.info("==========================\n")
                else:
                    # In non-debug mode, only print the answer
                    print(result.answer)
                
        except TimeoutError as e:
            logger.error(f"API request timed out: {e}")
            if args.debug:
                print(f"Error: API request timed out after {API_TIMEOUT} seconds")
            else:
                print("Error: API request timed out")
            
            # Try fallback if timeout occurs
            if not args.raw and args.debug:
                logger.info("Falling back to raw output due to timeout...")
                try:
                    # Fallback to raw output with shorter timeout
                    result = await asyncio.wait_for(
                        analyze_trivia_raw(image, args.debug),
                        timeout=API_TIMEOUT - 2  # Shorter timeout for fallback
                    )
                    logger.info("\n=== GPT-4o Fallback Analysis ===")
                    logger.info(result)
                    logger.info("==========================\n")
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {fallback_error}")
        except Exception as e:
            if args.debug:
                logger.error(f"Error analyzing trivia with GPT-4o: {e}")
                print(f"Error analyzing trivia with GPT-4o: {e}")
                print("Falling back to raw output...")
                try:
                    # Fallback to raw output
                    result = await analyze_trivia_raw(image, args.debug)
                    print("\n=== GPT-4o Fallback Analysis ===")
                    print(result)
                    print("==========================\n")
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {fallback_error}")
                    print(f"Fallback also failed: {fallback_error}")
            else:
                print("Error: Failed to analyze trivia")
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
    parser.add_argument("--debug", action="store_true",
                        help="Print debug information")
    parser.add_argument("--raw", action="store_true",
                        help="Use raw output from GPT-4o instead of structured JSON")
    parser.add_argument("--timeout", type=int, default=API_TIMEOUT,
                        help="Timeout for API calls in seconds (default: {})".format(API_TIMEOUT))
    parser.add_argument("image_path", nargs="?", help="Path to an image file to analyze instead of taking a screenshot")
    args = parser.parse_args()
    
    # Update timeout if specified
    API_TIMEOUT = args.timeout
    # Update timeout in chatgpt module
    set_api_timeout(API_TIMEOUT)
    
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
        screenshot_shutdown()

if __name__ == "__main__":
    main()
