# 🚀 Smart AI Optimization Plan - Cost-Effective Intelligence

**Branch:** `feature/smart-ai-optimization`  
**Goal:** Make AI smarter while reducing API costs by 60-70%  
**Date:** November 24, 2025

---

## 🎯 **Core Philosophy:**

> **"Use AI where it adds value, skip it where pandas is faster and cheaper!"**

**Current Problem:**
- Every question → API call to Gemini ($$$)
- Simple queries waste API tokens
- No learning from past analyses
- Generic responses for all data types

**Solution:**
- **3-tier query system:** Simple → Cached → AI
- **Domain intelligence:** Detect data type, adjust AI behavior
- **Vector-first:** Check semantic cache before calling API
- **Smart charts:** Rule-based selection for common patterns

---

## 💰 **API Cost Optimization Strategy**

### **Tier 1: NO AI NEEDED (70% of queries) ✅ FREE**

**Simple Aggregation Queries:**
```python
SIMPLE_QUERY_PATTERNS = {
    # Count patterns
    r"how many .* by (.+)": lambda df, col: df[col].value_counts(),
    r"count .* by (.+)": lambda df, col: df[col].value_counts(),
    r"show .* count": lambda df, col: df[col].value_counts(),
    
    # Sum patterns
    r"total (.+) by (.+)": lambda df, val, grp: df.groupby(grp)[val].sum(),
    r"sum of (.+)": lambda df, col: df[col].sum(),
    
    # Average patterns
    r"average (.+) by (.+)": lambda df, val, grp: df.groupby(grp)[val].mean(),
    r"mean (.+)": lambda df, col: df[col].mean(),
    
    # Top N patterns
    r"top (\d+) (.+)": lambda df, n, col: df[col].value_counts().head(int(n)),
    r"bottom (\d+) (.+)": lambda df, n, col: df[col].value_counts().tail(int(n)),
}
```

**Examples:**
- "How many orders by region?" → `df['region'].value_counts()` ✅ NO API CALL
- "Total revenue by product?" → `df.groupby('product')['revenue'].sum()` ✅ NO API CALL
- "Top 10 customers?" → `df['customer'].value_counts().head(10)` ✅ NO API CALL

**Savings:** ~$0.002 per query × 1000 queries/day = **$2/day saved** ($60/month)

---

### **Tier 2: VECTOR DB CACHE (20% of queries) ✅ CHEAP**

**Semantic Cache Check:**
```python
def check_semantic_cache(query, dataset_name):
    """Check if we already answered this before"""
    vector_store = get_vector_store()
    
    # Search for similar past queries
    similar = vector_store.search_similar_messages(
        query=query,
        dataset_name=dataset_name,
        limit=3,
        min_score=0.85  # 85% similarity threshold
    )
    
    if similar and similar[0]['score'] > 0.85:
        # Reuse past answer!
        return {
            "content": f"📋 **From past analysis:** {similar[0]['content']}",
            "cached": True,
            "original_query": similar[0]['query'],
            "suggested_actions": generate_followups(similar[0])
        }
    
    return None  # Cache miss, call AI
```

**Examples:**
- User asks: "Show revenue by region"
- Cache finds: "Display sales by location" (87% match)
- **Return cached answer** ✅ NO API CALL

**Cost:** Qdrant API call = ~$0.0001 vs Gemini = ~$0.002
**Savings:** 20× cheaper! (~$0.0018 per query)

---

### **Tier 3: SMART AI CALL (10% of queries) 💰 PAID**

**When to actually call AI:**
- Complex questions: "Analyze customer retention patterns"
- Multi-step queries: "Compare Q1 vs Q2 performance and suggest improvements"
- Open-ended exploration: "What insights can you find?"
- Chart generation: "Create visualization showing..."

**Optimization:**
```python
def smart_ai_call(query, profile, history):
    """Optimized AI call with context management"""
    
    # 1. Trim history (only last 4 messages, not all)
    recent_history = history[-4:] if len(history) > 4 else history
    
    # 2. Compress profile (remove sample data if not needed)
    if not is_data_dependent_query(query):
        profile = compress_profile(profile)  # Remove sample rows
    
    # 3. Use streaming (show partial results)
    response = client.stream_message(
        messages=build_messages(query, profile, recent_history)
    )
    
    return response
```

**Savings:** 
- Trimmed history: 50% fewer tokens
- Compressed profile: 30% fewer tokens
- Streaming: Better UX, same cost

---

## 🎯 **Domain Intelligence System**

### **Auto-Detect Data Type:**

