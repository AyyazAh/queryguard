import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import hashlib

# Page configuration
st.set_page_config(
    page_title="QueryGuard - Snowflake Cost Predictor",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .cost-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'query_history' not in st.session_state:
    st.session_state.query_history = []
if 'saved_queries' not in st.session_state:
    st.session_state.saved_queries = []

# Simple cost calculator (no ML dependencies)
def calculate_cost(query_text, mb_estimate):
    """Calculate cost based on Snowflake pricing: $0.50 per GB"""
    gb_scanned = mb_estimate / 1024
    base_cost = gb_scanned * 0.50
    
    query_upper = query_text.upper()
    
    # Complexity multipliers
    complexity = 1.0
    if 'JOIN' in query_upper:
        complexity *= 1.5
    if 'GROUP BY' in query_upper:
        complexity *= 1.3
    if 'ORDER BY' in query_upper:
        complexity *= 1.1
    if 'DISTINCT' in query_upper:
        complexity *= 1.2
    if 'WHERE' in query_upper:
        complexity *= 0.7
    if 'LIMIT' in query_upper:
        complexity *= 0.5
    
    final_cost = base_cost * complexity
    
    # Cap based on size
    if mb_estimate <= 10:
        final_cost = min(final_cost, 0.01)
    elif mb_estimate <= 100:
        final_cost = min(final_cost, 0.10)
    elif mb_estimate <= 1000:
        final_cost = min(final_cost, 0.50)
    
    return round(max(0.001, final_cost), 4)

# Authentication functions
def login():
    with st.sidebar:
        st.header("🔐 Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", key="login_button", use_container_width=True):
            # Demo users
            if username == "demo" and password == "demo123":
                st.session_state.authenticated = True
                st.session_state.user = {
                    'id': 1,
                    'username': 'demo',
                    'email': 'demo@queryguard.com',
                    'api_key': 'demo_key_123'
                }
                st.rerun()
            else:
                st.error("Invalid credentials. Try demo/demo123")

def signup():
    with st.sidebar:
        st.header("📝 Sign Up")
        email = st.text_input("Email", key="signup_email")
        username = st.text_input("Username", key="signup_username")
        password = st.text_input("Password", type="password", key="signup_password")
        
        if st.button("Sign Up", key="signup_button", use_container_width=True):
            if email and username and password:
                st.success("Account created! Please login with demo/demo123")
            else:
                st.error("Please fill all required fields")

def logout():
    st.session_state.authenticated = False
    st.session_state.user = None
    st.rerun()

# Main app
if not st.session_state.authenticated:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("""
        <div class="main-header">
            <h1>🔍 QueryGuard</h1>
            <p>Intelligent Snowflake Query Cost Optimization Platform</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        ### 🚀 Stop Wasting Money on Snowflake
        
        QueryGuard helps you:
        - **Predict** query costs before execution
        - **Optimize** expensive queries with AI suggestions
        - **Monitor** your Snowflake spending in real-time
        
        ### 💡 How It Works
        
        1. Enter your SQL query
        2. Estimate the data size (MB)
        3. Get instant cost prediction
        4. Receive optimization recommendations
        
        ### 📊 Pricing Reference
        
        Snowflake charges **$0.50 per GB scanned**
        
        | Size | Estimated Cost |
        |------|----------------|
        | 1 MB | $0.0005 |
        | 10 MB | $0.005 |
        | 100 MB | $0.05 |
        | 1 GB | $0.50 |
        | 10 GB | $5.00 |
        """)
    
    with col2:
        st.markdown("---")
        login()
        st.markdown("---")
        signup()
        st.markdown("---")
        st.info("**Demo Credentials:**\nUsername: `demo`\nPassword: `demo123`")
else:
    # Sidebar for authenticated users
    with st.sidebar:
        st.markdown("# 🔍 QueryGuard")
        st.markdown(f"### Welcome, {st.session_state.user['username']}!")
        st.markdown(f"📧 {st.session_state.user['email']}")
        
        st.markdown("---")
        
        # Navigation
        page = st.radio(
            "Navigation",
            ["🏠 Dashboard", "💰 Predict Cost", "📜 History", "📊 Analytics", "⚡ Examples"],
            key="nav_radio"
        )
        
        st.markdown("---")
        
        with st.expander("🔑 API Key"):
            st.code(st.session_state.user['api_key'], language="text")
            st.caption("Use this key for API access")
        
        if st.button("🚪 Logout", key="logout_button", use_container_width=True):
            logout()
    
    # Dashboard
    if page == "🏠 Dashboard":
        st.markdown("""
        <div class="main-header">
            <h1>Welcome to QueryGuard</h1>
            <p>Your Snowflake Cost Optimization Dashboard</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Predictions", len(st.session_state.query_history))
        
        with col2:
            total_cost = sum(q['cost'] for q in st.session_state.query_history)
            st.metric("Total Predicted Cost", f"${total_cost:.2f}")
        
        with col3:
            avg_cost = total_cost / len(st.session_state.query_history) if st.session_state.query_history else 0
            st.metric("Average Query Cost", f"${avg_cost:.4f}")
        
        if st.session_state.query_history:
            st.subheader("📋 Recent Queries")
            df = pd.DataFrame(st.session_state.query_history[-5:])
            st.dataframe(df[['query', 'cost', 'mb', 'timestamp']], use_container_width=True)
        else:
            st.info("No queries yet. Go to Predict Cost to get started!")
    
    # Predict Cost
    elif page == "💰 Predict Cost":
        st.header("💰 Predict Query Cost")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            query = st.text_area(
                "Enter your SQL query",
                height=150,
                placeholder="SELECT * FROM CUSTOMER WHERE C_NATIONKEY = 10 LIMIT 100",
                key="query_input"
            )
            
            mb = st.slider("Estimated data scanned (MB)", 1, 10000, 10, key="mb_slider")
            threshold = st.number_input("Alert threshold ($)", min_value=0.01, value=1.00, key="threshold")
            save_to_history = st.checkbox("Save to history", value=True, key="save_history")
            
            if st.button("💰 Predict Cost", type="primary", use_container_width=True):
                if query:
                    cost = calculate_cost(query, mb)
                    
                    if save_to_history:
                        st.session_state.query_history.append({
                            'query': query[:100],
                            'cost': cost,
                            'mb': mb,
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                    
                    if cost > threshold:
                        st.warning(f"⚠️ Alert: Query exceeds ${threshold} threshold! Estimated cost: ${cost:.4f}")
                    
                    st.markdown(f"""
                    <div class="cost-card">
                        <h3>Estimated Cost</h3>
                        <h1>${cost:.4f}</h1>
                        <p>Based on {mb} MB scan estimate</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Optimization tips
                    st.subheader("💡 Optimization Tips")
                    tips = []
                    if 'SELECT *' in query.upper():
                        tips.append("❌ Avoid SELECT * - specify only needed columns")
                    if 'WHERE' not in query.upper():
                        tips.append("⚠️ Add WHERE clause to filter data")
                    if 'LIMIT' not in query.upper():
                        tips.append("💡 Consider adding LIMIT for testing")
                    if 'JOIN' in query.upper():
                        tips.append("🔗 Ensure join columns are clustered")
                    if 'GROUP BY' in query.upper():
                        tips.append("📊 Consider pre-aggregating data")
                    
                    if tips:
                        for tip in tips:
                            st.markdown(f"- {tip}")
                    else:
                        st.success("✅ Your query looks optimized!")
                else:
                    st.warning("Please enter a SQL query")
        
        with col2:
            st.subheader("📊 Cost Reference")
            st.markdown("""
            | Size | Cost |
            |------|------|
            | 1 MB | $0.0005 |
            | 10 MB | $0.005 |
            | 100 MB | $0.05 |
            | 1 GB | $0.50 |
            | 10 GB | $5.00 |
            """)
            
            st.subheader("⚡ Quick Examples")
            examples = [
                ("Simple Count", "SELECT COUNT(*) FROM CUSTOMER", 10),
                ("With Filter", "SELECT * FROM CUSTOMER WHERE C_NATIONKEY = 10 LIMIT 100", 10),
                ("Aggregation", "SELECT C_NATIONKEY, COUNT(*) FROM CUSTOMER GROUP BY C_NATIONKEY", 100),
                ("Join Query", "SELECT * FROM CUSTOMER JOIN ORDERS ON C_CUSTKEY = O_CUSTKEY LIMIT 1000", 500)
            ]
            for name, example, size in examples:
                if st.button(f"📋 {name}", key=f"ex_{name}"):
                    st.session_state.query_input = example
                    st.session_state.mb_slider = size
                    st.rerun()
    
    # History
    elif page == "📜 History":
        st.header("📜 Query History")
        
        if st.session_state.query_history:
            df = pd.DataFrame(st.session_state.query_history)
            st.dataframe(df, use_container_width=True)
            
            if st.button("📥 Clear History"):
                st.session_state.query_history = []
                st.rerun()
        else:
            st.info("No query history yet. Start predicting costs!")
    
    # Analytics
    elif page == "📊 Analytics":
        st.header("📊 Analytics Dashboard")
        
        if st.session_state.query_history:
            df = pd.DataFrame(st.session_state.query_history)
            
            # Cost distribution
            fig = px.histogram(df, x='cost', nbins=20, title='Query Cost Distribution')
            st.plotly_chart(fig, use_container_width=True)
            
            # Cost by size
            fig2 = px.scatter(df, x='mb', y='cost', title='Cost vs Data Size',
                              labels={'mb': 'Data Size (MB)', 'cost': 'Cost ($)'})
            st.plotly_chart(fig2, use_container_width=True)
            
            # Top expensive
            st.subheader("Most Expensive Queries")
            top = df.nlargest(5, 'cost')[['query', 'cost', 'mb']]
            st.dataframe(top, use_container_width=True)
        else:
            st.info("Not enough data for analytics. Predict some queries first!")
    
    # Examples
    elif page == "⚡ Examples":
        st.header("⚡ Example Queries with Cost Estimates")
        
        examples = [
            ("Simple SELECT", "SELECT * FROM CUSTOMER LIMIT 100", 10, 0.005),
            ("Count with WHERE", "SELECT COUNT(*) FROM ORDERS WHERE O_ORDERDATE >= '2024-01-01'", 50, 0.025),
            ("GROUP BY", "SELECT C_NATIONKEY, COUNT(*) FROM CUSTOMER GROUP BY C_NATIONKEY", 100, 0.05),
            ("JOIN", "SELECT C.C_NAME, O.O_ORDERKEY FROM CUSTOMER C JOIN ORDERS O ON C.C_CUSTKEY = O.O_CUSTKEY", 500, 0.25),
            ("Complex Query", "SELECT N.N_NAME, SUM(O.O_TOTALPRICE) FROM CUSTOMER C JOIN ORDERS O ON C.C_CUSTKEY = O.O_CUSTKEY JOIN NATION N ON C.C_NATIONKEY = N.N_NATIONKEY GROUP BY N.N_NAME", 1000, 0.50)
        ]
        
        for name, query, mb, cost in examples:
            with st.expander(f"{name} - Estimated: ${cost:.4f}"):
                st.code(query, language='sql')
                st.write(f"**Estimated data scanned:** {mb} MB")
                st.write(f"**Estimated cost:** ${cost:.4f}")
                if st.button(f"Use this query", key=f"use_{name}"):
                    st.session_state.query_input = query
                    st.session_state.mb_slider = mb
                    st.rerun()

st.markdown("---")
st.caption("QueryGuard - Predict Snowflake query costs before execution | Powered by Streamlit")
