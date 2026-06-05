# OpenAnalyst Streamlit

OpenAnalyst is a Streamlit app for uploading CSV/XLSX datasets and exploring them with AI-assisted analysis and charts.

## 1) Download the project

### Option A: Clone with Git (recommended)

```bash
git clone https://github.com/atifc2/OpenAnalyst_Streamlit.git
cd OpenAnalyst_Streamlit
```

### Option B: Download ZIP

1. Open: https://github.com/atifc2/OpenAnalyst_Streamlit
2. Click **Code** → **Download ZIP**
3. Extract the ZIP and open a terminal in the extracted folder

## 2) Requirements

- Python 3.10+ recommended
- A Gemini API key

## 3) Setup environment and install dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 4) Configure API key

Create a `.env` file in the project root:

```bash
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

## 5) Run the app

```bash
streamlit run app.py
```

Then open the local URL shown in terminal (usually `http://localhost:8501`).

## Quick start script

You can also run:

```bash
chmod +x start.sh
./start.sh
```

If you use the script, make sure your `.env` contains `GEMINI_API_KEY`.
