#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$SCRIPT_DIR/.venv"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Python 3.11
install_python311() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Installing Python 3.11 using Homebrew..."
        brew install python@3.11
        brew link python@3.11
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "Installing Python 3.11..."
        sudo apt update
        sudo apt install -y software-properties-common
        sudo add-apt-repository -y ppa:deadsnakes/ppa
        sudo apt update
        sudo apt install -y python3.11 python3.11-venv
    else
        echo "Unsupported operating system"
        exit 1
    fi
}

# Install system dependencies based on OS
install_system_deps() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Installing system dependencies using Homebrew..."
        if ! command_exists brew; then
            echo "Homebrew not found. Please install Homebrew first."
            exit 1
        fi
        brew install sox ffmpeg jq
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "Installing system dependencies using apt..."
        sudo apt update
        sudo apt install -y sox ffmpeg jq
    else
        echo "Unsupported operating system"
        exit 1
    fi
}

# Create and setup virtual environment
setup_venv() {
    echo "Setting up virtual environment..."
    # First verify we're using Python 3.11
    if ! command -v python3.11 >/dev/null 2>&1; then
        echo "Python 3.11 not found in PATH"
        exit 1
    fi
    
    if [ ! -d "$VENV_DIR" ]; then
        python3.11 -m venv "$VENV_DIR"
    fi
    source "$VENV_DIR/bin/activate"
    
    # Verify we're using the correct Python version
    PYTHON_VERSION=$(python --version)
    if [[ ! $PYTHON_VERSION == *"3.11"* ]]; then
        echo "Wrong Python version in virtual environment: $PYTHON_VERSION"
        exit 1
    fi
    
    pip install --upgrade pip
    pip install openai-whisper ffmpeg-python
}

# Make scripts executable
make_executable() {
    echo "Making scripts executable..."
    chmod +x "$SCRIPT_DIR/speech_to_text_whisperLocal.sh"
    chmod +x "$SCRIPT_DIR/speech_to_text_whisperAPI.sh"
}

# Main installation process
echo "Starting installation..."

# Install Python 3.11
install_python311

# Check for Python 3.11 specifically
if ! command -v python3.11 >/dev/null 2>&1; then
    echo "Failed to install Python 3.11. Please install it manually."
    exit 1
fi

# Install system dependencies
install_system_deps

# Setup virtual environment and install Python packages
setup_venv

# Make scripts executable
make_executable

echo "Installation complete! You can now use the speech-to-text tools."
echo "Remember to activate the virtual environment with:"
echo "source $VENV_DIR/bin/activate"
