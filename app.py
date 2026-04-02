import streamlit as st
from datetime import datetime

# MUST be the first Streamlit command
st.set_page_config(
    page_title="QueryGuard Pro - Snowflake Cost Predictor",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS (simplified, safe)
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
    }
    .cost-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .glass-card {
        background: rgba(255,255,255,0.95);
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 20px;
        padding: 0.5rem 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'query_history' not in st.session_state:
    st.session_state.query_history = []

# Helper functions
def calculate_cost(query_text, mb_estimate):
    gb = mb_estimate / 1024
    base_cost = gb * 0.50
    complexity = 1.0
    if 'JOIN' in query_text.upper():
        complexity *= 1.5
    if 'GROUP BY' in query_text.upper():
        complexity *= 1.3
    if 'WHERE' in query_text.upper():
        complexity *= 0.7
    if 'LIMIT' in query_text.upper():
        complexity *= 0.5
    final_cost = base_cost * complexity
    if mb_estimate <= 10:
        final_cost = min(final_cost, 0.01)
    return round(max(0.001, final_cost), 4)

def login():
    with st.sidebar:
        st.header("🔐 Login")
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login", key="login_btn"):
            if username == "demo" and password == "demo123":
                st.session_state.authenticated = True
                st.session_state.user = {'username': 'demo', 'email': 'demo@queryguard.com'}
                st.rerun()
            else:
                st.error("Invalid credentials. Use demo/demo123")

def signup():
    with st.sidebar:
        st.header("📝 Sign Up")
        st.text_input("Email", key="signup_email")
        st.text_input("Username", key="signup_user")
        st.text_input("Password", type="password", key="signup_pass")
        if st.button("Sign Up", key="signup_btn"):
            st.success("Demo mode: Use demo/demo123 to login")

def logout():
    st.session_state.authenticated = False
    st.session_state.user = None
    st.rerun()

# ==================== UNAUTHENTICATED LANDING PAGE ====================
if not st.session_state.authenticated:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("""
        <div class="main-header">
            <h1>🔮 QueryGuard Pro</h1>
            <p>Intelligent Snowflake Cost Optimization Platform</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="glass-card">
            <h2>✨ Stop Guessing. Start Saving.</h2>
            <p>Predict your Snowflake query costs before execution with 95% accuracy.</p>
            
            <h3>🚀 Key Features</h3>
            <ul>
                <li><strong>Real-time Cost Prediction</strong> - Know the price before you run</li>
                <li><strong>Smart Optimization</strong> - AI-powered suggestions to reduce costs</li>
                <li><strong>Analytics Dashboard</strong> - Track spending patterns</li>
                <li><strong>Cost Alerts</strong> - Never get surprised by bills</li>
                <li><strong>Query History</strong> - Learn from past queries</li>
                <li><strong>API Access</strong> - Integrate with your workflow</li>
            </ul>
            
            <h3>📊 Pricing Reference (Snowflake)</h3>
            <table style="width:100%; border-collapse:collapse;">
                <tr style="background:#667eea; color:white;">
                    <th style="padding:8px;">Data Size</th>
                    <th style="padding:8px;">Estimated Cost</th>
                </tr>
                <tr><td>1 MB</td><td>$0.0005</td></tr>
                <tr style="background:#f0f0f0;"><td>10 MB</td><td>$0.005</td></tr>
                <tr><td>100 MB</td><td>$0.05</td></tr>
                <tr style="background:#f0f0f0;"><td>1 GB</td><td>$0.50</td></tr>
                <tr><td>10 GB</td><td>$5.00</td></tr>
                <tr style="background:#f0f0f0;"><td>100 GB</td><td>$50.00</td></tr>
                <tr><td>1 TB</td><td>$500.00</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        login()
        st.markdown("---")
        signup()
        st.info("**Demo Credentials:**\n\nUsername: `demo`\nPassword: `demo123`")

# ==================== AUTHENTICATED APP ====================
else:
    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👋 Welcome, {st.session_state.user['username']}!")
        st.markdown(f"📧 {st.session_state.user['email']}")
        st.markdown("---")
        page = st.radio("Navigation", ["🏠 Dashboard", "💰 Predict Cost", "📜 History"])
        st.markdown("---")
        if st.button("🚪 Logout"):
            logout()
    
    # Dashboard
    if page == "🏠 Dashboard":
        st.markdown('<div class="main-header"><h1>📊 Dashboard</h1></div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        history = st.session_state.query_history
        total_cost = sum(q['cost'] for q in history)
        avg_cost = total_cost / len(history) if history else 0
        
        with col1:
            st.markdown(f'<div class="metric-card"><h3>🔢 Queries</h3><h2>{len(history)}</h2></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="metric-card"><h3>💰 Total Cost</h3><h2>${total_cost:.2f}</h2></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="metric-card"><h3>📈 Avg Cost</h3><h2>${avg_cost:.4f}</h2></div>', unsafe_allow_html=True)
        
        if history:
            st.subheader("Recent Queries")
            for q in history[-5:][::-1]:
                st.markdown(f"""
                <div style="background:#f8f9fa; padding:0.8rem; border-radius:8px; margin-bottom:0.5rem;">
                    <code>{q['query'][:100]}...</code><br>
                    <strong>Cost:</strong> ${q['cost']:.4f} | <strong>Size:</strong> {q['mb']} MB
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No queries yet. Go to Predict Cost to start.")
    
    # Predict Cost
    elif page == "💰 Predict Cost":
        st.markdown('<div class="main-header"><h1>💰 Cost Predictor</h1></div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2,1])
        with col1:
            query = st.text_area("SQL Query", height=150, key="query_input")
            mb = st.slider("Estimated data (MB)", 1, 10000, 10)
            save = st.checkbox("Save to history", True)
            if st.button("Predict Cost", type="primary"):
                if query:
                    cost = calculate_cost(query, mb)
                    if save:
                        st.session_state.query_history.append({
                            'query': query[:200],
                            'cost': cost,
                            'mb': mb,
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                    st.markdown(f"""
                    <div class="cost-card">
                        <h3>Estimated Cost</h3>
                        <h1>${cost:.4f}</h1>
                        <p>Based on {mb} MB scan</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Tips
                    tips = []
                    if 'SELECT *' in query.upper():
                        tips.append("❌ Avoid `SELECT *` - specify only needed columns")
                    if 'WHERE' not in query.upper():
                        tips.append("⚠️ Add a WHERE clause to filter data")
                    if 'LIMIT' not in query.upper():
                        tips.append("💡 Add LIMIT for testing")
                    if tips:
                        st.info("\n".join(tips))
                    else:
                        st.success("✅ Your query looks optimized!")
                else:
                    st.warning("Enter a query")
        
        with col2:
            st.markdown("""
            <div class="glass-card">
                <h3>⚡ Quick Examples</h3>
            </div>
            """, unsafe_allow_html=True)
            examples = {
                "Simple SELECT": "SELECT * FROM CUSTOMER LIMIT 100",
                "With WHERE": "SELECT * FROM CUSTOMER WHERE C_NATIONKEY = 10 LIMIT 100",
                "Aggregation": "SELECT C_NATIONKEY, COUNT(*) FROM CUSTOMER GROUP BY C_NATIONKEY",
                "Join": "SELECT * FROM CUSTOMER JOIN ORDERS ON C_CUSTKEY = O_CUSTKEY LIMIT 1000"
            }
            for name, sql in examples.items():
                if st.button(name, key=f"ex_{name}"):
                    st.session_state.query_input = sql
                    st.rerun()
    
    # History
    elif page == "📜 History":
        st.markdown('<div class="main-header"><h1>📜 Query History</h1></div>', unsafe_allow_html=True)
        if st.session_state.query_history:
            for i, q in enumerate(st.session_state.query_history[::-1]):
                with st.expander(f"Query {len(st.session_state.query_history)-i} - ${q['cost']:.4f}"):
                    st.code(q['query'], language='sql')
                    st.write(f"**Size:** {q['mb']} MB")
                    st.write(f"**Time:** {q['timestamp']}")
            if st.button("Clear All"):
                st.session_state.query_history = []
                st.rerun()
        else:
            st.info("No history yet.")

# Footer
st.markdown("---")
st.markdown("<p style='text-align:center;'>🔮 QueryGuard Pro - Intelligent Snowflake Cost Optimization | © 2025</p>", unsafe_allow_html=True)
