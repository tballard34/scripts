# Speech-to-Text Tools

A collection of shell scripts for speech-to-text transcription using both OpenAI's Whisper API and local Whisper models.

## Prerequisites

- macOS or Ubuntu/Debian Linux
- Git

## Installation

1. **Run the setup script:**

    ```bash
    ./setup.sh
    ```

    This script will:
    - Install Python 3.11 if not present
    - Install required system dependencies (sox, ffmpeg, jq)
    - Create a Python virtual environment
    - Install Whisper and other Python dependencies
    - Make the transcription scripts executable

## Global Aliases (Optional)

To use these scripts from anywhere in your terminal, add the following aliases to your `~/.zshrc`:

```bash
# Speech-to-text aliases
alias speech_to_text='path/to/speech_to_text_whisperAPI.sh'
alias speech_to_text_local='path/to/speech_to_text_whisperLocal.sh'
```

Replace `path/to` with the actual path to your scripts. For example, if you cloned the repository to your home directory:

```bash
# Speech-to-text aliases
alias speech_to_text='$HOME/speech-to-text/speech_to_text_whisperAPI.sh'
alias speech_to_text_local='$HOME/speech-to-text/speech_to_text_whisperLocal.sh'
```

After adding the aliases:
1. Save the file
2. Reload your shell configuration:
   ```bash
   source ~/.zshrc
   ```

Now you can use the commands globally:

```bash
# API version
OPENAI_API_KEY=your_api_key speech_to_text -c

# Local version
speech_to_text_local -c -t
```

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
