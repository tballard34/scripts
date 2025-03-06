#!/usr/bin/env python3
"""
ChatGPT integration for Trivia Speed Assistant.

This module contains functions for interacting with OpenAI's GPT-4o API
to analyze trivia questions from images.
"""

import asyncio
import concurrent.futures
import functools
import logging
import os
import time
from typing import Optional

from dotenv import load_dotenv
from openai import AsyncOpenAI
from PIL import Image
from pydantic import BaseModel
# Import screenshot module for image preparation
from screenshot import prepare_image_for_api

# Configure logging
logger = logging.getLogger('trivia-speed')

# Load environment variables from .env file
load_dotenv()

# Get OpenAI API key from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Hardcoded model to GPT-4o
MODEL = "gpt-4o"
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "200"))  # Reduced token count for faster response
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "15"))  # Timeout for API calls in seconds

# Do not change the system prompt - this is for the AI
SYSTEM_PROMPT = """
# Role
You are an expert trivia player.

# Task
I will give you a trivia question in the form of a question and you must answer it. The questions will be multiple choice with most likely 3 options. These questions are coming from robinhoods trivia game so they are mostly financial questions. If you clearly do not konw the answer than say that you do not know.

# Output Format
Provide your response in valid JSON format with these fields:
- "rationale": A very brief explanation (1-2 sentences)
- "answer": The final answer (just the letter or specific answer word/phrase)

Example:
{
  "rationale": "Company X was founded in 1975 by Bill Gates and Paul Allen.",
  "answer": "Microsoft"
}
"""

# Define the Pydantic model for structured output
class TriviaAnalysis(BaseModel):
    rationale: str
    answer: str

# Create a single OpenAI client instance to reuse
client = AsyncOpenAI(api_key=OPENAI_API_KEY, timeout=API_TIMEOUT)

# Thread pool for CPU-bound tasks
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

def prepare_api_request(image):
    """
    Prepare the API request payload for GPT-4o.
    
    Args:
        image (PIL.Image): The image to analyze
        
    Returns:
        dict: The API request payload
    """
    # Encode the image to base64
    base64_image = prepare_image_for_api(image)
    
    system_content = SYSTEM_PROMPT
    response_format = TriviaAnalysis
    
    request = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": system_content
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Analyze this trivia question."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": MAX_TOKENS,
        "temperature": 0.1,  # Lower temperature for more deterministic responses
        "response_format": response_format
    }
    
    return request

async def analyze_trivia_with_gpt4o(image, debug=False):
    """
    Send the image to GPT-4o for analysis using Pydantic model for structured output.
    
    Args:
        image (PIL.Image): The image to analyze
        debug (bool, optional): Whether to print debug information.
        
    Returns:
        TriviaAnalysis: The parsed response from GPT-4o with rationale and answer
    """
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API key not found. Please set it in the .env file.")
    
    if debug:
        logger.info("Sending image to GPT-4o for analysis...")
    start_time = time.time()
    
    # Prepare the API request in a separate thread to avoid blocking
    loop = asyncio.get_event_loop()
    try:
        request = await loop.run_in_executor(
            thread_pool, 
            functools.partial(prepare_api_request, image)
        )
        
        # Call the OpenAI API with parse method and timeout
        try:
            response = await asyncio.wait_for(
                client.beta.chat.completions.parse(**request),
                timeout=API_TIMEOUT
            )
            
            if debug:
                elapsed = time.time() - start_time
                logger.info(f"GPT-4o response received in {elapsed:.3f} seconds")
            
            # Return the parsed model directly
            return response.choices[0].message.parsed
        except asyncio.TimeoutError:
            logger.error(f"API request timed out after {API_TIMEOUT} seconds")
            raise TimeoutError(f"GPT-4o API request timed out after {API_TIMEOUT} seconds")
        except Exception as e:
            logger.error(f"Error processing GPT-4o response: {e}")
            raise ValueError(f"Failed to process GPT-4o response: {e}")
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
    # Update the client timeout as well
    client.timeout = timeout 