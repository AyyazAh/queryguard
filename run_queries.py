import snowflake.connector
from config import *
import time

print("=" * 60)
print("🚀 RUNNING REAL QUERIES")
print("=" * 60)

# Connect to Snowflake
print("\n📡 Connecting to Snowflake...")
conn = snowflake.connector.connect(
    account=SNOWFLAKE_ACCOUNT,
    user=SNOWFLAKE_USER,
    password=SNOWFLAKE_PASSWORD,
    warehouse=SNOWFLAKE_WAREHOUSE,
    database=SNOWFLAKE_DATABASE,
    schema=SNOWFLAKE_SCHEMA
)
print("✅ Connected!")

cursor = conn.cursor()

# Real queries that will scan data
queries = [
    "SELECT COUNT(*) FROM CUSTOMER",
    "SELECT COUNT(*) FROM ORDERS",
    "SELECT COUNT(*) FROM LINEITEM",
    "SELECT * FROM CUSTOMER LIMIT 1000",
    "SELECT * FROM ORDERS LIMIT 1000",
    "SELECT C_NATIONKEY, COUNT(*) FROM CUSTOMER GROUP BY C_NATIONKEY",
    "SELECT O_ORDERPRIORITY, COUNT(*) FROM ORDERS GROUP BY O_ORDERPRIORITY",
    "SELECT L_RETURNFLAG, COUNT(*) FROM LINEITEM GROUP BY L_RETURNFLAG",
    "SELECT C.C_NAME, O.O_ORDERKEY FROM CUSTOMER C JOIN ORDERS O ON C.C_CUSTKEY = O.O_CUSTKEY LIMIT 1000",
    "SELECT C.C_NAME, SUM(O.O_TOTALPRICE) FROM CUSTOMER C JOIN ORDERS O ON C.C_CUSTKEY = O.O_CUSTKEY GROUP BY C.C_NAME LIMIT 100"
]

print("\n📊 Running queries to generate data...")
for i, query in enumerate(queries, 1):
    try:
        print(f"  {i}. Running: {query[:50]}...")
        cursor.execute(query)
        result = cursor.fetchone()
        print(f"     ✅ Completed - Result: {result[0] if result else 'N/A'}")
        time.sleep(0.5)  # Small delay between queries
    except Exception as e:
        print(f"     ❌ Error: {e}")

cursor.close()
conn.close()

print("\n" + "=" * 60)
print("✅ All queries completed!")
print("=" * 60)
print("\n⏰ WAIT 30 SECONDS for Snowflake to log these queries")
print("Then run: python collect.py")
print("=" * 60)