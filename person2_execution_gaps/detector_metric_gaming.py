import duckdb
import pandas as pd
import numpy as np
import os

# 1. Connect directly to Person 1's DuckDB database
db_path = "/home/aryan/Desktop/SOC/sat_sa.duckdb"
print(f"Connecting to database at: {db_path}")
con = duckdb.connect(db_path, read_only=True)

# 2. Query closed alerts to inspect closure distribution times (e.g., hour of day or time-to-close near SLA)
query = """
    SELECT 
        alert_id,
        entity_id,
        assigned_analyst,
        created_at,
        closed_at,
        EXTRACT(HOUR FROM CAST(closed_at AS TIMESTAMP)) AS close_hour,
        EPOCH(CAST(closed_at AS TIMESTAMP) - CAST(created_at AS TIMESTAMP)) AS duration_seconds
    FROM alerts
    WHERE status = 'Closed' 
      AND closed_at IS NOT NULL 
      AND created_at IS NOT NULL
"""

df = con.execute(query).df()
con.close()

print(f"Loaded {len(df)} records for metric-gaming analysis.")

findings = []

# 3. Detect Shift-End / Bulk Closure Gaming (e.g., unusual spikes of closures at specific hours or mass closures)
# Group closures by analyst and closing hour to spot unnatural spikes
analyst_hourly = df.groupby(['assigned_analyst', 'close_hour']).size().reset_index(name='closure_count')

# If an analyst closes an abnormally high number of alerts in a single hour compared to their median rate, flag it
for analyst, group in analyst_hourly.groupby('assigned_analyst'):
    median_hourly = group['closure_count'].median()
    mad_hourly = np.median(np.abs(group['closure_count'] - median_hourly))
    
    threshold = median_hourly + (3 * (mad_hourly if mad_hourly > 0 else 1))
    
    spikes = group[group['closure_count'] > threshold]
    for idx, row in spikes.iterrows():
        # Find sample alerts contributing to this spike
        spike_alerts = df[(df['assigned_analyst'] == analyst) & (df['close_hour'] == row['close_hour'])]['alert_id'].tolist()[:5]
        
        findings.append({
            "entity_id": df[df['assigned_analyst'] == analyst]['entity_id'].iloc[0],
            "finding_type": "execution_gap",
            "rule": "metric_gaming_bulk_closures",
            "value": f"{row['closure_count']} closures in hour {row['close_hour']:02d}:00 (Shift-end spike)",
            "peer_baseline": f"Median hourly closures: {median_hourly:.1f}",
            "severity_score": 7.0,
            "evidence_ids": spike_alerts
        })

df_findings = pd.DataFrame(findings).drop_duplicates(subset=['value'])

print(f"\nSuccessfully detected {len(df_findings)} metric-gaming execution gaps!")
if not df_findings.empty:
    print(df_findings.head(3))
    
    # 4. Save findings for dashboard integration
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "findings_metric_gaming.csv")
    df_findings.to_csv(output_path, index=False)
    print(f"Saved findings to {output_path}")