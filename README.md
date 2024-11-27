# Speech-to-Text Tools

A collection of shell scripts for speech-to-text transcription using both OpenAI's Whisper API and local Whisper models.

## Prerequisites

- `sox` - Sound processing tool
- `whisper` - OpenAI's Whisper (for local transcription)
- `curl` - For API requests (API version only)
- `jq` - For JSON processing (API version only)

## Installation

1. Clone the repository:

bash
git clone https://github.com/yourusername/speech-to-text-tools.git
cd speech-to-text-tools


2. Make the scripts executable:

bash
chmod +x speech_to_text_whisperLocal.sh
chmod +x speech_to_text_whisperAPI.sh

3. Install dependencies:

For macOS:

bash
brew install sox
pip install openai-whisper
brew install jq

For Ubuntu/Debian:

bash
sudo apt install sox
pip install openai-whisper
sudo apt install jq


## Usage

### Local Whisper Version

bash
./speech_to_text_whisperLocal.sh [-c] [-t] [-l]

Options:
- `-c`: Copy transcription to clipboard
- `-t`: Use tiny model
- `-l`: Use large model

### API Version

bash
OPENAI_API_KEY=your_api_key ./speech_to_text_whisperAPI.sh [-c]

Options:
- `-c`: Copy transcription to clipboard

## License

MIT