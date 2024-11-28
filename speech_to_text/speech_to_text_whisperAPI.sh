#!/bin/bash

handle_cleanup() {
    echo -e "\nProcessing recording..."
    trap - INT
}

show_spinner() {
    local process_id=$1
    local delay=0.1
    local spinner_chars='|/-\'
    while kill -0 $process_id 2>/dev/null; do
        local temp=${spinner_chars#?}
        printf " [%c]  " "$spinner_chars"
        local spinner_chars=$temp${spinner_chars%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

send_audio_to_whisper_api() {
    local audio_file_path=$1
    local api_response=$(curl -s -X POST "https://api.openai.com/v1/audio/transcriptions" \
        -H "Authorization: Bearer $OPENAI_API_KEY" \
        -F "file=@$audio_file_path" \
        -F "model=whisper-1")

    local transcription_text=$(echo "$api_response" | jq -r '.text')
    if [ "$transcription_text" != "null" ] && [ -n "$transcription_text" ]; then
        echo
        echo "$transcription_text"
        echo

        if $COPY_TO_CLIPBOARD; then
            echo "$transcription_text" | pbcopy
            echo "Transcription copied to clipboard."
        fi
    else
        echo "No transcription found in response:"
        echo "$api_response"
    fi
}

trap handle_cleanup INT

TEMP_AUDIO="/tmp/temp_recording.wav"
AUDIO_FILE="/tmp/recording.wav"

COPY_TO_CLIPBOARD=false
while getopts "c" opt; do
    case $opt in
        c) COPY_TO_CLIPBOARD=true ;;
        *) echo "Usage: $0 [-c]" >&2; exit 1 ;;
    esac
done

echo "Recording... Press Enter to stop."
echo
if ! command -v sox &> /dev/null; then
    echo "Error: sox is not installed. Please install it first (e.g., 'sudo apt install sox' or 'brew install sox')"
    exit 1
fi

sox -q -d "$TEMP_AUDIO" &
PID=$!

show_spinner $PID &

read -r -p ""

kill $PID 2>/dev/null

echo -e "\nProcessing recording..."

# Get audio duration in seconds using sox
duration=$(sox "$TEMP_AUDIO" -n stat 2>&1 | grep "Length" | awk '{print $3}')
MAX_DURATION=1200  # 20 minutes in seconds

if (( $(echo "$duration > $MAX_DURATION" | bc -l) )); then
    echo "Recording duration (${duration%.*} seconds) exceeds maximum allowed duration of $MAX_DURATION seconds."
    echo "Recording cancelled to prevent excessive API costs."
    rm -f "$TEMP_AUDIO" "$AUDIO_FILE"
    exit 1
fi

sox -q "$TEMP_AUDIO" -r 16000 -c 1 -b 16 "$AUDIO_FILE" > /dev/null 2>&1

if [ -f "$AUDIO_FILE" ] && [ -s "$AUDIO_FILE" ]; then
    echo "Sending audio to Whisper API..."
    send_audio_to_whisper_api "$AUDIO_FILE"
else
    echo "Error: Recording file is empty or not created"
fi

rm -f "$TEMP_AUDIO" "$AUDIO_FILE"
