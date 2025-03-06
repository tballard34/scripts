# Trivia Speed Assistant

A tool to help you quickly answer trivia questions by taking a screenshot and analyzing it with AI.

## Features

- Takes a screenshot of the right third of your screen (where trivia questions typically appear)
- Analyzes the image using multiple AI models:
  - **GPT-4o**: For answering trivia questions with reasoning
  - **Mistral AI**: Alternative model for answering trivia questions
  - **Gemini 2.0**: For OCR (Optical Character Recognition) to extract text from the image
  - **Perplexity AI**: For answering trivia questions using OCR results from Gemini with two models in parallel:
    - **sonor**: Perplexity's standard model
    - **sonar-pro**: Perplexity's advanced model
- Provides answers quickly with optional detailed reasoning
- Uses structured JSON output for consistent parsing
- Concurrent processing for faster results

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pnpm install
   ```
3. Create a `.env` file with your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key
   MISTRAL_API_KEY=your_mistral_api_key
   GEMINI_API_KEY=your_gemini_api_key
   PERPLEXITY_API_KEY=your_perplexity_api_key
   API_TIMEOUT=15
   MAX_TOKENS=200
   ```

## Usage

```
python scripts/main.py [options]
```

### Options

- `-o, --output`: Output file path (default: screenshots folder with timestamp)
- `-q, --quality`: JPEG quality (1-100, default: 60)
- `-r, --resize`: Resize factor for the image (default: 0.5 = 50%)
- `--save-original`: Save an unmodified copy of the screenshot
- `--no-gpt`: Skip sending to GPT-4o
- `--no-mistral`: Skip sending to Mistral AI
- `--no-gemini-ocr`: Skip sending to Gemini 2.0 for OCR (skip text extraction)
- `--no-perplexity`: Skip sending to Perplexity AI
- `--debug`: Print debug information
- `--timeout`: Timeout for API calls in seconds (default: 15)
- `image_path`: Path to an image file to analyze instead of taking a screenshot

### Examples

Basic usage (takes screenshot and analyzes with all models):
```
python scripts/main.py
```

Use only Gemini for OCR and Perplexity for analysis:
```
python scripts/main.py --no-gpt --no-mistral
```

Use only Gemini for OCR (no analysis):
```
python scripts/main.py --no-gpt --no-mistral --no-perplexity
```

Analyze an existing image:
```
python scripts/main.py path/to/image.jpg
```

## Requirements

- Python 3.8+
- OpenAI API key (for GPT-4o)
- Mistral API key (for Mistral AI)
- Gemini API key (for OCR)
- Perplexity API key (for Perplexity AI)

## License

MIT