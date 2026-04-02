# ml_model.py - Simplified version for Streamlit Cloud

class CostPredictor:
    """
    Simple cost predictor based on Snowflake's actual pricing
    No external dependencies needed
    """
    
    def predict(self, query_text: str, mb_estimate: float = 10) -> float:
        """Predict cost for a query"""
        # Convert MB to GB
        gb_scanned = mb_estimate / 1024
        
        # Base cost: $0.50 per GB
        base_cost = gb_scanned * 0.50
        
        # Complexity multipliers
        complexity = 1.0
        query_upper = query_text.upper()
        
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

# Create global instance
predictor = CostPredictor()
