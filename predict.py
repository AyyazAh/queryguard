import pandas as pd
import sqlite3
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import pickle
import re

print("=" * 60)
print("🎯 QUERYGUARD - COST PREDICTOR")
print("=" * 60)

# Load data
print("\n📂 Loading your queries...")
conn = sqlite3.connect('queryguard.db')
queries_df = pd.read_sql_query("SELECT * FROM queries", conn)
conn.close()

if len(queries_df) == 0:
    print("❌ No data found! Run collect.py first")
    exit()

print(f"✅ Loaded {len(queries_df)} queries")

# Create features
print("\n🔧 Creating features...")
features_df = queries_df.copy()
features_df['query_length'] = features_df['QUERY_TEXT'].str.len()
features_df['has_where'] = features_df['QUERY_TEXT'].str.upper().str.contains('WHERE').astype(int)
features_df['has_join'] = features_df['QUERY_TEXT'].str.upper().str.contains('JOIN').astype(int)
features_df['has_group'] = features_df['QUERY_TEXT'].str.upper().str.contains('GROUP BY').astype(int)
features_df['has_order'] = features_df['QUERY_TEXT'].str.upper().str.contains('ORDER BY').astype(int)
features_df['has_limit'] = features_df['QUERY_TEXT'].str.upper().str.contains('LIMIT').astype(int)
features_df['word_count'] = features_df['QUERY_TEXT'].str.split().str.len()
features_df['comma_count'] = features_df['QUERY_TEXT'].str.count(',')
# Fixed the escape character warning
features_df['paren_count'] = features_df['QUERY_TEXT'].str.count(r'\(') + features_df['QUERY_TEXT'].str.count(r'\)')

# Use bytes scanned and other features
features = ['query_length', 'has_where', 'has_join', 'has_group', 'has_order', 'has_limit',
            'word_count', 'comma_count', 'paren_count', 'BYTES_SCANNED']
X = features_df[features].fillna(0)
y = features_df['ESTIMATED_COST']

print(f"✅ Created {len(features)} features")

# Train model
print("\n🤖 Training model...")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
model.fit(X_train, y_train)

# Evaluate
train_score = model.score(X_train, y_train)
test_score = model.score(X_test, y_test)
print(f"✅ Model trained!")
print(f"   Training R² score: {train_score:.4f}")
print(f"   Test R² score: {test_score:.4f}")

# Show feature importance
importance_df = pd.DataFrame({
    'feature': features,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)
print(f"\n📊 Most important features:")
for i, row in importance_df.head(5).iterrows():
    print(f"   {row['feature']}: {row['importance']:.4f}")

# Save model
with open('cost_predictor.pkl', 'wb') as f:
    pickle.dump(model, f)
print(f"\n✅ Model saved to cost_predictor.pkl")

# Test on real queries from your data
print("\n🧪 Testing on actual queries from your data:")
test_queries = features_df.sample(min(5, len(features_df)))
for idx, row in test_queries.iterrows():
    query_text = row['QUERY_TEXT'][:80] if pd.notna(row['QUERY_TEXT']) else "N/A"
    actual_cost = row['ESTIMATED_COST']
    features_input = row[features].values.reshape(1, -1)
    predicted_cost = model.predict(features_input)[0]

    print(f"\n  Query: {query_text}...")
    print(f"  Actual cost: ${actual_cost:.2f}")
    print(f"  Predicted cost: ${predicted_cost:.2f}")
    print(f"  Error: ${abs(actual_cost - predicted_cost):.2f}")

print("\n" + "=" * 60)
print("✅ READY TO USE!")
print("=" * 60)