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

# 1. Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️ .env file not found. Creating template..."
    echo "GEMINI_API_KEY=your_api_key_here" > .env
    echo "✅ Created .env template. Replace placeholder with your real Gemini API key."
else
    echo "✅ .env file exists"
fi

# Validate key is configured (not placeholder/empty)
gemini_api_key=$(grep '^GEMINI_API_KEY=' .env | head -n 1 | cut -d'=' -f2-)
if [ -z "$gemini_api_key" ] || [ "$gemini_api_key" = "your_api_key_here" ]; then
    echo "❌ GEMINI_API_KEY is missing or still a placeholder in .env"
    echo "Please update .env with your real Gemini API key before running the app."
    exit 1
fi

# 2. Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    /usr/bin/python3 -m venv venv
fi

# 3. Activate the environment
echo "Activating virtual environment..."
source venv/bin/activate

# 4. Upgrade pip and install dependencies
echo "Upgrading pip and installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 5. Launch Streamlit app
echo "🚀 Launching Streamlit app..."
streamlit run app.py

echo "✅ Open Analyst MVP setup complete!"