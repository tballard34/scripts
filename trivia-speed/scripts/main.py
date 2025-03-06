#!/usr/bin/env python3
"""
Trivia Speed Assistant

This script takes a screenshot of the right third of the screen,
sends it to GPT-4o and/or Mistral AI for analysis, and returns the answer to the trivia question.
It can also use Gemini 2.0 for OCR to extract text from the image and Perplexity AI for analysis.
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

# Import Perplexity module
from perplexity import (
    analyze_trivia_with_perplexity,
    TriviaAnalysis as PerplexityTriviaAnalysis,
    set_api_timeout as set_perplexity_api_timeout,
    shutdown as perplexity_shutdown
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

# Global OCR result to share between Perplexity and other models
ocr_result = None

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
            # In non-debug mode, only print the answer with a newline before
            print(f"\n{result.answer}")
            
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
            # In non-debug mode, only print the answer with a newline before
            print(f"\n\033[38;5;208m{result.answer}\033[0m")
            
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

async def process_with_perplexity(ocr_result, args, model="sonar-pro"):
    """Process the OCR result with Perplexity AI
    
    Args:
        ocr_result: The OCR result containing question and options
        args: Command line arguments
        model (str, optional): The Perplexity model to use. Defaults to "sonar-pro".
    """
    try:
        if args.debug:
            logger.info(f"Sending OCR result to Perplexity for analysis using model: {model}...")
            print(f"Sending OCR result to Perplexity for analysis using model: {model}...")
        
        # Send OCR result to Perplexity
        perplexity_result = await analyze_trivia_with_perplexity(ocr_result, args.debug, model)
        
        # Print the result
        if args.debug:
            print(f"\n--- Perplexity AI Analysis ({model}) ---")
            print(f"Answer: {perplexity_result.answer}")
            print(f"Rationale: {perplexity_result.rationale}")
        else:
            if model == "sonar":
                color_code = "50"  # dark teal
            elif model == "sonar-pro":
                color_code = "40"  # blue
            else: # sonar-reasoning
                color_code = "30"  # light teal
            print(f"\n\033[38;5;{color_code}m{perplexity_result.answer}\033[0m")
        
        return perplexity_result
    except TimeoutError as e:
        logger.error(f"Perplexity API request timed out: {e}")
        if args.debug:
            print(f"Error: Perplexity API request timed out after {API_TIMEOUT} seconds")
        else:
            print(f"Error: Perplexity API request timed out for model {model}")
    except Exception as e:
        if args.debug:
            logger.error(f"Error analyzing with Perplexity ({model}): {e}")
            print(f"Error analyzing with Perplexity ({model}): {e}")
        else:
            print(f"Error: Failed to analyze with Perplexity ({model})")

async def process_with_gemini_ocr(image, args):
    """Process the image with Gemini OCR"""
    global ocr_result
    try:
        if args.debug:
            logger.info("Sending image to Gemini for OCR and analysis...")
            print("Sending image to Gemini for OCR and analysis...")
        
        # Send image to Gemini for OCR
        ocr_result = await extract_text_with_gemini(image, args.debug)
        
        # Print the OCR result
        if args.debug:
            # In debug mode, show full details
            print("\n--- Gemini OCR Result ---")
            print(f"Question: {ocr_result.question}")
            print("Options:")
            for i, option in enumerate(ocr_result.options):
                print(f"  {i+1}. {option}")
            print(f"Gemini Answer: {ocr_result.answer}")
            print(f"Gemini Rationale: {ocr_result.rationale}")
        elif args.show_ocr:
            # If --show-ocr flag is enabled, show question and options with spacing
            # Add a newline before the first line of output
            print(f"\n{ocr_result.question}\n")
            for i, option in enumerate(ocr_result.options):
                print(f"  {i+1}. {option}")
            print("")
            # Print the answer in purplish color
            print(f"\033[38;5;135m{ocr_result.answer}\033[0m")
        else:
            # By default, only print the answer in purplish color with a newline before
            print(f"\n\033[38;5;135m{ocr_result.answer}\033[0m")
        
        return ocr_result
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
    global ocr_result
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
            ocr_result = await process_with_gemini_ocr(image, args)
            
            # Run Perplexity with OCR result if enabled and OCR was successful
            if not args.no_perplexity and ocr_result:
                # Create tasks for both Perplexity models
                perplexity_tasks = [
                    process_with_perplexity(ocr_result, args, "sonar"),
                    process_with_perplexity(ocr_result, args, "sonar-pro"),
                    process_with_perplexity(ocr_result, args, "sonar-reasoning")
                ]
                # Run both Perplexity models in parallel
                await asyncio.gather(*perplexity_tasks)
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
            if args.debug and args.no_gemini_ocr and args.no_perplexity:
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
    parser.add_argument("--no-perplexity", action="store_true", 
                        help="Skip sending to Perplexity AI (skip Perplexity analysis)")
    parser.add_argument("--debug", action="store_true",
                        help="Print debug information")
    parser.add_argument("--show-ocr", action="store_true",
                        help="Show the OCR extracted question and options")
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
    set_perplexity_api_timeout(API_TIMEOUT)
    
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
        perplexity_shutdown()
        screenshot_shutdown()

if __name__ == "__main__":
    main()
