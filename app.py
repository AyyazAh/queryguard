import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
from ml_model import predictor
from database import db
import hashlib
import os

# Use Streamlit secrets for configuration
if 'snowflake' in st.secrets:
    SNOWFLAKE_ACCOUNT = st.secrets['snowflake']['account']
    SNOWFLAKE_USER = st.secrets['snowflake']['user']
    SNOWFLAKE_PASSWORD = st.secrets['snowflake']['password']



# Page configuration
st.set_page_config(
    page_title="QueryGuard - Snowflake Cost Optimizer",
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


# Authentication functions
def login():
    with st.sidebar:
        st.header("🔐 Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login", key="login_button", use_container_width=True):
            user = db.authenticate_user(username, password)
            if user:
                st.session_state.authenticated = True
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Invalid credentials")


def signup():
    with st.sidebar:
        st.header("📝 Sign Up")
        email = st.text_input("Email", key="signup_email")
        username = st.text_input("Username", key="signup_username")
        password = st.text_input("Password", type="password", key="signup_password")
        company = st.text_input("Company (Optional)", key="signup_company")

        if st.button("Sign Up", key="signup_button", use_container_width=True):
            if email and username and password:
                user = db.create_user(email, username, password, company)
                if user:
                    st.success("Account created! Please login.")
                else:
                    st.error("Username or email already exists")
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
        - **Alert** when queries exceed budget thresholds
        """)

    with col2:
        st.markdown("---")
        login()
        st.markdown("---")
        signup()
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
            ["🏠 Dashboard", "💰 Predict Cost", "📜 History", "📊 Analytics", "⚙️ Settings"],
            key="nav_radio"
        )

        st.markdown("---")

        # API Key display
        with st.expander("🔑 API Key"):
            st.code(st.session_state.user['api_key'], language="text")
            st.caption("Use this key for API access")

        if st.button("🚪 Logout", key="logout_button", use_container_width=True):
            logout()

    # Main content based on navigation
    if page == "🏠 Dashboard":
        st.markdown("""
        <div class="main-header">
            <h1>Welcome to QueryGuard</h1>
            <p>Your Snowflake Cost Optimization Dashboard</p>
        </div>
        """, unsafe_allow_html=True)

        # Metrics
        col1, col2, col3, col4 = st.columns(4)

        # Get user stats
        history = db.get_user_history(st.session_state.user['id'], limit=100)

        with col1:
            st.metric("Total Predictions", len(history))

        with col2:
            total_cost = history['predicted_cost'].sum() if len(history) > 0 else 0
            st.metric("Total Predicted Cost", f"${total_cost:.2f}")

        with col3:
            avg_cost = history['predicted_cost'].mean() if len(history) > 0 else 0
            st.metric("Average Query Cost", f"${avg_cost:.4f}")

        with col4:
            alerts = len(db.get_unresolved_alerts(st.session_state.user['id']))
            st.metric("Active Alerts", alerts)

        # Recent activity chart
        if len(history) > 0:
            st.subheader("📈 Recent Activity")
            history['date'] = pd.to_datetime(history['created_at']).dt.date
            daily_costs = history.groupby('date')['predicted_cost'].sum().reset_index()

            fig = px.line(daily_costs, x='date', y='predicted_cost',
                          title='Daily Predicted Costs',
                          labels={'predicted_cost': 'Cost ($)', 'date': 'Date'})
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

        # Recent queries
        st.subheader("📋 Recent Queries")
        if len(history) > 0:
            st.dataframe(
                history[['query_text', 'predicted_cost', 'created_at']].head(10),
                use_container_width=True
            )
        else:
            st.info("No queries yet. Start predicting costs!")


    elif page == "💰 Predict Cost":

        st.header("💰 Predict Query Cost")

        col1, col2 = st.columns([3, 2])

        with col1:

            query = st.text_area(

                "Enter your SQL query",

                height=200,

                placeholder="SELECT * FROM CUSTOMER WHERE C_NATIONKEY = 10 LIMIT 100",

                key="query_input"

            )

            col_a, col_b, col_c = st.columns(3)

            with col_a:

                bytes_estimate = st.number_input("Estimated bytes (MB)", min_value=1, value=10, key="bytes_estimate")

            with col_b:

                threshold = st.number_input("Alert threshold ($)", min_value=0.01, value=1.0, key="threshold")

            with col_c:

                save_to_history = st.checkbox("Save to history", value=True, key="save_history")

            if st.button("🔮 Predict Cost", type="primary", use_container_width=True, key="predict_button"):

                if query:

                    with st.spinner("Analyzing query..."):

                        # FIXED: Pass MB directly, not bytes

                        cost = predictor.predict(query, bytes_estimate)

                        # Save to history

                        if save_to_history:
                            db.save_query_history(

                                st.session_state.user['id'],

                                query,

                                cost

                            )

                        # Check threshold

                        if cost > threshold:
                            db.create_alert(

                                st.session_state.user['id'],

                                query,

                                cost,

                                threshold

                            )

                            st.warning(f"⚠️ Alert: Query exceeds ${threshold} threshold!")

                        # Display result

                        st.markdown(f"""

                        <div class="cost-card">

                            <h3>Estimated Cost</h3>

                            <h1>${cost:.4f}</h1>

                            <p>Based on {bytes_estimate} MB scan estimate</p>

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
                        if tips:
                            for tip in tips:
                                st.markdown(f"- {tip}")

                        else:

                            st.success("✅ Your query looks optimized!")
                else:
                    st.warning("Please enter a SQL query")
        with col2:
            st.subheader("📚 Saved Queries")
            saved_queries = db.get_saved_queries(st.session_state.user['id'])
            if saved_queries:

                for sq in saved_queries:
                    with st.expander(f"📝 {sq['name']}"):
                        st.code(sq['query_text'], language='sql')
                        if st.button(f"Use", key=f"use_{sq['id']}"):
                            st.session_state.selected_query = sq['query_text']
                            st.rerun()
            else:
                st.info("No saved queries yet")
            st.subheader("⚡ Quick Examples")
            examples = [
                ("Simple Count", "SELECT COUNT(*) FROM CUSTOMER"),
                ("With Filter", "SELECT * FROM CUSTOMER WHERE C_NATIONKEY = 10 LIMIT 100"),
                ("Aggregation", "SELECT C_NATIONKEY, COUNT(*) FROM CUSTOMER GROUP BY C_NATIONKEY")
            ]
            for name, example in examples:
                if st.button(f"📋 {name}", key=f"ex_{name}"):
                    st.session_state.selected_query = example
                    st.rerun()

    elif page == "📜 History":
        st.header("📜 Query History")

        history = db.get_user_history(st.session_state.user['id'], limit=100)

        if len(history) > 0:
            # Filters
            col1, col2 = st.columns(2)
            with col1:
                min_cost = st.number_input("Min Cost ($)", min_value=0.0, value=0.0, key="min_cost")
            with col2:
                max_cost = st.number_input("Max Cost ($)", min_value=0.0, value=100.0, key="max_cost")

            filtered = history[(history['predicted_cost'] >= min_cost) &
                               (history['predicted_cost'] <= max_cost)]

            st.dataframe(
                filtered[['query_text', 'predicted_cost', 'created_at', 'status']],
                use_container_width=True,
                height=400
            )

            # Export options
            if st.button("📥 Export to CSV", key="export_csv"):
                csv = filtered.to_csv(index=False)
                st.download_button("Download CSV", csv, "query_history.csv", "text/csv", key="download_csv")
        else:
            st.info("No query history yet. Start predicting!")

    elif page == "📊 Analytics":
        st.header("📊 Analytics Dashboard")

        history = db.get_user_history(st.session_state.user['id'], limit=500)

        if len(history) > 0:
            # Cost distribution
            st.subheader("Cost Distribution")
            fig = px.histogram(history, x='predicted_cost', nbins=20,
                               title='Query Cost Distribution',
                               labels={'predicted_cost': 'Cost ($)', 'count': 'Number of Queries'})
            st.plotly_chart(fig, use_container_width=True)

            # Time analysis
            st.subheader("Time Analysis")
            history['hour'] = pd.to_datetime(history['created_at']).dt.hour
            hourly_costs = history.groupby('hour')['predicted_cost'].mean()

            fig = px.line(x=hourly_costs.index, y=hourly_costs.values,
                          title='Average Cost by Hour',
                          labels={'x': 'Hour of Day', 'y': 'Average Cost ($)'})
            st.plotly_chart(fig, use_container_width=True)

            # Top expensive queries
            st.subheader("Top 10 Most Expensive Queries")
            top_expensive = history.nlargest(10, 'predicted_cost')[['query_text', 'predicted_cost']]
            st.dataframe(top_expensive, use_container_width=True)
        else:
            st.info("Not enough data for analytics")

    elif page == "⚙️ Settings":
        st.header("⚙️ Settings")

        st.subheader("Alert Settings")
        alert_threshold = st.number_input("Default Alert Threshold ($)", min_value=0.01, value=1.0,
                                          key="alert_threshold")

        st.subheader("Notification Preferences")
        email_alerts = st.checkbox("Email Alerts", value=True, key="email_alerts")
        slack_webhook = st.text_input("Slack Webhook URL (Optional)", key="slack_webhook")

        st.subheader("API Settings")
        st.info(f"Your API Key: `{st.session_state.user['api_key']}`")
        if st.button("Regenerate API Key", key="regenerate_key"):
            st.warning("This will invalidate your old API key")

        if st.button("Save Settings", type="primary", key="save_settings"):
            st.success("Settings saved successfully!")