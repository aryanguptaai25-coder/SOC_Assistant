import duckdb
import pandas as pd
import numpy as np
import os

# 1. Connect directly to Person 1's DuckDB database
db_path = "/home/aryan/Desktop/SOC/sat_sa.duckdb"
print(f"Connecting to database at: {db_path}")
con = duckdb.connect(db_path, read_only=True)

# 2. Query total alert volume per entity
query = """
    SELECT 
        entity_id,
        COUNT(alert_id) AS total_alerts
    FROM alerts
    GROUP BY entity_id
"""

df = con.execute(query).df()
con.close()

print(f"Analyzed alert volumes for {len(df)} entities.")

# 3. Calculate Peer Benchmarks using Robust Statistics (Median and MAD)
# We avoid using Mean (average) because a single noisy entity could ruin the baseline
median_volume = df['total_alerts'].median()
mad_volume = np.median(np.abs(df['total_alerts'] - median_volume))

print(f"Peer Baseline -> Median Alerts: {median_volume:.0f} | MAD: {mad_volume:.0f}")

# Define the threshold for suspiciously low activity (e.g., more than 2 MADs below the median)
low_threshold = max(0, median_volume - (2 * mad_volume))
print(f"Entities with fewer than {low_threshold:.0f} alerts will be flagged.")

findings = []

# 4. Flag anomalous entities
for idx, row in df.iterrows():
    if row['total_alerts'] < low_threshold:
        findings.append({
            "entity_id": row['entity_id'],
            "finding_type": "negative_space",
            "rule": "low_activity_entity",
            "value": f"{row['total_alerts']} total alerts",
            "peer_baseline": f"Median: {median_volume:.0f}",
            "severity_score": 8.5,  # High severity for widespread telemetry failure
            "evidence_ids": [] # No specific alert IDs to list, the issue is the LACK of alerts
        })

df_findings = pd.DataFrame(findings)

print(f"\nSuccessfully detected {len(df_findings)} low-activity execution gaps!")
if not df_findings.empty:
    print(df_findings.head())
    
    # 5. Save the findings for dashboard integration
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "findings_low_activity.csv")
    df_findings.to_csv(output_path, index=False)
    print(f"Saved findings to {output_path}")