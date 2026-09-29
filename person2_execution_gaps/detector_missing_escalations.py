import duckdb
import pandas as pd
import os

# Connect to Person 1's DuckDB database
db_path = "/home/aryan/Desktop/SOC/sat_sa.duckdb"
con = duckdb.connect(db_path, read_only=True)

# Query critical alerts that were closed without escalation
query = """
    SELECT 
        alert_id,
        entity_id,
        asset_id,
        severity,
        status,
        escalated,
        escalated_at,
        assigned_analyst,
        closure_note
    FROM alerts
    WHERE severity = 'Critical' 
      AND status = 'Closed' 
      AND (escalated = FALSE OR escalated_at IS NULL)
"""

df_violations = con.execute(query).df()
con.close()

print(f"Detected {len(df_violations)} critical alerts closed without escalation.")

# Format findings to the Shared Findings Contract
findings = []
for idx, row in df_violations.iterrows():
    findings.append({
        "entity_id": row['entity_id'],
        "finding_type": "execution_gap",
        "rule": "critical_alert_no_escalation",
        "value": "Closed without escalation",
        "peer_baseline": "Mandatory Tier-2/3 Escalation for Criticals",
        "severity_score": 10.0, # Maximum severity for unescalated criticals
        "evidence_ids": [row['alert_id']]
    })

df_findings = pd.DataFrame(findings)

if not df_findings.empty:
    print(df_findings.head(3))
    
    # Save output for integration
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "findings_missing_escalations.csv")
    df_findings.to_csv(output_path, index=False)
    print(f"Saved findings to {output_path}")