```python
def detect_data_domain(df):
    """Detect what kind of data this is"""
    
    columns = set(df.columns.str.lower())
    
    # Define domain patterns
    DOMAIN_PATTERNS = {
        "sales": [
            {"keywords": ['revenue', 'sales', 'orders', 'products'], "weight": 3},
            {"keywords": ['price', 'quantity', 'discount'], "weight": 2},
            {"keywords": ['customer', 'date', 'region'], "weight": 1}
        ],
        "marketing": [
            {"keywords": ['campaign', 'impressions', 'clicks', 'conversions'], "weight": 3},
            {"keywords": ['cost', 'cpc', 'ctr', 'roi'], "weight": 2},
            {"keywords": ['channel', 'source', 'medium'], "weight": 1}
        ],
        "hr": [
            {"keywords": ['employee', 'salary', 'department', 'hire_date'], "weight": 3},
            {"keywords": ['performance', 'rating', 'manager'], "weight": 2},
            {"keywords": ['tenure', 'headcount', 'turnover'], "weight": 1}
        ],
        "financial": [
            {"keywords": ['revenue', 'expense', 'profit', 'loss'], "weight": 3},
            {"keywords": ['budget', 'actual', 'variance', 'forecast'], "weight": 2},
            {"keywords": ['account', 'cost_center', 'gl_code'], "weight": 1}
        ],
        "survey": [
            {"keywords": ['rating', 'score', 'satisfaction', 'feedback'], "weight": 3},
            {"keywords": ['nps', 'response', 'question', 'answer'], "weight": 2},
            {"keywords": ['sentiment', 'comment', 'text'], "weight": 1}
        ]
    }
    
    # Score each domain
    scores = {}
    for domain, patterns in DOMAIN_PATTERNS.items():
        score = 0
        for pattern in patterns:
            matches = len(columns & set(pattern["keywords"]))
            score += matches * pattern["weight"]
        scores[domain] = score
    
    # Return highest scoring domain (or "general" if no clear match)
    best_domain = max(scores, key=scores.get)
    return best_domain if scores[best_domain] >= 3 else "general"
```

---

### **Domain-Specific AI Prompts:**

**Sales Mode:**
```python
SALES_MODE_PROMPT = """
You are analyzing SALES/E-COMMERCE data. Focus on:

KEY METRICS TO HIGHLIGHT:
- Revenue trends (daily/weekly/monthly)
- Top performing products/categories
- Regional performance comparison
- Customer segmentation by value
- Discount impact on sales

CHART PREFERENCES:
- Time series for trends (line charts)
- Bar charts for product/region comparison
- Heatmaps for correlation analysis
- Funnel charts for conversion stages

SUGGESTED QUESTIONS:
- "What products drive the most revenue?"
- "Which regions are growing/declining?"
- "How do discounts affect sales?"
"""
```

**Marketing Mode:**
```python
MARKETING_MODE_PROMPT = """
You are analyzing MARKETING CAMPAIGN data. Focus on:

KEY METRICS TO HIGHLIGHT:
- Campaign ROI and ROAS
- Channel performance comparison
- Conversion funnel drop-offs
- Cost per acquisition trends
- Lead quality indicators

CHART PREFERENCES:
- Funnel charts for conversion stages
- Scatter plots for ROI analysis
- Bar charts for channel comparison
- Trend lines for time-based performance

SUGGESTED QUESTIONS:
- "Which campaigns have the best ROI?"
- "Where are we losing leads in the funnel?"
- "What's our most cost-effective channel?"
"""
```

*(Similar prompts for HR, Financial, Survey modes)*

---

## 📊 **Smart Chart Selection Rules**

### **Chart Decision Tree:**

```python
CHART_SELECTION_RULES = {
    "trend_over_time": {
        "condition": lambda cols: any('date' in str(c).lower() for c in cols),
        "chart_type": "line",
        "x": "date_column",
        "y": "numeric_column"
    },
    "category_comparison": {
        "condition": lambda data: data['unique_x'] < 20,  # Not too many categories
        "chart_type": "bar",
        "x": "category_column",
        "y": "value_column"
    },
    "distribution": {
        "condition": lambda data: data['is_numeric'] and data['unique_values'] > 20,
        "chart_type": "histogram",
        "x": "numeric_column"
    },
    "correlation": {
        "condition": lambda cols: len([c for c in cols if is_numeric(c)]) >= 2,
        "chart_type": "scatter",
        "x": "numeric_column_1",
        "y": "numeric_column_2"
    },
    "part_of_whole": {
        "condition": lambda data: data['unique_x'] < 7,  # Max 7 slices
        "chart_type": "pie",
        "values": "value_column",
        "names": "category_column"
    }
}
```

**Benefits:**
- Consistent chart selection (no random bar charts everywhere!)
- Faster generation (rule-based, no AI needed)
- Better visual insights

---

## 🏗️ **Implementation Plan**

### **Phase 1: Query Classification System** (Week 1)
- [ ] Create `utils/query_classifier.py`
- [ ] Implement simple pattern matching (Tier 1)
- [ ] Add fallback to AI for unmatched queries
- [ ] Test with 100 sample queries
- **Goal:** Route 50% of queries to simple mode

