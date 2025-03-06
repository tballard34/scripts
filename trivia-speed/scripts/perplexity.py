#!/usr/bin/env python3
"""
Perplexity AI integration for Trivia Speed Assistant.

This module contains functions for interacting with Perplexity's API
to analyze trivia questions using OCR results from Gemini.
"""

import asyncio
import concurrent.futures
import functools
import json
import logging
import os
import time
from typing import Optional
import re

import aiohttp
from dotenv import load_dotenv
from pydantic import BaseModel

# Configure logging
logger = logging.getLogger('trivia-speed')

# Load environment variables from .env file
load_dotenv()

# Get Perplexity API key from environment variables
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
# Perplexity API endpoint
API_ENDPOINT = "https://api.perplexity.ai/chat/completions"
# Default model
MODEL = "sonar-pro"
MAX_TOKENS = int(os.getenv("PERPLEXITY_MAX_TOKENS", "10000"))  # Token count for response
API_TIMEOUT = int(os.getenv("PERPLEXITY_API_TIMEOUT", "15"))  # Timeout for API calls in seconds

# System prompt for Perplexity
SYSTEM_PROMPT = """
# Role
You are an expert trivia player.

# Task
I will give you a trivia question that has been extracted using OCR. The question will include multiple choice options. 
These questions are coming from Robinhood's trivia game so they are mostly financial questions. 
If you clearly do not know the answer, then say that you do not know.

# Output Format
You MUST provide your response in valid JSON format with these fields:
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

# Thread pool for CPU-bound tasks
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

def prepare_api_request(ocr_result, model=MODEL):
    """
    Prepare the API request payload for Perplexity.
    
    Args:
        ocr_result: The OCR result containing question and options
        model (str, optional): The Perplexity model to use. Defaults to MODEL.
        
    Returns:
        dict: The API request payload
    """
    # Format the question and options into a single prompt
    question_text = ocr_result.question
    options_text = "\n".join([f"{i+1}. {option}" for i, option in enumerate(ocr_result.options)])
    
    user_prompt = f"Question: {question_text}\n\nOptions:\n{options_text}"
    
    # Create the request payload
    request = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        "max_tokens": MAX_TOKENS,
        "temperature": 0.1,  # Lower temperature for more deterministic responses
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "schema": TriviaAnalysis.model_json_schema()
            }
        }
    }
    
    return request

def extract_json_from_sonar_reasoning(content):
    """
    Extract JSON from sonar-reasoning model output which may include a <think>...</think> section.
    
    Args:
        content (str): The raw content from the API response
        
    Returns:
        dict: The extracted JSON data
    """
    # Check if the content contains a <think> section
    if "<think>" in content and "```json" in content:
        # Extract the JSON part that comes after the <think> section
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1).strip()
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from sonar-reasoning output")
                raise ValueError("Failed to parse JSON from sonar-reasoning output")
    
    # If no <think> section or no JSON found, try to parse the whole content as JSON
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse JSON from content")
        raise ValueError("Failed to parse JSON from content")

async def analyze_trivia_with_perplexity(ocr_result, debug=False, model=MODEL):
    """
    Send the OCR result to Perplexity for analysis.
    
    Args:
        ocr_result: The OCR result containing question and options
        debug (bool, optional): Whether to print debug information.
        model (str, optional): The Perplexity model to use. Defaults to MODEL.
        
    Returns:
        TriviaAnalysis: The parsed response from Perplexity with rationale and answer
    """
    if not PERPLEXITY_API_KEY:
        raise ValueError("Perplexity API key not found. Please set it in the .env file.")
    
    if debug:
        logger.info(f"Sending OCR result to Perplexity for analysis using model: {model}...")
    start_time = time.time()
    
    # Prepare the API request in a separate thread to avoid blocking
    loop = asyncio.get_event_loop()
    try:
        request = await loop.run_in_executor(
            thread_pool, 
            functools.partial(prepare_api_request, ocr_result, model)
        )
        
        # Call the Perplexity API with timeout
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {PERPLEXITY_API_KEY}"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    API_ENDPOINT,
                    headers=headers,
                    json=request,
                    timeout=API_TIMEOUT
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Perplexity API error: {response.status} - {error_text}")
                        raise ValueError(f"Perplexity API error: {response.status} - {error_text}")
                    
                    result = await response.json()
                    
            if debug:
                elapsed = time.time() - start_time
                logger.info(f"Perplexity response received in {elapsed:.3f} seconds")
            
            # Extract the content from the response
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "{}")
            
            # Parse the content based on the model
            try:
                if model == "sonar-reasoning":
                    if debug:
                        logger.info("Processing sonar-reasoning model output")
                    parsed_content = extract_json_from_sonar_reasoning(content)
                else:
                    # For other models, parse the content directly as JSON
                    parsed_content = json.loads(content)
                
                return TriviaAnalysis(**parsed_content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Raw content: {content}")
                raise ValueError(f"Failed to parse Perplexity response: Invalid JSON returned")
                
        except asyncio.TimeoutError:
            logger.error(f"API request timed out after {API_TIMEOUT} seconds")
            raise TimeoutError(f"Perplexity API request timed out after {API_TIMEOUT} seconds")
        except Exception as e:
            logger.error(f"Error processing Perplexity response: {e}")
            raise ValueError(f"Failed to process Perplexity response: {e}")
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