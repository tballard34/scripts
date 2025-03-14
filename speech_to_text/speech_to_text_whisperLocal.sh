#!/bin/bash

# Get the script's directory and source the virtual environment
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$SCRIPT_DIR/.venv"

if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "Virtual environment not found. Please run setup.sh first."
    exit 1
fi

source "$VENV_DIR/bin/activate"

# Prerequisite checks
check_prerequisites() {
    local missing_tools=()

    # Check for sox
    if ! command -v sox &> /dev/null; then
        missing_tools+=("sox")
        echo "Error: sox is not installed. Please run setup.sh first."
    fi

    # Check for ffmpeg
    if ! command -v ffmpeg &> /dev/null; then
        missing_tools+=("ffmpeg")
        echo "Error: ffmpeg is not installed. Please run setup.sh first."
    fi

    # Exit if any tools are missing
    if [ ${#missing_tools[@]} -ne 0 ]; then
        echo "Please run setup.sh to install the missing tools and try again."
        exit 1
    fi
}

# Call the prerequisite check function
check_prerequisites

handle_cleanup() {
    echo -e "\nProcessing recording..."
    trap - INT
}

show_spinner() {
    local process_id=$1
    local delay=0.1
    local spinner_chars='|/-\'
    while kill -0 "$process_id" 2>/dev/null; do
        local temp=${spinner_chars#?}
        printf " [%c]  " "$spinner_chars"
        spinner_chars="$temp${spinner_chars%"$temp"}"
        sleep "$delay"
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

send_audio_with_whisper() {
    local audio_file_path=$1
    local transcription_file="/tmp/$(basename "$audio_file_path" .wav).txt"

    # Determine the model to use
    local model="base"
    if [ "$USE_TINY_MODEL" = true ]; then
        model="tiny"
    fi
    if [ "$USE_LARGE_MODEL" = true ]; then
        model="large"
    fi

    echo "Transcribing audio locally with Whisper (using ${model} model)..."

    # Run Whisper from virtual environment
    "$VENV_DIR/bin/whisper" "$audio_file_path" --model "$model" --output_format txt --output_dir /tmp > /dev/null 2>&1

    if [ -f "$transcription_file" ] && [ -s "$transcription_file" ]; then
        transcription_text=$(cat "$transcription_file")
        echo
        echo "$transcription_text"
        echo

        if $COPY_TO_CLIPBOARD; then
            if [[ "$OSTYPE" == "darwin"* ]]; then
                echo "$transcription_text" | pbcopy
                echo "Transcription copied to clipboard."
            elif [[ "$OSTYPE" == "linux-gnu"* ]] && command -v xclip &> /dev/null; then
                echo "$transcription_text" | xclip -selection clipboard
                echo "Transcription copied to clipboard."
            else
                echo "Clipboard functionality not available on this system."
            fi
        fi
    else
        echo "No transcription found in the output."
    fi
}

trap handle_cleanup INT

TEMP_AUDIO="/tmp/temp_recording.wav"
AUDIO_FILE="/tmp/recording.wav"

COPY_TO_CLIPBOARD=false
USE_TINY_MODEL=false
USE_LARGE_MODEL=false

while getopts "ctl" opt; do
    case $opt in
        c) COPY_TO_CLIPBOARD=true ;;
        t) USE_TINY_MODEL=true ;;
        l) USE_LARGE_MODEL=true ;;
        *) echo "Usage: $0 [-c] [-t] [-l]" >&2; exit 1 ;;
    esac
done

echo "Recording... Press Enter to stop."
echo

sox -q -d "$TEMP_AUDIO" &
PID=$!

show_spinner "$PID" &

read -r -p ""

kill "$PID" 2>/dev/null

echo -e "\nProcessing recording..."

sox -q "$TEMP_AUDIO" -r 16000 -c 1 -b 16 "$AUDIO_FILE" > /dev/null 2>&1

if [ -f "$AUDIO_FILE" ] && [ -s "$AUDIO_FILE" ]; then
    send_audio_with_whisper "$AUDIO_FILE"
else
    echo "Error: Recording file is empty or not created"
fi

rm -f "$TEMP_AUDIO" "$AUDIO_FILE"
