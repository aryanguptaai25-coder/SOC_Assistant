import duckdb
import pandas as pd
import os
from sklearn.ensemble import IsolationForest

db_path = "/home/aryan/Desktop/SOC/sat_sa.duckdb"
con = duckdb.connect(db_path, read_only=True)

# 1. Extract entity-level features for the ML model
query = """
    SELECT 
        entity_id,
        COUNT(alert_id) AS total_alerts,
        COUNT(DISTINCT category) AS unique_categories,
        COUNT(DISTINCT asset_id) AS active_assets
    FROM alerts
    GROUP BY entity_id
"""
df = con.execute(query).df()
con.close()

# 2. Train the Isolation Forest Model
# contamination=0.1 means we expect roughly 10% of our entities to be anomalies
features = df[['total_alerts', 'unique_categories', 'active_assets']].fillna(0)
clf = IsolationForest(contamination=0.1, random_state=42)

# 3. Predict Anomalies (-1 means anomaly, 1 means normal)
df['anomaly_score'] = clf.fit_predict(features)

anomalies = df[df['anomaly_score'] == -1]

findings = []
for idx, row in anomalies.iterrows():
    findings.append({
        "entity_id": row['entity_id'],
        "finding_type": "ml_anomaly",
        "rule": "isolation_forest_outlier",
        "value": f"Anomalous pattern: {row['total_alerts']} alerts, {row['active_assets']} assets",
        "peer_baseline": "Standard multi-dimensional cluster",
        "severity_score": 7.5,
        "evidence_ids": []
    })

df_findings = pd.DataFrame(findings)

print(f"\nIsolation Forest caught {len(df_findings)} unknown-pattern anomalies!")
if not df_findings.empty:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "findings_ml_anomalies.csv")
    df_findings.to_csv(output_path, index=False)
    print(f"Saved findings to {output_path}")