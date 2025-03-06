#!/usr/bin/env python3
"""
Mistral AI integration for Trivia Speed Assistant.

This module contains functions for interacting with Mistral AI's API
to analyze trivia questions from images.
"""

import os
import time
import asyncio
import json
from mistralai import Mistral
from pydantic import BaseModel
import functools
import concurrent.futures
import logging
import base64
from PIL import Image
from typing import Optional

# Import screenshot module for image preparation
from screenshot import prepare_image_for_api

# Configure logging
logger = logging.getLogger('trivia-speed')

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Get Mistral API key from environment variables
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
# Hardcoded model to Pixtral 12B
MODEL = "pixtral-12b-2409"
MAX_TOKENS = int(os.getenv("MISTRAL_MAX_TOKENS", "200"))  # Reduced token count for faster response
API_TIMEOUT = int(os.getenv("MISTRAL_API_TIMEOUT", "15"))  # Timeout for API calls in seconds

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

# Create a single Mistral client instance to reuse
client = Mistral(api_key=MISTRAL_API_KEY)

# Thread pool for CPU-bound tasks
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

def prepare_api_request(image, is_raw=False):
    """
    Prepare the API request payload for Mistral.
    
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

Example:
The company was founded in 1975 by Bill Gates and Paul Allen.
ANSWER: Microsoft
"""
    else:
        system_content = SYSTEM_PROMPT
    
    messages = [
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
                    "image_url": f"data:image/jpeg;base64,{base64_image}"
                }
            ]
        }
    ]
    
    request = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": MAX_TOKENS,
        "temperature": 0.1,  # Lower temperature for more deterministic responses
    }
    
    # Add response_format for JSON mode if not using raw output
    if not is_raw:
        request["response_format"] = {
            "type": "json_object"
        }
    
    return request

async def analyze_trivia_with_mistral(image, debug=False):
    """
    Send the image to Mistral for analysis.
    
    Args:
        image (PIL.Image): The image to analyze
        debug (bool, optional): Whether to print debug information.
        
    Returns:
        TriviaAnalysis: The parsed response from Mistral with rationale and answer
    """
    if not MISTRAL_API_KEY:
        raise ValueError("Mistral API key not found. Please set it in the .env file.")
    
    if debug:
        logger.info("Sending image to Mistral for analysis...")
    start_time = time.time()
    
    # Prepare the API request in a separate thread to avoid blocking
    loop = asyncio.get_event_loop()
    try:
        request = await loop.run_in_executor(
            thread_pool, 
            functools.partial(prepare_api_request, image, is_raw=False)
        )
        
        # Call the Mistral API with timeout
        try:
            response = await asyncio.wait_for(
                client.chat.complete_async(**request),
                timeout=API_TIMEOUT
            )
            
            if debug:
                elapsed = time.time() - start_time
                logger.info(f"Mistral response received in {elapsed:.3f} seconds")
            
            content = response.choices[0].message.content
            
            # Parse the JSON response
            try:
                result = json.loads(content)
                # Extract rationale and answer from the JSON
                rationale = result.get("rationale", "")
                answer = result.get("answer", "")
                
                return TriviaAnalysis(rationale=rationale, answer=answer)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                # Fallback to the old parsing method if JSON parsing fails
                lines = content.strip().split('\n')
                rationale = ""
                answer = ""
                
                # More robust parsing for non-JSON responses
                if "rationale" in content.lower() or "answer" in content.lower():
                    # Try to extract structured data from unstructured text
                    for line in lines:
                        line = line.strip()
                        if line.lower().startswith("answer:") or "answer:" in line.lower():
                            parts = line.lower().split("answer:")
                            if len(parts) > 1:
                                answer = parts[1].strip()
                        elif line.lower().startswith("rationale:") or "rationale:" in line.lower():
                            parts = line.lower().split("rationale:")
                            if len(parts) > 1:
                                rationale = parts[1].strip()
                        elif not answer and line:  # If we haven't found the answer yet, it's part of the rationale
                            rationale += line + " "
                else:
                    # Simple approach: last line is likely the answer
                    if lines:
                        answer = lines[-1].strip()
                        rationale = " ".join(lines[:-1]).strip()
                
                # If we still don't have an answer, use the whole content as the answer
                if not answer:
                    answer = content.strip()
                    
                return TriviaAnalysis(rationale=rationale.strip(), answer=answer)
                
        except asyncio.TimeoutError:
            logger.error(f"API request timed out after {API_TIMEOUT} seconds")
            raise TimeoutError(f"Mistral API request timed out after {API_TIMEOUT} seconds")
        except Exception as e:
            logger.error(f"Error processing Mistral response: {e}")
            raise ValueError(f"Failed to process Mistral response: {e}")
    except Exception as e:
        logger.error(f"Error preparing API request: {e}")
        raise ValueError(f"Failed to prepare API request: {e}")

async def analyze_trivia_raw(image, debug=False):
    """
    Send the image to Mistral for analysis without structured output.
    
    Args:
        image (PIL.Image): The image to analyze
        debug (bool, optional): Whether to print debug information.
        
    Returns:
        str: The raw response from Mistral
    """
    if not MISTRAL_API_KEY:
        raise ValueError("Mistral API key not found. Please set it in the .env file.")
    
    if debug:
        logger.info("Sending image to Mistral for raw analysis...")
    start_time = time.time()
    
    # Prepare the API request in a separate thread to avoid blocking
    loop = asyncio.get_event_loop()
    try:
        request = await loop.run_in_executor(
            thread_pool, 
            functools.partial(prepare_api_request, image, is_raw=True)
        )
        
        # Call the Mistral API
        try:
            response = await asyncio.wait_for(
                client.chat.complete_async(**request),
                timeout=API_TIMEOUT
            )
            
            if debug:
                elapsed = time.time() - start_time
                logger.info(f"Mistral raw response received in {elapsed:.3f} seconds")
            
            content = response.choices[0].message.content
            
            # Try to extract just the answer if not in debug mode
            if not debug:
                # More efficient string parsing
                lines = content.strip().split('\n')
                
                # Look for an answer line
                for line in lines:
                    if line.lower().startswith("answer:"):
                        return line.replace("answer:", "", 1).strip()
                
                # If no explicit answer line, try to find the most likely answer
                # Typically the last non-empty line is the answer
                for line in reversed(lines):
                    if line.strip():
                        return line.strip()
            
            return content.strip() or "No answer found"
        except asyncio.TimeoutError:
            logger.error(f"API request timed out after {API_TIMEOUT} seconds")
            raise TimeoutError(f"Mistral API request timed out after {API_TIMEOUT} seconds")
        except Exception as e:
            logger.error(f"Error processing Mistral raw response: {e}")
            raise ValueError(f"Failed to process Mistral raw response: {e}")
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