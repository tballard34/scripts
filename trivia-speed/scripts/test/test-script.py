#!/usr/bin/env python3
"""
Test script for trivia-speed

This script runs main.py on each screenshot in the src/test/screenshots folder,
tracks the time taken, and checks if the answers are correct.
"""

import os
import sys
import time
import subprocess
import argparse
from pathlib import Path
import re
import asyncio
import concurrent.futures

# Add the parent directory to the path so we can import from src
sys.path.append(str(Path(__file__).parent.parent.parent))

# Define the expected answers for each screenshot
EXPECTED_ANSWERS = {
    "tesla.jpg": ["Tesla", "TSLA"],
    "SPS.jpg": ["SPS"],
    "7000.jpg": ["7000", "$7,000", "$7000", "7,000"],
    "ge.jpg": ["General Electric", "GE"],
    "nasdaq.jpg": ["NASDAQ", "Nasdaq", "Nasdaq Composite"],
    "Apple.jpg": ["Apple", "AAPL"],
    "Lineage.jpg": ["Lineage"]
}

def run_main_on_screenshot(screenshot_path, model="gpt", debug=False, verbose=False):
    """Run main.py on a screenshot and return the output and time taken"""
    start_time = time.time()
    
    # Run main.py with the screenshot path
    cmd = [
        "python", 
        str(Path(__file__).parent.parent / "main.py"),
    ]
    
    # Add debug flag if requested
    if debug:
        cmd.append("--debug")
    
    # Add model-specific flags
    if model == "gpt":
        cmd.append("--no-mistral")
        cmd.append("--no-gemini")
        cmd.append("--no-sonar")
        cmd.append("--no-sonar-pro")
        cmd.append("--no-sonar-reasoning")
    elif model == "mistral":
        cmd.append("--no-gpt")
        cmd.append("--no-gemini")
        cmd.append("--no-sonar")
        cmd.append("--no-sonar-pro")
        cmd.append("--no-sonar-reasoning")
    elif model == "gemini":
        cmd.append("--no-gpt")
        cmd.append("--no-mistral")
        cmd.append("--no-sonar")
        cmd.append("--no-sonar-pro")
        cmd.append("--no-sonar-reasoning")
    elif model == "sonar":
        cmd.append("--only-sonar")
    elif model == "sonar-pro":
        cmd.append("--only-sonar-pro")
    elif model == "sonar-reasoning":
        cmd.append("--only-sonar-reasoning")
    
    # Add the screenshot path
    cmd.append(screenshot_path)
    
    if verbose:
        print(f"Running command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    end_time = time.time()
    time_taken = end_time - start_time
    
    # Check if the time taken is reasonable for an API call
    if time_taken < 1.0 and not debug:
        print(f"WARNING: Response time ({time_taken:.2f}s) is too fast for a {model.upper()} API call!")
        print("The API might not be getting called. Try running with --debug to see more details.")
    
    if verbose:
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
    
    return result.stdout.strip(), time_taken

def check_answer(output, expected_answers):
    """Check if the output contains any of the expected answers"""
    # If expected_answers is a string, convert to list
    if isinstance(expected_answers, str):
        expected_answers = [expected_answers]
    
    # Convert output to lowercase for case-insensitive comparison
    output_lower = output.lower()
    
    # Extract the answer from the output
    extracted = extract_answer(output)
    extracted_lower = extracted.lower() if extracted else ""
    
    # Check if any of the expected answers are in the output or extracted answer
    for expected in expected_answers:
        expected_lower = expected.lower()
        
        # Check in full output
        if expected_lower in output_lower:
            return True
        
        # Check in extracted answer
        if extracted and expected_lower in extracted_lower:
            return True
        
        # Special case for numbers with/without commas or dollar signs
        if any(c.isdigit() for c in expected):
            # Remove non-digit characters for comparison
            expected_digits = ''.join(c for c in expected if c.isdigit())
            output_digits = ''.join(c for c in output if c.isdigit())
            extracted_digits = ''.join(c for c in extracted if c.isdigit())
            
            if expected_digits in output_digits or expected_digits in extracted_digits:
                return True
    
    return False

def extract_answer(output):
    """Try to extract just the answer from the output"""
    # If output is empty or None, return empty string
    if not output:
        return ""
    
    # The output should now always be just the answer since we're using structured output
    # and main.py only prints the answer in non-debug mode
    if output and not output.startswith("{") and not "===" in output:
        return output.strip()
    
    # For debug mode or other formats, try to extract the answer
    for line in output.split('\n'):
        if "Answer:" in line:
            return line.replace("Answer:", "").strip()
    
    # If no clear answer found, return the last non-empty line (often the answer)
    non_empty_lines = [line.strip() for line in output.split('\n') if line.strip()]
    if non_empty_lines:
        return non_empty_lines[-1]
    
    # If all else fails, return the whole output (truncated if too long)
    if len(output) > 50:
        return output[:47] + "..."
    return output

async def process_screenshot(screenshot_file, model, args):
    """Process a single screenshot asynchronously"""
    screenshot_name = screenshot_file.name
    expected_answers = EXPECTED_ANSWERS.get(screenshot_name, ["Unknown"])
    
    # Display the first expected answer in the table
    display_expected = expected_answers[0] if isinstance(expected_answers, list) else expected_answers
    
    # Run main.py on the screenshot (in a thread pool to avoid blocking)
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        output, time_taken = await loop.run_in_executor(
            pool, 
            lambda: run_main_on_screenshot(str(screenshot_file), model, args.debug, args.verbose)
        )
    
    # Extract the answer from the output
    actual_answer = extract_answer(output)
    
    # Check if the answer is correct
    is_correct = check_answer(output, expected_answers)
    
    return {
        "screenshot": screenshot_name,
        "expected_answer": display_expected,
        "actual_answer": actual_answer,
        "output": output,
        "is_correct": is_correct,
        "time_taken": time_taken
    }

async def process_screenshots_async(screenshots_dir, model, args):
    """Process all screenshots for a specific model asynchronously and return results"""
    print(f"\n{'='*50}")
    print(f"Running tests with {model.upper()} model")
    print(f"{'='*50}")
    
    print(f"{'Screenshot':<20} | {'Expected Answer':<20} | {'Actual Answer':<30} | {'Correct?':<10} | {'Time (s)':<10}")
    print("-" * 100)
    
    # Create tasks for all screenshots
    tasks = []
    for screenshot_file in screenshots_dir.glob("*.jpg"):
        task = process_screenshot(screenshot_file, model, args)
        tasks.append(task)
    
    # Run all tasks concurrently
    results = await asyncio.gather(*tasks)
    
    # Sort results by screenshot name for consistent output
    results.sort(key=lambda r: r["screenshot"])
    
    # Print results
    for result in results:
        print(f"{result['screenshot']:<20} | {result['expected_answer']:<20} | {result['actual_answer']:<30} | {'Yes' if result['is_correct'] else 'No':<10} | {result['time_taken']:.2f}s")
    
    # Print summary
    correct_count = sum(1 for r in results if r["is_correct"])
    total_count = len(results)
    print("\nSummary:")
    print(f"Correct: {correct_count}/{total_count} ({correct_count/total_count*100:.1f}%)")
    print(f"Average time: {sum(r['time_taken'] for r in results)/total_count:.2f}s")
    
    # Check if the average time is reasonable for API calls
    avg_time = sum(r['time_taken'] for r in results)/total_count
    if avg_time < 1.0:
        print(f"\nWARNING: Average response time is too fast for {model.upper()} API calls!")
        print("The API might not be getting called. Try running with --debug for more details.")
    
    return results

async def main_async(args):
    """Async version of main function"""
    # Get the path to the screenshots folder
    screenshots_dir = Path(__file__).parent / "screenshots"
    
    # Check if all models are disabled
    if (args.no_gpt and args.no_mistral and args.no_gemini and 
        args.no_sonar and args.no_sonar_pro and args.no_sonar_reasoning):
        print("Error: Cannot disable all models. Please enable at least one model.")
        return
    
    # Process screenshots for each model if not disabled
    results = {}
    
    # Process GPT
    if not args.no_gpt:
        results["gpt"] = await process_screenshots_async(screenshots_dir, "gpt", args)
    
    # Process Mistral
    if not args.no_mistral:
        results["mistral"] = await process_screenshots_async(screenshots_dir, "mistral", args)
    
    # Process Gemini
    if not args.no_gemini:
        results["gemini"] = await process_screenshots_async(screenshots_dir, "gemini", args)
    
    # Process Sonar
    if not args.no_sonar:
        results["sonar"] = await process_screenshots_async(screenshots_dir, "sonar", args)
    
    # Process Sonar Pro
    if not args.no_sonar_pro:
        results["sonar-pro"] = await process_screenshots_async(screenshots_dir, "sonar-pro", args)
    
    # Process Sonar Reasoning
    if not args.no_sonar_reasoning:
        results["sonar-reasoning"] = await process_screenshots_async(screenshots_dir, "sonar-reasoning", args)
    
    # Print comparison if multiple models were tested
    if len(results) > 1:
        print("\n" + "="*50)
        print("Model Comparison")
        print("="*50)
        
        # Get total count (should be the same for all models)
        total_count = len(next(iter(results.values())))
        
        # Print accuracy comparison
        print("Accuracy:")
        for model, model_results in results.items():
            correct_count = sum(1 for r in model_results if r["is_correct"])
            print(f"{model.upper()} Accuracy: {correct_count}/{total_count} ({correct_count/total_count*100:.1f}%)")
        
        print("\nAverage Response Time:")
        for model, model_results in results.items():
            avg_time = sum(r['time_taken'] for r in model_results)/total_count
            print(f"{model.upper()} Average Time: {avg_time:.2f}s")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test trivia-speed on a set of screenshots")
    parser.add_argument("--debug", action="store_true", help="Run with debug output")
    parser.add_argument("--verbose", action="store_true", help="Show verbose output")
    parser.add_argument("--no-gpt", action="store_true", help="Skip testing with GPT model")
    parser.add_argument("--no-mistral", action="store_true", help="Skip testing with Mistral model")
    parser.add_argument("--no-gemini", action="store_true", help="Skip testing with Gemini model")
    parser.add_argument("--no-sonar", action="store_true", help="Skip testing with Sonar model")
    parser.add_argument("--no-sonar-pro", action="store_true", help="Skip testing with Sonar Pro model")
    parser.add_argument("--no-sonar-reasoning", action="store_true", help="Skip testing with Sonar Reasoning model")
    args = parser.parse_args()
    
    # Run the async main function
    asyncio.run(main_async(args))

if __name__ == "__main__":
    main()
