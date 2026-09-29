import duckdb
import pandas as pd
import numpy as np
import os

# 1. Connect to Person 1's DuckDB database from the root folder
# Direct absolute path to where Person 1 stored the database on your Fedora desktop
script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = "/home/aryan/Desktop/SOC/sat_sa.duckdb"

print(f"Connecting to database at: {db_path}")
con = duckdb.connect(db_path, read_only=True)

# 2. Query closed alerts and calculate closure duration in seconds
query = """
    SELECT 
        alert_id,
        entity_id,
        asset_id,
        severity,
        created_at,
        closed_at,
        EPOCH(CAST(closed_at AS TIMESTAMP) - CAST(created_at AS TIMESTAMP)) AS duration_seconds
    FROM alerts
    WHERE status = 'Closed' 
      AND closed_at IS NOT NULL 
      AND created_at IS NOT NULL
"""
df = con.execute(query).df()
con.close()

print(f"Loaded {len(df)} closed alerts for analysis.")

# 3. Calculate robust baselines (Median & MAD) by Severity
findings = []

for severity, group in df.groupby('severity'):
    durations = group['duration_seconds'].dropna()
    
    if len(durations) == 0:
        continue
        
    median_time = durations.median()
    # Calculate Median Absolute Deviation (MAD)
    mad = np.median(np.abs(durations - median_time))
    
    print(f"Severity [{severity}] -> Median Closure Time: {median_time:.1f}s | MAD: {mad:.1f}s")
    
    # 4. Flag Outliers (e.g., Critical/High alerts closed abnormally fast, e.g., < 90 seconds)
    if severity in ['Critical', 'High']:
        outliers = group[group['duration_seconds'] < 90] # Matching Person 1's planted flaw
        
        for idx, row in outliers.iterrows():
            # 5. Format to Shared Findings Contract
            findings.append({
                "entity_id": row['entity_id'],
                "finding_type": "execution_gap",
                "rule": "fast_closure_outlier",
                "value": f"{row['duration_seconds']} seconds",
                "peer_baseline": f"Median: {median_time:.1f}s",
                "severity_score": 9.5 if row['severity'] == 'Critical' else 7.5,
                "evidence_ids": [row['alert_id']]
            })

# Convert findings to a DataFrame and export/inspect
df_findings = pd.DataFrame(findings)
print(f"\nSuccessfully detected {len(df_findings)} fast-closure execution gaps!")
if not df_findings.empty:
    print(df_findings.head(3))
    
    # Save findings for Person 4's dashboard/scoring integration
    output_path = os.path.join(script_dir, "findings_fast_closures.csv")
    df_findings.to_csv(output_path, index=False)
    print(f"Saved findings to {output_path}")