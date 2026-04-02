# demo_mode.py
# Use this if you don't want to connect to Snowflake

class DBSimulator:
    def authenticate_user(self, username, password):
        # Demo users
        if username == "demo" and password == "demo123":
            return {
                'id': 1,
                'username': 'demo',
                'email': 'demo@queryguard.com',
                'api_key': 'demo_key_123'
            }
        return None

    def create_user(self, email, username, password, company=None):
        return {'id': 2, 'username': username, 'api_key': 'new_key'}

    def save_query_history(self, user_id, query, cost):
        pass

    def get_user_history(self, user_id, limit=100):
        import pandas as pd
        return pd.DataFrame()

    def get_unresolved_alerts(self, user_id):
        return []

    def get_saved_queries(self, user_id):
        return []

    def create_alert(self, user_id, query, cost, threshold):
        pass

# Use this for demo
# db = DBSimulator()