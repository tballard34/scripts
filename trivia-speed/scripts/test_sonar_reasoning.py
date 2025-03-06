#!/usr/bin/env python3
"""
Test script for the sonar-reasoning model output handling in perplexity.py.
"""

import json
import logging
from perplexity import extract_json_from_sonar_reasoning, TriviaAnalysis

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Sample sonar-reasoning output with <think> section
SAMPLE_OUTPUT = """<think>
Okay, let's tackle this trivia question. The user is asking which US company became the first to reach a $1 trillion market cap, with options being Apple, Amazon, or Microsoft.

First, I need to recall the information from the provided search results. Let me go through each result to find the relevant details.

Looking at search result [1], the title clearly states that Apple became the first US trillion-dollar public company in 2018. The article mentions that Apple's shares closed at $207.39 on August 2, 2018, pushing its market cap to about $1.001 trillion. It also notes that other tech giants like Amazon and Microsoft were approaching but hadn't reached that milestone yet. This seems like a strong indicator that Apple was the first.

Search result [3] includes a table showing the time each company took to reach $1 trillion. Apple's entry shows it took 37 years, 7 months, and 15 days from its IPO in 1980 to reach $1 trillion in August 2018. Amazon is listed as reaching it in September 2018, just a month after Apple. Microsoft followed in April 2019. This confirms Apple was first among these three.

Search result [5] also mentions that Apple was the first US company to surpass the trillion-dollar mark in August 2018, and it was the first longer-lasting trillion-dollar company. PetroChina is noted as the first ever, but it's not a US company, so Apple holds the title for US companies.

The other results, like [2] and [4], discuss Amazon reaching $2 trillion and other companies, but they don't contradict the information about Apple being the first to $1 trillion. 

So, putting it all together, the answer is Apple (AAPL). The rationale is that Apple achieved the $1 trillion market cap first in August 2018, as per multiple sources. The other options, Amazon and Microsoft, reached this milestone later.
</think>

```json
{
  "rationale": "Apple became the first US company to reach a $1 trillion market cap on August 2, 2018, when its shares closed at $207.39[1][3][5].",
  "answer": "Apple (AAPL)"
}
```"""

def test_extract_json():
    """Test the extract_json_from_sonar_reasoning function."""
    try:
        # Extract JSON from the sample output
        parsed_content = extract_json_from_sonar_reasoning(SAMPLE_OUTPUT)
        
        # Validate the extracted JSON
        analysis = TriviaAnalysis(**parsed_content)
        
        # Print the results
        logger.info("Successfully extracted JSON from sonar-reasoning output:")
        logger.info(f"Rationale: {analysis.rationale}")
        logger.info(f"Answer: {analysis.answer}")
        
        # Verify the expected values
        expected_answer = "Apple (AAPL)"
        if analysis.answer == expected_answer:
            logger.info("✅ Test passed: Answer matches expected value")
        else:
            logger.error(f"❌ Test failed: Expected answer '{expected_answer}', got '{analysis.answer}'")
            
        return True
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

def test_regular_json():
    """Test handling regular JSON without <think> section."""
    regular_json = """{"rationale": "Apple was the first US company to reach $1 trillion in market cap in August 2018.", "answer": "Apple (AAPL)"}"""
    
    try:
        # Extract JSON from regular output
        parsed_content = extract_json_from_sonar_reasoning(regular_json)
        
        # Validate the extracted JSON
        analysis = TriviaAnalysis(**parsed_content)
        
        # Print the results
        logger.info("Successfully extracted JSON from regular output:")
        logger.info(f"Rationale: {analysis.rationale}")
        logger.info(f"Answer: {analysis.answer}")
        
        # Verify the expected values
        expected_answer = "Apple (AAPL)"
        if analysis.answer == expected_answer:
            logger.info("✅ Test passed: Answer matches expected value")
        else:
            logger.error(f"❌ Test failed: Expected answer '{expected_answer}', got '{analysis.answer}'")
            
        return True
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("Testing sonar-reasoning output handling...")
    
    # Run the tests
    sonar_test_result = test_extract_json()
    regular_test_result = test_regular_json()
    
    # Print overall results
    if sonar_test_result and regular_test_result:
        logger.info("✅ All tests passed!")
    else:
        logger.error("❌ Some tests failed!") 