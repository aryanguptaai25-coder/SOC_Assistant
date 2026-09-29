import duckdb
import pandas as pd
import os

# 1. Connect to DuckDB
db_path = "/home/aryan/Desktop/SOC/sat_sa.duckdb"
print(f"Connecting to database at: {db_path}")
con = duckdb.connect(db_path, read_only=True)

# 2. Query distinct alert categories per entity
query = """
    SELECT entity_id, category 
    FROM alerts 
    WHERE category IS NOT NULL
    GROUP BY entity_id, category
"""
df = con.execute(query).df()
con.close()

# 3. Determine the global "Peer Baseline" (all standard categories seen across the network)
all_categories = set(df['category'].unique())
print(f"Global categories detected across peers: {all_categories}")

findings = []

# 4. Find entities completely missing common categories
for entity, group in df.groupby('entity_id'):
    entity_categories = set(group['category'].unique())
    missing_categories = all_categories - entity_categories
    
    if missing_categories:
        findings.append({
            "entity_id": entity,
            "finding_type": "negative_space",
            "rule": "missing_alert_category",
            "value": f"Missing categories: {', '.join(missing_categories)}",
            "peer_baseline": "Peers successfully reporting these categories",
            "severity_score": 6.0, # Medium severity for missing category coverage
            "evidence_ids": []
        })

df_findings = pd.DataFrame(findings)

print(f"\nSuccessfully detected {len(df_findings)} missing-category gaps!")
if not df_findings.empty:
    print(df_findings.head(3))
    
    # 5. Save output
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "findings_missing_categories.csv")
    df_findings.to_csv(output_path, index=False)
    print(f"Saved findings to {output_path}")