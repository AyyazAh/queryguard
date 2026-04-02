import sqlite3

print("=" * 60)
print("🔍 CHECKING YOUR DATABASE")
print("=" * 60)

# Check queryguard.db
conn = sqlite3.connect('queryguard.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f"\n📋 Tables in queryguard.db: {tables}")

if tables:
    # Check queries table
    try:
        cursor.execute("SELECT COUNT(*) FROM queries")
        count = cursor.fetchone()[0]
        print(f"📊 Total queries: {count}")

        cursor.execute("SELECT COUNT(*) FROM queries WHERE bytes_scanned > 0")
        count_with_bytes = cursor.fetchone()[0]
        print(f"📊 Queries with bytes_scanned > 0: {count_with_bytes}")

        if count_with_bytes > 0:
            cursor.execute("SELECT AVG(bytes_scanned), MAX(bytes_scanned) FROM queries WHERE bytes_scanned > 0")
            avg_bytes, max_bytes = cursor.fetchone()
            print(f"📊 Average bytes scanned: {avg_bytes:,.0f}")
            print(f"📊 Max bytes scanned: {max_bytes:,.0f}")

            # Show sample queries
            cursor.execute(
                "SELECT query_text, bytes_scanned, estimated_cost FROM queries WHERE bytes_scanned > 0 LIMIT 5")
            samples = cursor.fetchall()
            print("\n📝 Sample queries with data:")
            for i, sample in enumerate(samples, 1):
                text = sample[0][:50] if sample[0] else "N/A"
                print(f"  {i}. {text}...")
                print(f"     Bytes: {sample[1]:,}, Cost: ${sample[2]:.4f}")
        else:
            print("\n⚠️ No queries with byte scan data found!")
            print("Please run some queries in Snowflake first.")

    except sqlite3.OperationalError as e:
        print(f"❌ Error: {e}")

conn.close()

# Also check if there's a data folder
import os

if os.path.exists('data/queryguard.db'):
    print("\n📁 Also found data/queryguard.db")
    conn2 = sqlite3.connect('data/queryguard.db')
    cursor2 = conn2.cursor()
    cursor2.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables2 = cursor2.fetchall()
    print(f"   Tables in data/queryguard.db: {tables2}")
    conn2.close()

print("\n" + "=" * 60)