### **Phase 2: Vector Cache Integration** (Week 1)
- [ ] Enhance `utils/vector_db.py` with cache functions
- [ ] Add similarity threshold tuning (0.80-0.90)
- [ ] Implement cache warming (pre-populate common queries)
- [ ] Add cache hit/miss metrics
- **Goal:** 20% cache hit rate

### **Phase 3: Domain Detection** (Week 2)
- [ ] Create `utils/domain_detector.py`
- [ ] Implement scoring algorithm
- [ ] Add domain-specific prompts folder: `prompts/domains/`
- [ ] Create 5 mode files (sales, marketing, hr, financial, survey)
- **Goal:** 90% accurate domain detection

### **Phase 4: Smart Chart Engine** (Week 2)
- [ ] Create `utils/smart_charts.py`
- [ ] Implement rule-based chart selection
- [ ] Add chart templates for each domain
- [ ] Override AI chart suggestions with smart rules
- **Goal:** Better charts, less AI calls

### **Phase 5: UI/UX Updates** (Week 3)
- [ ] Move Vector Search to prominent position (before AI Stats)
- [ ] Add "Similar Past Analyses" widget
- [ ] Show domain mode indicator (🏪 Sales Mode)
- [ ] Add "Query Type" badge (Simple/Cached/AI)
- [ ] Show API cost savings counter
- **Goal:** Transparency and engagement

### **Phase 6: Metrics & Optimization** (Week 3)
- [ ] Add API call tracking
- [ ] Measure cost savings (before/after)
- [ ] A/B test cache thresholds
- [ ] Tune domain detection weights
- **Goal:** 60-70% API cost reduction

---

## 📈 **Expected Results**

### **Cost Savings:**
```
BEFORE:
- 1000 queries/day × $0.002/query = $2.00/day = $60/month

AFTER:
- 700 simple queries × $0 = $0
- 200 cached queries × $0.0001 = $0.02/day
- 100 AI queries × $0.002 = $0.20/day
= $0.22/day = $6.60/month

SAVINGS: $53.40/month (89% reduction!) 💰
```

### **Performance:**
- Simple queries: <100ms (instant!)
- Cached queries: <200ms (fast!)
- AI queries: 2-4s (acceptable)

### **User Experience:**
- Faster responses for common questions
- Learn from past analyses (vector memory)
- Smarter suggestions based on data type
- Better chart selection

---

## 🚦 **Success Metrics**

Track in `st.session_state.api_stats`:

```python
{
    "total_queries": 1000,
    "simple_queries": 700,  # 70%
    "cached_queries": 200,  # 20%
    "ai_queries": 100,      # 10%
    
    "api_cost_saved": "$53.40",
    "avg_response_time": "0.8s",
    
    "domain_detected": "sales",
    "domain_confidence": 0.87,
    
    "cache_hit_rate": 0.20,
    "cache_avg_similarity": 0.88
}
```

Display in sidebar:
```
💰 API Savings Today: $1.78 (89%)
⚡ Avg Response: 0.8s
🎯 Cache Hit Rate: 20%
🏪 Mode: Sales (87% confident)
```

---

## 🔧 **Technical Architecture**

### **New Files to Create:**

```
utils/
├── query_classifier.py      # Tier system: Simple/Cached/AI
├── domain_detector.py       # Detect sales/marketing/hr/etc
├── smart_charts.py          # Rule-based chart selection
└── cache_manager.py         # Vector cache optimization

prompts/
└── domains/
    ├── sales_mode.txt
    ├── marketing_mode.txt
    ├── hr_mode.txt
    ├── financial_mode.txt
    └── survey_mode.txt
```

### **Modified Files:**

```
app.py                      # Add domain indicator, query type badges
utils/ai_core.py           # Integrate query classifier
utils/vector_db.py         # Enhance with cache functions
utils/ui_components.py     # Show cache hits, savings counter
```

---

## 🎯 **Key Principles**

1. **AI is expensive, use it wisely** - Skip AI for simple aggregations
2. **Memory is cheaper than compute** - Cache everything possible
3. **Domain knowledge is free** - Use rules for common patterns
4. **Show, don't tell** - Make vector search visible and useful
5. **Measure everything** - Track costs, speed, accuracy

---

## 🚀 **Next Steps**

1. **Review this plan** with team
2. **Prioritize phases** based on impact
3. **Start with Phase 1** (Query Classification) - biggest wins!
4. **Iterate rapidly** - measure, optimize, repeat

**Let's build the smartest, most cost-effective data analyst AI!** 🎉

---

**Questions to Answer:**
- [ ] Should we cache charts too? (Storage vs API cost trade-off)
- [ ] What similarity threshold is optimal? (Test 0.80, 0.85, 0.90)
- [ ] Should we charge users based on query tier? (Free/Premium model)
- [ ] How to handle multi-dataset queries? (Cross-domain analysis)

**Ready to start Phase 1?** 🚦
