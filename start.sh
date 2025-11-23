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
    echo "⚠️ .env file not found. Creating one..."
    echo "DEEPSEEK_API_KEY=sk-54caf78ef48e462888301b9a9f6f5656" > .env
    echo "✅ Created .env file with DeepSeek API key"
else
    echo "✅ .env file exists"
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