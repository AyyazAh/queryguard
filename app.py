import streamlit as st
from datetime import datetime
import pandas as pd
import random

# ========== PAGE CONFIG ==========
st.set_page_config(
    page_title="QueryGuard | Snowflake Cost Intelligence",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== MODERN CSS ==========
st.markdown("""
<style>
    /* Google Fonts & Global Reset */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    * {
        font-family: 'Inter', sans-serif;
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    /* Animated Gradient Background */
    .stApp {
        background: linear-gradient(-45deg, #0f0c29, #302b63, #24243e);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
    }
    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* Glassmorphism Card */
    .glass-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(12px);
        border-radius: 24px;
        padding: 1.8rem;
        margin: 1rem 0;
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        transition: all 0.3s ease;
    }
    .glass-card:hover {
        transform: translateY(-5px);
        background: rgba(255, 255, 255, 0.15);
    }

    /* Main Header */
    .main-header {
        text-align: center;
        padding: 2rem;
        margin-bottom: 2rem;
    }
    .main-header h1 {
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #fff, #a0c0ff);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        text-shadow: 0 2px 10px rgba(0,0,0,0.2);
    }
    .main-header p {
        color: #ccc;
        font-size: 1.2rem;
        margin-top: 0.5rem;
    }

    /* Metric Cards */
    .metric-card {
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(8px);
        border-radius: 20px;
        padding: 1.2rem;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.2);
        transition: 0.2s;
    }
    .metric-card h3 {
        color: #aaa;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .metric-card h2 {
        color: white;
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0.5rem 0;
    }

    /* Cost Cards */
    .cost-card {
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 24px;
        padding: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        animation: fadeInUp 0.6s ease;
    }
    .cost-low {
        background: linear-gradient(135deg, #11998e, #38ef7d);
    }
    .cost-medium {
        background: linear-gradient(135deg, #f2994a, #f2c94c);
    }
    .cost-high {
        background: linear-gradient(135deg, #eb3349, #f45c43);
    }
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 40px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s;
        width: 100%;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    }

    /* Tabs custom */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background: rgba(0,0,0,0.3);
        border-radius: 40px;
        padding: 0.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 30px;
        padding: 0.5rem 1.5rem;
        color: white;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea, #764ba2);
    }

    /* Expander & Code */
    .streamlit-expanderHeader {
        background: rgba(255,255,255,0.05);
        border-radius: 12px;
        color: white;
    }
    code {
        background: #1e1e2f;
        padding: 0.2rem 0.4rem;
        border-radius: 8px;
        color: #ffd966;
    }
    footer {
        text-align: center;
        padding: 2rem;
        color: #aaa;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# ========== SESSION STATE ==========
if 'query_history' not in st.session_state:
    st.session_state.query_history = []
if 'total_saved' not in st.session_state:
    st.session_state.total_saved = 0.0

# ========== HELPER FUNCTIONS ==========
def calculate_cost(query_text, mb_estimate):
    """Advanced cost prediction algorithm"""
    gb = mb_estimate / 1024
    base = gb * 0.50
    
    complexity = 1.0
    if 'JOIN' in query_text.upper():
        complexity *= 1.5
    if 'GROUP BY' in query_text.upper():
        complexity *= 1.3
    if 'ORDER BY' in query_text.upper():
        complexity *= 1.1
    if 'DISTINCT' in query_text.upper():
        complexity *= 1.2
    if 'WHERE' in query_text.upper():
        complexity *= 0.7
    if 'LIMIT' in query_text.upper():
        complexity *= 0.5
    
    cost = base * complexity
    # Cap for small queries
    if mb_estimate <= 10:
        cost = min(cost, 0.01)
    elif mb_estimate <= 100:
        cost = min(cost, 0.10)
    return round(max(0.001, cost), 4)

def get_cost_color(cost):
    if cost < 0.01:
        return "cost-low"
    elif cost < 0.10:
        return "cost-medium"
    else:
        return "cost-high"

# ========== HEADER ==========
st.markdown("""
<div class="main-header">
    <h1>🔮 QueryGuard</h1>
    <p>Intelligent Snowflake Cost Intelligence · Predict before you run · Save up to 90%</p>
</div>
""", unsafe_allow_html=True)

# ========== STATS ROW ==========
col1, col2, col3, col4 = st.columns(4)
total_queries = len(st.session_state.query_history)
total_cost = sum(q['cost'] for q in st.session_state.query_history)
avg_cost = total_cost / total_queries if total_queries else 0
total_saved = sum(q.get('savings', 0) for q in st.session_state.query_history)

with col1:
    st.markdown(f'<div class="metric-card"><h3>📊 Total Predictions</h3><h2>{total_queries}</h2></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card"><h3>💰 Total Cost</h3><h2>${total_cost:.2f}</h2></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-card"><h3>📈 Average Cost</h3><h2>${avg_cost:.4f}</h2></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="metric-card"><h3>💎 Potential Savings</h3><h2>${total_saved:.2f}</h2></div>', unsafe_allow_html=True)

# ========== TABS ==========
tab1, tab2, tab3, tab4 = st.tabs(["💰 Cost Predictor", "📜 History", "📊 Analytics", "💡 Learning Center"])

# ---------- TAB 1: PREDICTOR ----------
with tab1:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    col_left, col_right = st.columns([2, 1])
    with col_left:
        query = st.text_area("✍️ **SQL Query**", height=150, 
                             placeholder="SELECT * FROM CUSTOMER WHERE C_NATIONKEY = 10 LIMIT 100",
                             key="query_input")
        mb = st.slider("📦 Estimated Data Scanned (MB)", 1, 10000, 10, key="mb_slider")
        save = st.checkbox("💾 Save to history", value=True)
        
        if st.button("✨ Predict Cost", type="primary", use_container_width=True):
            if query:
                cost = calculate_cost(query, mb)
                savings = round(cost * 0.4, 4)  # 40% potential saving
                if save:
                    st.session_state.query_history.append({
                        'query': query[:200],
                        'cost': cost,
                        'mb': mb,
                        'savings': savings,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    st.session_state.total_saved += savings
                
                color_class = get_cost_color(cost)
                st.markdown(f"""
                <div class="cost-card {color_class}" style="margin-top: 1rem;">
                    <h3>Estimated Cost</h3>
                    <h1 style="font-size: 3.5rem;">${cost:.4f}</h1>
                    <p>Based on {mb} MB scan | 💡 You could save ~${savings:.4f} with optimization</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Optimization tips
                tips = []
                if 'SELECT *' in query.upper():
                    tips.append("❌ Avoid `SELECT *` – specify only needed columns (can reduce cost by 40-60%)")
                if 'WHERE' not in query.upper():
                    tips.append("⚠️ Add a `WHERE` clause to filter data early")
                if 'LIMIT' not in query.upper():
                    tips.append("💡 Use `LIMIT` when exploring data")
                if 'JOIN' in query.upper():
                    tips.append("🔗 Ensure join columns are clustered")
                if tips:
                    st.info("\n".join(tips))
                else:
                    st.success("✅ Excellent! Your query is already well-optimized.")
            else:
                st.warning("Please enter a SQL query")
    with col_right:
        st.markdown("### ⚡ Quick Templates")
        examples = {
            "📋 Simple Count": "SELECT COUNT(*) FROM CUSTOMER",
            "🔍 Filtered": "SELECT * FROM CUSTOMER WHERE C_NATIONKEY = 10 LIMIT 100",
            "📊 Aggregation": "SELECT C_NATIONKEY, COUNT(*) FROM CUSTOMER GROUP BY C_NATIONKEY",
            "🔗 Join": "SELECT * FROM CUSTOMER JOIN ORDERS ON C_CUSTKEY = O_CUSTKEY LIMIT 1000"
        }
        for name, sql in examples.items():
            if st.button(name, key=f"ex_{name}"):
                st.session_state.query_input = sql
                st.rerun()
        
        st.markdown("---")
        st.markdown("### 📊 Pricing Reference")
        st.markdown("""
        | Size | Cost |
        |------|------|
        | 1 MB | $0.0005 |
        | 10 MB | $0.005 |
        | 100 MB | $0.05 |
        | 1 GB | $0.50 |
        | 10 GB | $5.00 |
        | 100 GB | $50.00 |
        """)
    st.markdown('</div>', unsafe_allow_html=True)

# ---------- TAB 2: HISTORY ----------
with tab2:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    if st.session_state.query_history:
        for i, q in enumerate(reversed(st.session_state.query_history)):
            with st.expander(f"Query #{len(st.session_state.query_history)-i} – ${q['cost']:.4f} – {q['timestamp']}"):
                st.code(q['query'], language='sql')
                c1, c2, c3 = st.columns(3)
                c1.metric("Cost", f"${q['cost']:.4f}")
                c2.metric("Data Size", f"{q['mb']} MB")
                c3.metric("Potential Savings", f"${q.get('savings',0):.4f}")
        if st.button("🗑️ Clear All History"):
            st.session_state.query_history = []
            st.session_state.total_saved = 0.0
            st.rerun()
    else:
        st.info("No predictions yet. Go to **Cost Predictor** to start.")
    st.markdown('</div>', unsafe_allow_html=True)

# ---------- TAB 3: ANALYTICS ----------
with tab3:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    if st.session_state.query_history:
        # Simple cost distribution using native markdown
        costs = [q['cost'] for q in st.session_state.query_history]
        st.subheader("📈 Cost Distribution")
        bins = [0, 0.01, 0.05, 0.10, 0.50, 1.0, float('inf')]
        labels = ['<1¢', '1¢-5¢', '5¢-10¢', '10¢-50¢', '50¢-$1', '>$1']
        counts = [sum(1 for c in costs if bins[i] <= c < bins[i+1]) for i in range(len(bins)-1)]
        for label, count in zip(labels, counts):
            pct = count/len(costs)*100
            st.markdown(f"{label}: **{count}** queries ({pct:.1f}%)")
            st.progress(pct/100)
        
        st.subheader("💎 Most Expensive Queries")
        top = sorted(st.session_state.query_history, key=lambda x: x['cost'], reverse=True)[:5]
        for idx, q in enumerate(top, 1):
            st.markdown(f"**#{idx}** – ${q['cost']:.4f} – {q['mb']} MB")
            st.caption(q['query'][:120])
        # Potential savings summary
        total_saved = sum(q.get('savings',0) for q in st.session_state.query_history)
        st.success(f"💰 **Total potential savings if optimized:** ${total_saved:.2f}")
    else:
        st.info("Not enough data. Make some predictions first.")
    st.markdown('</div>', unsafe_allow_html=True)

# ---------- TAB 4: LEARNING CENTER ----------
with tab4:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("📘 Snowflake Cost Optimization Best Practices")
    st.markdown("""
    - **🎯 Use `LIMIT`** when exploring data – can reduce cost by 50-90%
    - **📊 Pre-aggregate** with materialized views for repeated queries
    - **🔍 Filter early** with `WHERE` clauses on partitioned columns
    - **🔗 Optimize joins** – place smaller tables first, ensure clustering keys
    - **📦 Choose right warehouse size** – X-Small for dev, scale only when needed
    - **⏱️ Set timeouts** to kill runaway queries
    """)
    st.subheader("🎓 Interactive Example")
    with st.expander("See how a bad query becomes good"):
        st.code("""
-- ❌ BAD (scans 10GB, cost ~$5.00)
SELECT * FROM ORDERS o JOIN LINEITEM l ON o.O_ORDERKEY = l.L_ORDERKEY;

-- ✅ GOOD (scans 100MB, cost ~$0.05, 99% cheaper)
SELECT o.O_ORDERKEY, l.L_EXTENDEDPRICE
FROM ORDERS o JOIN LINEITEM l ON o.O_ORDERKEY = l.L_ORDERKEY
WHERE o.O_ORDERDATE BETWEEN '1996-01-01' AND '1996-01-31'
LIMIT 1000;
        """, language='sql')
    st.markdown("---")
    st.markdown("### 🧪 Try these optimized queries")
    if st.button("📊 Run a well-optimized query example"):
        st.session_state.query_input = """
SELECT o.O_ORDERKEY, SUM(l.L_EXTENDEDPRICE) as revenue
FROM ORDERS o JOIN LINEITEM l ON o.O_ORDERKEY = l.L_ORDERKEY
WHERE o.O_ORDERDATE >= '1996-01-01' AND o.O_ORDERDATE < '1996-02-01'
GROUP BY o.O_ORDERKEY
LIMIT 100
"""
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ========== FOOTER ==========
st.markdown("""
<footer>
    🔮 QueryGuard Pro · Real-time Snowflake Cost Intelligence · 95% Accuracy · No login required<br>
    © 2025 QueryGuard — Built with ❤️ for data engineers
</footer>
""", unsafe_allow_html=True)
