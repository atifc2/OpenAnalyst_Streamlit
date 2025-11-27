# OpenAnalyst - Testing Checklist

**Testing Date:** November 23, 2025  
**Version:** MVP v2.0 (Post-UX Improvements)  
**URL:** http://localhost:8501

---

## ✅ Quick Start Test

### 1. Authentication
- [ ] Login page displays professionally
- [ ] Demo credentials work (demo_user / demo123)
- [ ] Can create new account
- [ ] Logout works correctly
- [ ] No deprecation warnings visible

### 2. First Visit Experience
- [ ] Onboarding modal appears for new users
- [ ] 5-step tour is clear and helpful
- [ ] Can skip onboarding
- [ ] Won't show again after completion

---

## ✅ Core Functionality Tests

### 3. Data Upload & Processing
- [ ] Can upload CSV files
- [ ] Can upload XLSX files
- [ ] Multiple files process correctly
- [ ] Sample datasets load (3 available)
- [ ] Data cleaning works (auto-cleanup)
- [ ] Data preview shows in sidebar

### 4. Model Selector
- [ ] Model selector visible in sidebar
- [ ] Shows 5 models (3 Gemini + 2 placeholders)
- [ ] Can switch between Gemini models
- [ ] OpenAI/Claude show "No API Connected" warning
- [ ] Active model indicator displays correctly
- [ ] Switch persists across interactions

### 5. Dataset Management
- [ ] Multiple datasets listed in radio buttons
- [ ] Active dataset shows with ✓ checkmark
- [ ] Switching dataset shows confirmation dialog
- [ ] "Switch & Clear Chat" clears messages
- [ ] Canvas is preserved when switching
- [ ] Cancel button keeps current dataset

---

## ✅ Chat & Analysis Tests

### 6. AI Responses (Results-First)
- [ ] AI leads with results, not methodology
- [ ] No "I will analyze..." or "Let me group..." responses
- [ ] Insights are clear and business-focused
- [ ] Numbers and metrics shown first

### 7. Reasoning Toggle
- [ ] "🔍 Show Reasoning" appears for each response
- [ ] Collapsed by default
- [ ] Expands to show technical details
- [ ] Methodology explained in reasoning section
- [ ] Works for all AI responses

### 8. Charts & Visualizations
- [ ] Charts generate correctly
- [ ] Chart type selector appears
- [ ] Can switch between bar/line/scatter/pie
- [ ] Charts display with proper formatting
- [ ] Color and styling look professional

### 9. Suggested Actions
- [ ] Suggested actions appear as buttons
- [ ] Clicking action adds to chat
- [ ] Actions are relevant to analysis
- [ ] Buttons trigger new analysis

---

## ✅ Canvas & Export Tests

### 10. Tab Navigation
- [ ] Three tabs visible: Chat | Data Preview | Canvas
- [ ] Switching tabs works smoothly
- [ ] Content persists across tab switches
- [ ] Active tab highlighted

### 11. Data Preview Tab
- [ ] Shows 4 key metrics (Rows, Columns, Missing, Memory)
- [ ] Full data table displays
- [ ] Table is scrollable and readable
- [ ] Column info expander works
- [ ] Shows types, null counts, unique values

### 12. Canvas Management
- [ ] "📌 Add to Canvas" button works
- [ ] Items added show in Canvas tab
- [ ] Item counter shows correct number
- [ ] Each item displays title + content + chart

### 13. Duplicate Prevention
- [ ] Adding same item twice shows warning
- [ ] Warning says "already in canvas"
- [ ] Duplicate is NOT added
- [ ] Different items can be added

### 14. Canvas Text Visibility
- [ ] Text wraps properly (no truncation)
- [ ] Long text readable with line breaks
- [ ] Background styling visible
- [ ] Border and spacing look good

### 15. New Canvas Button
- [ ] "🆕 New Canvas" button visible
- [ ] Clicking shows confirmation dialog
- [ ] "Yes, Clear" removes all items
- [ ] "Cancel" keeps items
- [ ] Success message appears after clearing

### 16. Finalize Report Button
- [ ] "📋 Finalize Report" button visible
- [ ] Only shows when canvas has items
- [ ] Clicking switches to Report Mode
- [ ] Can navigate back to Workshop

---

## ✅ Export Tests

### 17. PDF Export
- [ ] "📄 Download PDF Report" button works
- [ ] File downloads as .pdf (not .md)
- [ ] PDF opens correctly
- [ ] Contains all canvas items
- [ ] Charts embedded as images
- [ ] Text formatted properly
- [ ] Page breaks between items
- [ ] Metadata (timestamp, dataset) included

### 18. HTML Export
- [ ] "🌐 Download HTML Report" button works
- [ ] File downloads as .html
- [ ] HTML opens in browser
- [ ] Professional styling with gradients
- [ ] Charts are INTERACTIVE (not static)
- [ ] Can hover/zoom charts
- [ ] All content readable

### 19. Export Options
- [ ] "Include timestamps" checkbox works
- [ ] Timestamps appear when checked
- [ ] Timestamps hidden when unchecked
- [ ] Both export options work together

---

## ✅ Error Handling Tests

