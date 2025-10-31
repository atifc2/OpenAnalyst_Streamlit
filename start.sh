#!/bin/bash

# ----------------------------
# Open Analyst MVP Startup Script
# FIXED: Handles Anaconda conflicts
# ----------------------------

echo "🚀 Starting Open Analyst MVP setup..."

# 0. Deactivate any conda environment
if command -v conda &> /dev/null; then
    echo "Deactivating Anaconda/Miniconda..."
    conda deactivate 2>/dev/null || true
fi

# 1. Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    # Use system Python, not Anaconda Python
    /usr/bin/python3 -m venv venv
fi

# 2. Activate the environment
echo "Activating virtual environment..."
source venv/bin/activate

# 3. Verify we're using the right Python
echo "Using Python from: $(which python)"
echo "Python version: $(python --version)"

# 4. Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# 5. Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# 6. Verify critical packages
echo "Verifying package versions..."
python -c "import numpy; import pandas; print(f'NumPy: {numpy.__version__}'); print(f'Pandas: {pandas.__version__}')"

# 7. Launch Streamlit app
echo "Launching Streamlit app..."
streamlit run app.py

# ----------------------------
# Notes:
# - This script now deactivates conda before creating venv
# - Uses /usr/bin/python3 to avoid Anaconda's Python
# - Ensures Ollama is installed and your Llama3 model is available locally
# - For Windows, replace 'source venv/bin/activate' with:
#       venv\Scripts\activate
# ----------------------------
echo "✅ Open Analyst MVP setup complete!"