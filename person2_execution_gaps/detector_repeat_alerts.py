import duckdb
import pandas as pd
import os

# 1. Connect directly to Person 1's DuckDB database using the absolute path
db_path = "/home/aryan/Desktop/SOC/sat_sa.duckdb"
print(f"Connecting to database at: {db_path}")
con = duckdb.connect(db_path, read_only=True)

# 2. Query to find assets experiencing multiple alerts where linked cases lack remediation
query = """
    SELECT 
        c.case_id,
        c.remediation_action,
        a.asset_id,
        a.entity_id,
        COUNT(a.alert_id) as alert_frequency
    FROM alerts a
    JOIN cases c ON CONTAINS(c.linked_alert_ids, a.alert_id)
    GROUP BY c.case_id, c.remediation_action, a.asset_id, a.entity_id
    HAVING COUNT(a.alert_id) >= 2
"""

df = con.execute(query).df()
con.close()

print(f"Analyzed asset alert clusters. Found {len(df)} candidate records.")

# 3. Format findings to the Shared Findings Contract
findings = []
for idx, row in df.iterrows():
    # Flag cases where remediation is empty, generic, or missing
    remediation = str(row['remediation_action']).strip()
    if not remediation or remediation.lower() == 'nan' or len(remediation) < 5:
        findings.append({
            "entity_id": row['entity_id'],
            "finding_type": "execution_gap",
            "rule": "repeat_alerts_no_remediation",
            "value": f"{row['alert_frequency']} repeat alerts on asset",
            "peer_baseline": "Required root-cause fix for recurring asset alerts",
            "severity_score": 8.0,
            "evidence_ids": [row['case_id'], row['asset_id']]
        })

df_findings = pd.DataFrame(findings)

print(f"\nSuccessfully detected {len(df_findings)} repeat-alert execution gaps!")
if not df_findings.empty:
    print(df_findings.head(3))
    
    # 4. Save the output findings in your folder for the dashboard integration
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "findings_repeat_alerts.csv")
    df_findings.to_csv(output_path, index=False)
    print(f"Saved findings to {output_path}")