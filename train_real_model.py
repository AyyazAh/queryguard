import sqlite3
import pandas as pd
import pickle
from sklearn.ensemble import RandomForestRegressor
import os
import numpy as np

print("=" * 60)
print("🎯 TRAINING MODEL WITH YOUR REAL DATA")
print("=" * 60)

# Load data from queryguard.db
conn = sqlite3.connect('queryguard.db')

# Check what columns we have
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(queries)')
columns = [col[1] for col in cursor.fetchall()]
print(f"\n📋 Available columns: {columns}")

# Determine correct column names
if 'estimated_cost' in columns:
    cost_col = 'estimated_cost'
elif 'ESTIMATED_COST' in columns:
    cost_col = 'ESTIMATED_COST'
else:
    cost_col = 'estimated_cost'  # fallback

if 'bytes_scanned' in columns:
    bytes_col = 'bytes_scanned'
elif 'BYTES_SCANNED' in columns:
    bytes_col = 'BYTES_SCANNED'
else:
    bytes_col = 'bytes_scanned'

if 'query_text' in columns:
    text_col = 'query_text'
elif 'QUERY_TEXT' in columns:
    text_col = 'QUERY_TEXT'
else:
    text_col = 'query_text'

print(f"📊 Using columns: text={text_col}, bytes={bytes_col}, cost={cost_col}")

# Load data
queries_df = pd.read_sql_query(f"""
    SELECT {text_col} as query_text, 
           {bytes_col} as bytes_scanned, 
           {cost_col} as estimated_cost
    FROM queries
    WHERE {bytes_col} > 0
""", conn)
conn.close()

print(f"\n📊 Loaded {len(queries_df)} queries with real byte scan data")

if len(queries_df) == 0:
    print("❌ No queries with byte scan data found!")
    exit()

print(f"💰 Cost range: ${queries_df['estimated_cost'].min():.4f} - ${queries_df['estimated_cost'].max():.2f}")
print(f"📈 Bytes range: {queries_df['bytes_scanned'].min():,.0f} - {queries_df['bytes_scanned'].max():,.0f} bytes")

# Create features
print("\n🔧 Creating features...")
queries_df['query_length'] = queries_df['query_text'].str.len()
queries_df['word_count'] = queries_df['query_text'].str.split().str.len()
queries_df['has_where'] = queries_df['query_text'].str.upper().str.contains('WHERE').astype(int)
queries_df['has_join'] = queries_df['query_text'].str.upper().str.contains('JOIN').astype(int)
queries_df['has_group'] = queries_df['query_text'].str.upper().str.contains('GROUP BY').astype(int)
queries_df['has_order'] = queries_df['query_text'].str.upper().str.contains('ORDER BY').astype(int)
queries_df['has_limit'] = queries_df['query_text'].str.upper().str.contains('LIMIT').astype(int)
queries_df['has_count'] = queries_df['query_text'].str.upper().str.contains('COUNT').astype(int)
queries_df['has_sum'] = queries_df['query_text'].str.upper().str.contains('SUM').astype(int)

# Features for training
features = [
    'query_length', 'word_count',
    'has_where', 'has_join', 'has_group', 'has_order', 'has_limit',
    'has_count', 'has_sum', 'bytes_scanned'
]

X = queries_df[features].fillna(0)
y = queries_df['estimated_cost']

print(f"✅ Created {len(X)} training samples")
print(f"📊 Features: {features}")

# Train model
print("\n🤖 Training Random Forest model...")
model = RandomForestRegressor(
    n_estimators=100,
    max_depth=10,
    random_state=42,
    n_jobs=-1
)
model.fit(X, y)

# Evaluate
train_score = model.score(X, y)
print(f"✅ Model trained! R² score: {train_score:.4f}")

# Feature importance
importance_df = pd.DataFrame({
    'feature': features,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print("\n📊 Feature importance:")
for _, row in importance_df.iterrows():
    print(f"   {row['feature']}: {row['importance']:.4f}")

# Save model
os.makedirs('models', exist_ok=True)
with open('models/cost_predictor.pkl', 'wb') as f:
    pickle.dump({'model': model, 'features': features}, f)

print("\n✅ Model saved to models/cost_predictor.pkl")

# Test predictions
print("\n🧪 Testing predictions on your actual queries:")
for idx, row in queries_df.head(5).iterrows():
    query_preview = row['query_text'][:60] if len(row['query_text']) > 60 else row['query_text']
    actual_cost = row['estimated_cost']

    features_input = row[features].values.reshape(1, -1)
    predicted_cost = model.predict(features_input)[0]

    print(f"\n  Query: {query_preview}...")
    print(f"    Actual: ${actual_cost:.4f}")
    print(f"    Predicted: ${predicted_cost:.4f}")
    print(f"    Error: ${abs(actual_cost - predicted_cost):.4f}")

# Test on new queries
print("\n" + "=" * 60)
print("🧪 Testing on new queries (estimates):")
print("=" * 60)

test_queries = [
    ("SELECT * FROM CUSTOMER LIMIT 100", 10),
    ("SELECT COUNT(*) FROM ORDERS", 50),
    ("SELECT C_NATIONKEY, COUNT(*) FROM CUSTOMER GROUP BY C_NATIONKEY", 100),
    ("SELECT * FROM CUSTOMER JOIN ORDERS LIMIT 1000", 200),
]

for query, mb in test_queries:
    bytes_scanned = mb * 1024 * 1024

    # Create features for this query
    features_input = pd.DataFrame([{
        'query_length': len(query),
        'word_count': len(query.split()),
        'has_where': 1 if 'WHERE' in query.upper() else 0,
        'has_join': 1 if 'JOIN' in query.upper() else 0,
        'has_group': 1 if 'GROUP BY' in query.upper() else 0,
        'has_order': 1 if 'ORDER BY' in query.upper() else 0,
        'has_limit': 1 if 'LIMIT' in query.upper() else 0,
        'has_count': 1 if 'COUNT' in query.upper() else 0,
        'has_sum': 1 if 'SUM' in query.upper() else 0,
        'bytes_scanned': bytes_scanned
    }])

    cost = model.predict(features_input)[0]
    print(f"\n  {mb}MB query:")
    print(f"    Query: {query[:50]}...")
    print(f"    Estimated cost: ${cost:.4f}")

print("\n" + "=" * 60)
print("✅ Model ready! Restart Streamlit to use it.")
print("=" * 60)