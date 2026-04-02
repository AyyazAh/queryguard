import streamlit as st
import pickle
import pandas as pd
import os

class CostPredictor:
    def __init__(self, model_path='models/cost_predictor.pkl'):
        self.model_path = model_path
        self.model = None
        self.features = None
        self.load_model()

    def load_model(self):
        """Load trained model"""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    data = pickle.load(f)
                    self.model = data['model']
                    self.features = data['features']
                return True
            except:
                return False
        return False

    def predict(self, query_text: str, mb_estimate: float = 10) -> float:
        """Predict cost for a query"""
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

predictor = CostPredictor()