import duckdb
import os

# Locate the database file in the root folder (one level up from person2_execution_gaps)
script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.abspath(os.path.join(script_dir, "..", "sat_sa.duckdb"))

print(f"Connecting to database at: {db_path}")

# Connect to DuckDB in read-only mode (safe for querying)
con = duckdb.connect(db_path, read_only=True)

# 1. See what tables are available
print("\n--- Tables in Database ---")
tables = con.execute("SHOW TABLES").df()
print(tables)

# 2. Example Query: Find critical alerts closed unusually fast (Execution Gap)
print("\n--- Querying Fast Critical Alerts ---")
query = """
    SELECT alert_id, entity_id, asset_id, severity, created_at, closed_at 
    FROM alerts 
    WHERE severity = 'Critical' AND status = 'Closed'
    LIMIT 5
"""
df_fast_alerts = con.execute(query).df()
print(df_fast_alerts)

# Always close the connection when done
con.close()