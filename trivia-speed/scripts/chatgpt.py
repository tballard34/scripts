#!/usr/bin/env python3
"""
ChatGPT integration for Trivia Speed Assistant.

This module contains functions for interacting with OpenAI's GPT-4o API
to analyze trivia questions from images.
"""

import os
import time
import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv
from pydantic import BaseModel
import functools
import concurrent.futures
import logging
from PIL import Image
from typing import Optional

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

# System prompt for ChatGPT - Extremely simplified for faster processing
SYSTEM_PROMPT = """
You are an expert trivia player. Analyze the trivia question and provide:
- Very brief rationale (1-2 sentences)
- The final answer (just the letter or specific answer word/phrase)
"""

# Define the Pydantic model for structured output
class TriviaAnalysis(BaseModel):
    rationale: str
    answer: str

# Create a single OpenAI client instance to reuse
client = AsyncOpenAI(api_key=OPENAI_API_KEY, timeout=API_TIMEOUT)

# Thread pool for CPU-bound tasks
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

def prepare_api_request(image, is_raw=False):
    """
    Prepare the API request payload for GPT-4o.
    
    Args:
        image (PIL.Image): The image to analyze
        is_raw (bool): Whether to use raw output format
        
    Returns:
        dict: The API request payload
    """
    # Encode the image to base64
    base64_image = prepare_image_for_api(image)
    
    if is_raw:
        system_content = """
You are an expert trivia player. Analyze the question and provide:
- Brief reasoning (1-2 sentences)
- Final answer on a new line starting with "ANSWER: "
"""
        response_format = None
    else:
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
    }
    
    if response_format:
        request["response_format"] = response_format
    
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
            functools.partial(prepare_api_request, image, is_raw=False)
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

async def analyze_trivia_raw(image, debug=False):
    """
    Send the image to GPT-4o for analysis without structured output.
    
    Args:
        image (PIL.Image): The image to analyze
        debug (bool, optional): Whether to print debug information.
        
    Returns:
        str: The raw response from GPT-4o
    """
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API key not found. Please set it in the .env file.")
    
    if debug:
        logger.info("Sending image to GPT-4o for raw analysis...")
    start_time = time.time()
    
    # Prepare the API request in a separate thread to avoid blocking
    loop = asyncio.get_event_loop()
    try:
        request = await loop.run_in_executor(
            thread_pool, 
            functools.partial(prepare_api_request, image, is_raw=True)
        )
        
        # Call the OpenAI API without JSON response format
        try:
            response = await asyncio.wait_for(
                client.chat.completions.create(**request),
                timeout=API_TIMEOUT
            )
            
            if debug:
                elapsed = time.time() - start_time
                logger.info(f"GPT-4o raw response received in {elapsed:.3f} seconds")
            
            content = response.choices[0].message.content
            
            # Try to extract just the answer if not in debug mode
            if not debug:
                # More efficient string parsing
                for line in content.split('\n'):
                    if line.startswith("ANSWER:"):
                        return line.replace("ANSWER:", "").strip()
            
            return content
        except asyncio.TimeoutError:
            logger.error(f"API request timed out after {API_TIMEOUT} seconds")
            raise TimeoutError(f"GPT-4o API request timed out after {API_TIMEOUT} seconds")
        except Exception as e:
            logger.error(f"Error processing GPT-4o raw response: {e}")
            raise ValueError(f"Failed to process GPT-4o raw response: {e}")
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