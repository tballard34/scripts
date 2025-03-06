#!/usr/bin/env python3
"""
Gemini OCR and Analysis integration for Trivia Speed Assistant.

This module contains functions for interacting with Google's Gemini API
to perform OCR on trivia question images and provide answers.
"""

import os
import time
import asyncio
import json
import functools
import concurrent.futures
import logging
from PIL import Image
from typing import Optional
import google.generativeai as genai
from pydantic import BaseModel

# Import screenshot module for image preparation
from screenshot import prepare_image_for_api

# Configure logging
logger = logging.getLogger('trivia-speed')

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Get Gemini API key from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

MODEL = "gemini-2.0-flash"
MAX_TOKENS = int(os.getenv("GEMINI_MAX_TOKENS", "10000"))  # Token count for response
API_TIMEOUT = int(os.getenv("GEMINI_API_TIMEOUT", "15"))  # Timeout for API calls in seconds

# Configure the Gemini API
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Do not change the system prompt - this is for the AI
SYSTEM_PROMPT = """
# Role
You are an expert trivia player with OCR capabilities.

# Task
I will give you an image containing a trivia question. Extract the text and answer the question.

# Output Format
Provide your response in valid JSON format with these fields:
- "question": The full text of the question
- "options": An array of the multiple choice options (if present)
- "rationale": A brief explanation of your reasoning (1-2 sentences)
- "answer": The final answer (just the letter or specific answer word/phrase)

Example:
{
  "question": "Which company was founded by Bill Gates and Paul Allen in 1975?",
  "options": ["Apple", "Microsoft", "IBM"],
  "rationale": "Microsoft was founded by Bill Gates and Paul Allen in 1975 in Albuquerque, New Mexico.",
  "answer": "Microsoft"
}
"""

# Define the Pydantic model for structured output
class OCRResult(BaseModel):
    question: str
    options: list[str]
    rationale: str
    answer: str

# Thread pool for CPU-bound tasks
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

def prepare_api_request(image):
    """
    Prepare the API request payload for Gemini.
    
    Args:
        image (PIL.Image): The image to analyze
        
    Returns:
        dict: The API request payload
    """
    # Convert PIL image to base64
    base64_image = prepare_image_for_api(image)
    
    # Create the content parts
    contents = [
        {
            "role": "user",
            "parts": [
                {"text": SYSTEM_PROMPT},
                {"inline_data": {"mime_type": "image/jpeg", "data": base64_image}}
            ]
        }
    ]
    
    # Create generation config
    generation_config = {
        "max_output_tokens": MAX_TOKENS,
        "temperature": 0.1,  # Lower temperature for more deterministic responses
        "response_mime_type": "application/json"
    }
    
    return {
        "contents": contents,
        "generation_config": generation_config
    }

async def extract_text_with_gemini(image, debug=False):
    """
    Send the image to Gemini for OCR analysis and answer using structured output.
    
    Args:
        image (PIL.Image): The image to analyze
        debug (bool, optional): Whether to print debug information.
        
    Returns:
        OCRResult: The parsed response from Gemini with extracted text and answer
    """
    if not GEMINI_API_KEY:
        raise ValueError("Gemini API key not found. Please set it in the .env file.")
    
    if debug:
        logger.info("Sending image to Gemini for OCR and analysis...")
    start_time = time.time()
    
    # Prepare the API request in a separate thread to avoid blocking
    loop = asyncio.get_event_loop()
    try:
        request = await loop.run_in_executor(
            thread_pool, 
            functools.partial(prepare_api_request, image)
        )
        
        # Call the Gemini API with timeout
        try:
            # Create a coroutine to call the Gemini API
            async def call_gemini_api():
                model = genai.GenerativeModel(MODEL)
                response = await loop.run_in_executor(
                    thread_pool,
                    lambda: model.generate_content(**request)
                )
                return response
            
            # Call with timeout
            response = await asyncio.wait_for(
                call_gemini_api(),
                timeout=API_TIMEOUT
            )
            
            if debug:
                elapsed = time.time() - start_time
                logger.info(f"Gemini response received in {elapsed:.3f} seconds")
            
            # Parse the JSON response
            try:
                content = response.text
                result = json.loads(content)
                
                # Extract fields from the JSON
                question = result.get("question", "")
                options = result.get("options", [])
                rationale = result.get("rationale", "")
                answer = result.get("answer", "")
                
                return OCRResult(question=question, options=options, rationale=rationale, answer=answer)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                # Fallback to using the raw text
                full_text = response.text
                
                # Try to extract question, options, and answer from the text
                lines = full_text.strip().split('\n')
                question = ""
                options = []
                rationale = ""
                answer = ""
                
                # Simple parsing logic for non-JSON response
                for i, line in enumerate(lines):
                    line = line.strip()
                    if "question" in line.lower() and not question:
                        question = line.split(":", 1)[1].strip() if ":" in line else line
                    elif "option" in line.lower() or (line and line[0].isalpha() and line[1:2] == '.'):
                        option_text = line.split(":", 1)[1].strip() if ":" in line else line[2:].strip()
                        options.append(option_text)
                    elif "answer" in line.lower() and not answer:
                        answer = line.split(":", 1)[1].strip() if ":" in line else line
                    elif "reason" in line.lower() or "rationale" in line.lower() and not rationale:
                        rationale = line.split(":", 1)[1].strip() if ":" in line else line
                
                # If we couldn't parse properly, use first line as question and last as answer
                if not question and lines:
                    question = lines[0]
                if not answer and lines:
                    answer = lines[-1]
                if not rationale:
                    rationale = "Unable to determine rationale from response."
                
                return OCRResult(question=question, options=options, rationale=rationale, answer=answer)
                
        except asyncio.TimeoutError:
            logger.error(f"API request timed out after {API_TIMEOUT} seconds")
            raise TimeoutError(f"Gemini API request timed out after {API_TIMEOUT} seconds")
        except Exception as e:
            logger.error(f"Error processing Gemini response: {e}")
            raise ValueError(f"Failed to process Gemini response: {e}")
    except Exception as e:
        logger.error(f"Error preparing API request: {e}")
        raise ValueError(f"Failed to prepare API request: {e}")

def shutdown():
    """Shutdown the thread pool"""
    thread_pool.shutdown(wait=False)

def set_api_timeout(timeout):
    """Set the API timeout value"""
    global API_TIMEOUT
    API_TIMEOUT = timeout 