### 20. API Quota Errors
- [ ] Hit quota by making many requests rapidly
- [ ] Error message is clear and helpful
- [ ] Shows: "⚠️ API Quota Exceeded for [model]"
- [ ] Suggests alternative models
- [ ] Shows what user can do
- [ ] "Switch model" action suggested
- [ ] Error doesn't crash the app

### 21. Other API Errors
- [ ] Rate limit shows: "⏱️ Rate Limit Reached"
- [ ] Auth error shows: "🔑 Authentication Issue"
- [ ] Generic error shows: "❌ Unexpected Error"
- [ ] All errors have reasoning in expander
- [ ] All errors have suggested actions

### 22. Missing Columns Error
- [ ] AI requests non-existent column for chart
- [ ] Shows: "❌ Missing columns: [list]"
- [ ] Shows available columns
- [ ] Doesn't crash app
- [ ] User can continue chatting

---

## ✅ Search Feature Tests

### 23. Find Similar Analyses
- [ ] Feature renamed from "Search Past Analyses"
- [ ] Title is "🔍 Find Similar Analyses"
- [ ] Help section expands
- [ ] Help text is clear with examples
- [ ] Search box has helpful placeholder
- [ ] Searching works (if vector DB active)
- [ ] Results show match percentage
- [ ] Results show dataset source
- [ ] Results show timestamp

---

## ✅ Performance & UX Tests

### 24. Responsiveness
- [ ] App loads in < 3 seconds
- [ ] No visible lag when switching tabs
- [ ] Charts render quickly (< 2 seconds)
- [ ] File upload feedback is clear
- [ ] Spinner shows during AI processing

### 25. Visual Design
- [ ] Colors are professional (purple/blue theme)
- [ ] Icons enhance understanding
- [ ] Spacing is consistent
- [ ] No text overlaps
- [ ] Buttons are clearly labeled
- [ ] Help text is visible but not intrusive

### 26. User Guidance
- [ ] Empty canvas shows helpful message
- [ ] Empty chat shows "Generate Initial Summary" button
- [ ] All features have hover tooltips
- [ ] Error messages are actionable
- [ ] Success messages are clear

---

## ✅ Edge Cases

### 27. No Data Uploaded
- [ ] App shows: "Please upload a file to begin"
- [ ] No crashes or errors
- [ ] Sample datasets available
- [ ] Can load sample data instead

### 28. Large Datasets
- [ ] Upload 1000+ row dataset
- [ ] Processing completes without error
- [ ] Memory metric displays correctly
- [ ] Charts render properly
- [ ] Export works with large data

### 29. Multiple Canvas Items
- [ ] Add 10+ items to canvas
- [ ] All items display
- [ ] Scrolling works
- [ ] Performance remains good
- [ ] Export includes all items

### 30. Session Persistence
- [ ] Upload data
- [ ] Add to canvas
- [ ] Refresh page
- [ ] Session data preserved (if not cleared)
- [ ] No unexpected state loss

---

## 🐛 Known Issues (Non-Critical)

1. **Python 3.9 Warning** - Expected, user can upgrade Python later
2. **Watchdog Warning** - Optional, improves auto-reload performance
3. **Importlib.metadata Error** - Non-critical vector DB version check
4. **IDE Import Warnings** - Pylance can't resolve venv, packages installed correctly

---

## ✅ Deployment Checklist

Before sharing with users:

- [ ] All environment variables set (.env file)
- [ ] config.yaml in .gitignore
- [ ] No sensitive data committed
- [ ] README updated with new features
- [ ] All dependencies in requirements.txt
- [ ] start.sh script works
- [ ] Sample datasets available
- [ ] Demo credentials documented

---

## 📊 Test Results Summary

**Total Tests:** 30 categories  
**Pass:** ___ / 30  
**Fail:** ___ / 30  
**Notes:** ___________

---

## 🚀 User Acceptance Criteria

App is ready for testers when:

1. ✅ All Phase 1-6 features working
2. ✅ No critical bugs or crashes
3. ✅ PDF export generates correctly
4. ✅ HTML export works with interactive charts
5. ✅ Error messages are helpful
6. ✅ UI is professional and clean
7. ✅ Documentation is complete

---

## 📝 Feedback Collection

When testing with users, ask:

1. **First Impression:** Does the interface feel professional?
2. **AI Responses:** Are the insights clear and useful?
3. **Canvas Workflow:** Is it intuitive to build reports?
4. **Export Quality:** Are PDFs/HTML suitable for sharing?
5. **Error Experience:** When errors occur, is it clear what to do?
6. **Tab Layout:** Does the 3-tab design work better than side-by-side?
7. **Model Switching:** Is it clear how to handle quota limits?
8. **Overall:** What's the #1 thing to improve next?

---

## 🎯 Success Metrics

**Quantitative:**
- Time to first insight: < 2 minutes
- Time to export report: < 30 seconds
- Error recovery success: > 90%
- Feature discovery: > 80% find canvas/export

**Qualitative:**
- Users describe app as "professional"
- Users understand results-first responses
- Users successfully recover from quota errors
- Users prefer new layout to old

---

**Testing Status:** Ready to begin  
**Tester Instructions:** Follow checklist top to bottom, mark each item, note any issues
