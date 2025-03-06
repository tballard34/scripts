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

def run_main_on_screenshot(screenshot_path, debug=False, verbose=False):
    """Run main.py on a screenshot and return the output and time taken"""
    start_time = time.time()
    
    # Run main.py with the screenshot path
    cmd = [
        "python", 
        str(Path(__file__).parent.parent / "main.py"),
        "--raw",  # Use raw output for simpler parsing
    ]
    
    # Add debug flag if requested
    if debug:
        cmd.append("--debug")
    
    # Add the screenshot path
    cmd.append(screenshot_path)
    
    if verbose:
        print(f"Running command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    end_time = time.time()
    time_taken = end_time - start_time
    
    # Check if the time taken is reasonable for an API call
    if time_taken < 1.0 and not debug:
        print(f"WARNING: Response time ({time_taken:.2f}s) is too fast for a ChatGPT API call!")
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
    
    # Look for "ANSWER:" in the output
    for line in output.split('\n'):
        if "ANSWER:" in line:
            return line.replace("ANSWER:", "").strip()
    
    # Look for a line that might contain the answer (after "rationale" or "reasoning")
    lines = output.split('\n')
    for i, line in enumerate(lines):
        if "rationale" in line.lower() or "reasoning" in line.lower() or "analysis" in line.lower():
            # The answer might be in the next line or two
            if i + 1 < len(lines) and lines[i + 1].strip():
                return lines[i + 1].strip()
            elif i + 2 < len(lines) and lines[i + 2].strip():
                return lines[i + 2].strip()
    
    # If no clear answer found, return the last non-empty line (often the answer)
    non_empty_lines = [line.strip() for line in lines if line.strip()]
    if non_empty_lines:
        return non_empty_lines[-1]
    
    # If all else fails, return the whole output (truncated if too long)
    if len(output) > 50:
        return output[:47] + "..."
    return output

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test trivia-speed on a set of screenshots")
    parser.add_argument("--debug", action="store_true", help="Run with debug output")
    parser.add_argument("--verbose", action="store_true", help="Show verbose output")
    args = parser.parse_args()
    
    # Get the path to the screenshots folder
    screenshots_dir = Path(__file__).parent / "screenshots"
    
    # Create a results table
    results = []
    
    print(f"{'Screenshot':<20} | {'Expected Answer':<20} | {'Actual Answer':<30} | {'Correct?':<10} | {'Time (s)':<10}")
    print("-" * 100)
    
    # Process each screenshot
    for screenshot_file in screenshots_dir.glob("*.jpg"):
        screenshot_name = screenshot_file.name
        expected_answers = EXPECTED_ANSWERS.get(screenshot_name, ["Unknown"])
        
        # Display the first expected answer in the table
        display_expected = expected_answers[0] if isinstance(expected_answers, list) else expected_answers
        
        # Run main.py on the screenshot
        output, time_taken = run_main_on_screenshot(str(screenshot_file), args.debug, args.verbose)
        
        # Extract the answer from the output
        actual_answer = extract_answer(output)
        
        # Check if the answer is correct
        is_correct = check_answer(output, expected_answers)
        
        # Print the result
        print(f"{screenshot_name:<20} | {display_expected:<20} | {actual_answer:<30} | {'Yes' if is_correct else 'No':<10} | {time_taken:.2f}s")
        
        # Store the result
        results.append({
            "screenshot": screenshot_name,
            "expected_answer": display_expected,
            "actual_answer": actual_answer,
            "output": output,
            "is_correct": is_correct,
            "time_taken": time_taken
        })
    
    # Print summary
    correct_count = sum(1 for r in results if r["is_correct"])
    total_count = len(results)
    print("\nSummary:")
    print(f"Correct: {correct_count}/{total_count} ({correct_count/total_count*100:.1f}%)")
    print(f"Average time: {sum(r['time_taken'] for r in results)/total_count:.2f}s")
    
    # Check if the average time is reasonable for API calls
    avg_time = sum(r['time_taken'] for r in results)/total_count
    if avg_time < 1.0:
        print("\nWARNING: Average response time is too fast for ChatGPT API calls!")
        print("The API might not be getting called. Try running with --debug for more details.")

if __name__ == "__main__":
    main()
