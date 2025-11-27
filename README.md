# 📊 OpenAnalyst

**AI-Powered Data Analysis Platform with Results-First Insights**

OpenAnalyst is a professional-grade data analysis tool that combines powerful AI capabilities with an intuitive interface. Upload your data, ask questions in natural language, and get actionable insights with beautiful visualizations.

---

## ✨ Key Features

### 🤖 AI Analysis
- **Results-First Responses** - Get insights immediately, methodology hidden until needed
- **Multiple Model Support** - Switch between Gemini Flash, Flash-Lite, and Flash-8B
- **Smart Context** - Semantic search finds related past analyses
- **Collapsible Reasoning** - Technical details available but not intrusive

### 📊 Visualizations
- **Dynamic Charts** - Bar, line, scatter, pie, histogram, box plots
- **Interactive Controls** - Switch chart types on the fly
- **Professional Styling** - Publication-ready visualizations
- **High-Resolution Export** - Charts embedded in PDF/HTML exports

### 📌 Canvas Workspace
- **Pin & Organize** - Save insights and charts for later
- **Duplicate Prevention** - Smart detection prevents re-adding same items
- **Multi-Dataset Support** - Canvas persists across dataset switches
- **Clear Management** - New Canvas button with confirmation

### 📄 Professional Exports
- **PDF Reports** - High-res embedded charts, professional formatting
- **HTML Reports** - Interactive Plotly charts, responsive design
- **Metadata Preservation** - Timestamps, dataset sources included
- **One-Click Download** - Export entire analysis in seconds

### 🎨 Clean Interface
- **Tab-Based Layout** - Chat, Data Preview, Canvas in separate tabs
- **Dataset Switching** - Clear confirmation when switching data
- **Active Indicators** - Visual feedback for current dataset/model
- **Helpful Guidance** - Contextual help throughout the app

