import duckdb
import pandas as pd
import os

# 1. Connect to DuckDB
db_path = "/home/aryan/Desktop/SOC/sat_sa.duckdb"
print(f"Connecting to database at: {db_path}")
con = duckdb.connect(db_path, read_only=True)

# 2. Query: Find Critical assets that have ZERO alerts
# We do a LEFT JOIN from assets to alerts. If alert_id is NULL, the asset has no alerts.
query = """
    SELECT 
        a.asset_id,
        a.entity_id,
        a.asset_type,
        a.criticality
    FROM assets a
    LEFT JOIN alerts al ON a.asset_id = al.asset_id
    WHERE a.criticality = 'Critical' 
      AND al.alert_id IS NULL
"""

df = con.execute(query).df()
con.close()

print(f"Scanned asset inventory. Found {len(df)} Silent Critical Assets (Zero Telemetry).")

# 3. Format into the Shared Findings Contract
findings = []
for idx, row in df.iterrows():
    findings.append({
        "entity_id": row['entity_id'],
        "finding_type": "negative_space",
        "rule": "silent_critical_asset",
        "value": f"0 alerts logged for {row['asset_type']}",
        "peer_baseline": "Continuous telemetry expected for all Critical assets",
        "severity_score": 9.0,  # High severity because a blind spot on a critical asset is dangerous
        "evidence_ids": [row['asset_id']]
    })

df_findings = pd.DataFrame(findings)

if not df_findings.empty:
    print("\nPreview of Findings:")
    print(df_findings.head(3))
    
    # 4. Save output
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "findings_silent_assets.csv")
    df_findings.to_csv(output_path, index=False)
    print(f"\nSaved findings to {output_path}")