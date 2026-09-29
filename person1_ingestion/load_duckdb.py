import duckdb
import os

# Set up paths so it dynamically finds your CSVs in the SOC folder
script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, "sat_sa.duckdb")

print(f"Creating offline DuckDB database at {db_path}...")
con = duckdb.connect(db_path)

# Map the CSV paths
alerts_csv = os.path.join(script_dir, "alerts_poisoned.csv")
assets_csv = os.path.join(script_dir, "asset_inventory_poisoned.csv")
cases_csv = os.path.join(script_dir, "cases_poisoned.csv")
ground_truth_csv = os.path.join(script_dir, "ground_truth.csv")

print("Ingesting datasets with automatic schema and column mapping...")

# DuckDB's read_csv_auto automatically infers schemas and maps columns based on the CSV headers
con.execute(f"CREATE OR REPLACE TABLE assets AS SELECT * FROM read_csv_auto('{assets_csv}')")
print("✓ Loaded 'assets' table")

con.execute(f"CREATE OR REPLACE TABLE alerts AS SELECT * FROM read_csv_auto('{alerts_csv}')")
print("✓ Loaded 'alerts' table")

con.execute(f"CREATE OR REPLACE TABLE cases AS SELECT * FROM read_csv_auto('{cases_csv}')")
print("✓ Loaded 'cases' table")

con.execute(f"CREATE OR REPLACE TABLE ground_truth AS SELECT * FROM read_csv_auto('{ground_truth_csv}')")
print("✓ Loaded 'ground_truth' table")

print("\n--- Verification ---")
# Verify that the tables were created successfully
tables = con.execute("SHOW TABLES").df()
print("Tables in database:\n", tables.to_string(index=False))

# Do a quick count on alerts to confirm data loaded
alert_count = con.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
print(f"\nTotal alerts ready for analysis: {alert_count}")

con.close()
print("\nSuccess! Hand over 'sat_sa.duckdb' to the rest of the team.")