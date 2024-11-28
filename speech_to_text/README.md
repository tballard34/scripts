# Speech-to-Text Tools

A collection of shell scripts for speech-to-text transcription using both OpenAI's Whisper API and local Whisper models.

## Prerequisites

- **sox**: Sound processing tool
- **ffmpeg**: Audio and video converter
- **Python 3.7 or higher**
- **pip**: Python package installer
- **Whisper**: OpenAI's Whisper (for local transcription)
- **curl**: For API requests (API version only)
- **jq**: For JSON processing (API version only)

## Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/tballard34/speech-to-text-tools.git
    cd speech-to-text-tools
    ```

2. **Make the scripts executable:**

    ```bash
    chmod +x speech_to_text_whisperLocal.sh
    chmod +x speech_to_text_whisperAPI.sh
    ```

3. **Install dependencies:**

    - **For macOS:**

        ```bash
        brew install sox ffmpeg jq
        pip3 install --upgrade openai-whisper
        ```

    - **For Ubuntu/Debian:**

        ```bash
        sudo apt update
        sudo apt install sox ffmpeg jq
        pip3 install --upgrade openai-whisper
        ```

    Note: The `pip3 install --upgrade openai-whisper` command will install Whisper and its dependencies, including PyTorch.

## Usage

### Local Whisper Version

Run the script:

```bash
./speech_to_text_whisperLocal.sh [-c] [-t] [-l]
```

**Options:**

- `-c`: Copy the transcription to the clipboard
- `-t`: Use the tiny model (faster, less accurate)
- `-l`: Use the large model (slower, more accurate)

**Example:**

Transcribe using the local tiny model and copy to clipboard:

```bash
./speech_to_text_whisperLocal.sh -c -t
```

### API Version

Run the script with your OpenAI API key:

```bash
OPENAI_API_KEY=your_api_key ./speech_to_text_whisperAPI.sh [-c]
```

**Options:**

- `-c`: Copy the transcription to the clipboard

**Example:**

Transcribe using the API and copy to clipboard:

```bash
OPENAI_API_KEY=your_api_key ./speech_to_text_whisperAPI.sh -c
```

Note: Replace `your_api_key` with your actual OpenAI API key.