### 🛡️ Error Handling
- **Graceful Quota Management** - Helpful messages when API limits hit
- **Model Suggestions** - Automatic recommendations for alternatives
- **Clear Error Messages** - No technical jargon, actionable next steps
- **Never Crashes** - Robust error recovery

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+ (3.10+ recommended)
- Gemini API key ([Get one free](https://makersuite.google.com/app/apikey))
- Qdrant Cloud account (optional, for semantic search)

### Installation

1. **Clone the repository:**
```bash
git clone <your-repo-url>
cd OpenAnalyst
```

2. **Create virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables:**
Create a `.env` file:
```env
GEMINI_API_KEY=your_gemini_api_key_here
QDRANT_URL=your_qdrant_url_here (optional)
QDRANT_API_KEY=your_qdrant_key_here (optional)
```

5. **Run the app:**
```bash
chmod +x start.sh
./start.sh
```

Or manually:
```bash
streamlit run app.py
```

6. **Access the app:**
Open http://localhost:8501 in your browser

### Demo Credentials
- **Username:** demo_user
- **Password:** demo123

---

## 📖 User Guide

### Getting Started

1. **Login** - Use demo credentials or create an account
2. **Upload Data** - CSV or XLSX files supported (or try sample datasets)
3. **Ask Questions** - Natural language queries about your data
4. **Pin Insights** - Click "📌 Add to Canvas" on useful responses
5. **Export Report** - Click "📋 Finalize Report" then download PDF/HTML

### Understanding AI Responses

**Results-First Format:**
- Main insights shown immediately
- Numbers and findings first
- Methodology hidden in "🔍 Show Reasoning"

**Example:**
```
✅ Northeast leads with $847K average sales, 23% above company average.

🔍 Show Reasoning (click to expand)
  → Grouped data by region
  → Calculated mean sales per region
  → Compared to overall average
```

### Working with the Canvas

**Adding Items:**
- Click "📌 Add to Canvas" on any AI response
- Both text insights and charts are saved
- Duplicates automatically prevented

**Managing Canvas:**
- Switch to Canvas tab to view all items
- Click 🗑️ to remove individual items
- Click "🆕 New Canvas" to start fresh (with confirmation)
- Click "📋 Finalize Report" to export everything

### Switching Models

If you hit API quota limits:
1. Open sidebar model selector
2. Choose different Gemini model
3. Continue your analysis
4. Your data and canvas are preserved

**Available Models:**
- Gemini Flash - Fast, balanced
- Gemini Flash Lite - Current, free tier
- Gemini Flash-8B - Efficient, lighter
- GPT-4 / Claude - Placeholders (no API connected)

### Exporting Reports

**PDF Export:**
- Professional formatting
- High-resolution chart images (800x500, 2x scale)
- Page breaks between sections
- Metadata included (optional timestamps)

**HTML Export:**
- Interactive Plotly charts
- Responsive design
- Gradient header styling
- Self-contained single file

**Export Options:**
- ✅ Include timestamps - Shows when items were added
- Downloads with timestamp in filename

---

## 🗂️ Project Structure

```
OpenAnalyst/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── start.sh                        # Quick start script
├── .env                           # Environment variables (create this)
├── config.yaml                    # User credentials (auto-generated)
├── prompts/
│   └── system_prompt.txt          # AI system instructions
├── utils/
│   ├── ai_core.py                 # Gemini API integration
│   ├── data_handler.py            # Data cleaning & processing
│   ├── ui_components.py           # Streamlit UI functions
│   ├── auth.py                    # Authentication system
│   ├── onboarding.py              # First-visit tour
│   └── vector_db.py               # Qdrant semantic search
├── sample_*.csv                   # Demo datasets
├── UX_IMPROVEMENTS_SUMMARY.md     # Implementation details
├── TESTING_CHECKLIST.md           # QA checklist
├── IMPLEMENTATION_STATUS.md       # Development status
└── QDRANT_INTEGRATION.md          # Vector DB documentation
```

---

## 🔧 Configuration

### Environment Variables

**Required:**
- `GEMINI_API_KEY` - Your Google Gemini API key

**Optional:**
- `QDRANT_URL` - Qdrant Cloud cluster URL
- `QDRANT_API_KEY` - Qdrant API key

### Authentication

User credentials stored in `config.yaml` (bcrypt hashed passwords)
- Auto-generated on first run
- In `.gitignore` for security
- Demo accounts pre-configured

### Sample Datasets

Three datasets included for testing:
1. **E-commerce Sales** - 650 rows, intentional data quality issues
2. **Customer Survey** - 800 rows, missing values, outliers
3. **Financial Metrics** - 34 months, negative values, impossible rates

---

## 🛠️ Development

### Tech Stack

**Backend:**
- Python 3.9+
- Streamlit 1.50.0
- Google Gemini API
- Pandas 2.2.1

**Visualizations:**
- Plotly 5.18.0
- Kaleido 1.2.0 (chart export)

**Documents:**
- ReportLab 4.4.5 (PDF)
- HTML templates (interactive exports)

**Database:**
- Qdrant Cloud (vector storage)
- Gemini text-embedding-004 (768-dim)

**Authentication:**
- streamlit-authenticator 0.3.1
- bcrypt password hashing

### Running Tests

```bash
# Run with debug mode
streamlit run app.py -- --debug=true

# Run with admin mode
streamlit run app.py -- --admin=true
```

### Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly (see TESTING_CHECKLIST.md)
5. Submit pull request

---

## 📊 Features Roadmap

### ✅ Implemented (MVP v2.0)
- Results-first AI responses
- Collapsible reasoning
- Canvas duplicate prevention
- PDF export with charts
- HTML export with interactive plots
- Model switching
- Graceful error handling
- Tab-based layout
- Dataset switch confirmation
- New canvas management

### 🔜 Coming Soon
- Drag-and-drop canvas reordering
- Export templates (executive, technical)
- Chart customization in exports
- Multi-user collaboration
- Database persistence
- Learning system (user preferences)
- Advanced RAG capabilities

---

## 🐛 Troubleshooting

### PDF Export Issues

**Charts not appearing:**
```bash
pip install --upgrade kaleido reportlab
```

**Chromium download error:**
- Kaleido needs internet on first run
- Downloads chromium automatically
- ~100MB download

### API Errors

**Quota exceeded:**
- Switch to different Gemini model
- Wait a few minutes
- Your data is safe

**Authentication failed:**
- Check GEMINI_API_KEY in .env
- Verify key is valid
- Regenerate if needed

### Import Errors

**Module not found:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**Version conflicts:**
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🤝 Support

**Documentation:**
- UX_IMPROVEMENTS_SUMMARY.md - Feature details
- TESTING_CHECKLIST.md - QA guide
- QDRANT_INTEGRATION.md - Vector DB setup

**Issues:**
- GitHub Issues for bug reports
- Include error messages and steps to reproduce

**Contact:**
- Email: [your-email]
- GitHub: [your-github]

---

## 🙏 Acknowledgments

- Google Gemini for powerful AI capabilities
- Streamlit for amazing framework
- Qdrant for semantic search
- Plotly for beautiful visualizations
- ReportLab for PDF generation

---

**Version:** MVP v2.0 (Post-UX Improvements)  
**Last Updated:** November 23, 2025  
**Status:** ✅ Production Ready
