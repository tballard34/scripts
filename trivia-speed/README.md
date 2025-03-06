# Trivia Speed Assistant

A fast and efficient system for analyzing trivia questions using GPT-4o.

## Architecture

The system consists of two main components:

1. **Client (`client/trivia-client.py`)**: 
   - Takes screenshots locally
   - Processes and optimizes images
   - Sends images to the server for analysis
   - Displays results

2. **Server (`server/trivia-server.py`)**: 
   - Maintains a persistent connection with OpenAI
   - Receives images from the client
   - Sends images to GPT-4o for analysis
   - Returns structured results

This architecture provides several benefits:
- Reduced latency through persistent connections
- Separation of concerns (client handles UI/screenshots, server handles AI)
- More efficient resource usage

## Directory Structure

```
trivia-speed/
├── client/                # Client-side code
│   ├── trivia-client.py   # Client implementation
│   └── trivia.sh          # Client shell script
├── server/                # Server-side code
│   ├── trivia-server.py   # Server implementation
│   └── start-server.sh    # Server shell script
├── common/                # Shared resources
│   ├── requirements.txt   # Dependencies
│   ├── .env               # Environment variables
│   ├── .env.example       # Example environment file
│   └── screenshots/       # Directory for saved screenshots
├── trivia-main.py         # Main entry point
├── trivia.sh              # Main shell script
└── README.md              # This file
```

## Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd trivia-speed
   ```

2. Install dependencies:
   ```bash
   pip install -r common/requirements.txt
   ```

3. Create a `.env` file in the `common` directory with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   MAX_TOKENS=200
   ```

## Usage

### Using the Main Script

The easiest way to use the system is through the main script:

```bash
./trivia.sh [command] [options]
```

Commands:
- `server`: Start the trivia server
- `client`: Start the trivia client

Examples:
```bash
# Start the server
./trivia.sh server

# Start the client
./trivia.sh client

# Start the client with options
./trivia.sh client --quality 90 --debug
```

### Starting the Server Directly

```bash
./server/start-server.sh
```

The server will start and listen on http://127.0.0.1:8000.

### Using the Client Directly

```bash
./client/trivia.sh [options]
```

Options:
- `-q, --quality`: JPEG quality (1-100, default: 60)
- `-r, --resize`: Resize factor for the image (default: 0.5 = 50%)
- `--save-original`: Save an unmodified copy of the screenshot
- `--no-gpt`: Skip sending to GPT-4o (just take screenshot)
- `--debug`: Print debug information
- `--raw`: Use raw output from GPT-4o instead of structured JSON

## API Endpoints

The server exposes the following endpoints:

- `GET /`: Check if the server is running
- `POST /analyze`: Analyze a trivia question from a base64-encoded image
- `POST /analyze-upload`: Analyze a trivia question from an uploaded image file

## Performance

The system is optimized for speed:
- Local screenshot capture reduces network overhead
- Persistent connection with OpenAI reduces latency
- Image optimization reduces transfer size
- Structured output parsing for consistent results

## Troubleshooting

If you encounter issues:

1. Make sure the server is running (`./trivia.sh server`)
2. Check your OpenAI API key in the `common/.env` file
3. Ensure all dependencies are installed
4. Check the server logs for error messages

## License

[MIT License](LICENSE)