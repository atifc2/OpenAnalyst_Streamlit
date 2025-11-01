#!/bin/bash

# ----------------------------
# Open Analyst MVP Startup Script
# ----------------------------

echo "🚀 Starting Open Analyst MVP setup..."

# 0. Deactivate any conda environment
if command -v conda &> /dev/null; then
    echo "Deactivating Anaconda/Miniconda..."
    conda deactivate 2>/dev/null || true
fi

# 1. Check for Ollama
echo "🔍 Checking for Ollama installation..."
if ! command -v ollama &> /dev/null; then
    echo "⚙️ Ollama not found. Installing Ollama..."

    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS install
        curl -fsSL https://ollama.com/download/Ollama-darwin.zip -o ollama.zip
        unzip ollama.zip -d /Applications/Ollama
        rm ollama.zip
        echo "✅ Ollama installed (macOS)"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux install
        curl -fsSL https://ollama.com/install.sh | sh
        echo "✅ Ollama installed (Linux)"
    else
        echo "❌ Unsupported OS for automatic Ollama install."
        echo "Please manually install from https://ollama.com/download"
        exit 1
    fi
else
    echo "✅ Ollama already installed."
fi

# 2. Ensure model is available
MODEL_NAME="llama3"
echo "🔍 Checking for Ollama model: $MODEL_NAME ..."
if ! ollama list | grep -q "$MODEL_NAME"; then
    echo "📦 Pulling Ollama model: $MODEL_NAME ..."
    ollama pull $MODEL_NAME
else
    echo "✅ Model $MODEL_NAME already available."
fi

# 3. Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    /usr/bin/python3 -m venv venv
fi

# 4. Activate the environment
echo "Activating virtual environment..."
source venv/bin/activate

# 5. Upgrade pip and install dependencies
echo "Upgrading pip and installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 6. Launch Streamlit app
echo "🚀 Launching Streamlit app..."
streamlit run app.py

echo "✅ Open Analyst MVP setup complete!"
