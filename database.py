# database.py - Simplified for Streamlit Cloud
import streamlit as st
import pandas as pd
from datetime import datetime

class Database:
    """Simple in-memory database for demo"""
    
    def __init__(self):
        # Use session state to persist data
        if 'users' not in st.session_state:
            st.session_state.users = {}
        if 'history' not in st.session_state:
            st.session_state.history = {}
    
    def authenticate_user(self, username, password):
        # Demo user - anyone can login with demo/demo123
        if username == "demo" and password == "demo123":
            return {
                'id': 1,
                'username': 'demo',
                'email': 'demo@queryguard.com',
                'api_key': 'demo_key_123',
                'is_admin': False
            }
        return None
    
    def create_user(self, email, username, password, company=None):
        # Auto-create demo account
        return {'id': 2, 'username': username, 'api_key': 'new_key'}
    
    def save_query_history(self, user_id, query, cost):
        # Store in session state
        key = f"history_{user_id}"
        if key not in st.session_state:
            st.session_state[key] = []
        st.session_state[key].append({
            'query_text': query,
            'predicted_cost': cost,
            'created_at': datetime.now(),
            'status': 'predicted'
        })
    
    def get_user_history(self, user_id, limit=100):
        key = f"history_{user_id}"
        if key in st.session_state:
            data = st.session_state[key][-limit:]
            return pd.DataFrame(data)
        return pd.DataFrame()
    
    def get_unresolved_alerts(self, user_id):
        return []
    
    def get_saved_queries(self, user_id):
        return []
    
    def create_alert(self, user_id, query, cost, threshold):
        pass

db = Database()
