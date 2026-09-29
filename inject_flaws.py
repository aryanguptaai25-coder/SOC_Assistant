import pandas as pd
import random
import os
from datetime import timedelta

# VS Code will automatically resolve this to /home/aryan/Desktop/SOC/
script_dir = os.path.dirname(os.path.abspath(__file__))
assets_path = os.path.join(script_dir, "asset_inventory.csv")
alerts_path = os.path.join(script_dir, "alerts.csv")
cases_path = os.path.join(script_dir, "cases.csv")
ground_truth_path = os.path.join(script_dir, "ground_truth.csv")

print("Loading baseline data...")
df_assets = pd.read_csv(assets_path)
df_alerts = pd.read_csv(alerts_path)
df_cases = pd.read_csv(cases_path)

# Ensure timestamps are parsed properly
df_alerts['created_at'] = pd.to_datetime(df_alerts['created_at'])
df_alerts['acknowledged_at'] = pd.to_datetime(df_alerts['acknowledged_at'])
df_alerts['closed_at'] = pd.to_datetime(df_alerts['closed_at'])

ground_truth = []

# --- 1. Flaw: Fast Closures (Execution Gap) ---
print("Planting Flaw: Fast Closures...")
fast_closure_candidates = df_alerts[(df_alerts['severity'] == 'Critical') & (df_alerts['status'] == 'Closed')].sample(n=100)
for idx, row in fast_closure_candidates.iterrows():
    fast_close_time = row['created_at'] + timedelta(seconds=random.randint(60, 120))
    df_alerts.at[idx, 'closed_at'] = fast_close_time
    df_alerts.at[idx, 'acknowledged_at'] = row['created_at'] + timedelta(seconds=random.randint(10, 45))
    
    ground_truth.append({
        "flaw_type": "fast_closure",
        "reference_id": row['alert_id'],
        "entity_id": row['entity_id']
    })

# --- 2. Flaw: No escalation on critical alerts (Execution Gap) ---
print("Planting Flaw: No Escalation on Critical Alerts...")
no_escalation_candidates = df_alerts[(df_alerts['severity'] == 'Critical') & (df_alerts['status'] == 'Closed') & (df_alerts['escalated'] == True)].sample(n=150)
for idx, row in no_escalation_candidates.iterrows():
    df_alerts.at[idx, 'escalated'] = False
    df_alerts.at[idx, 'escalated_at'] = pd.NaT
    
    ground_truth.append({
        "flaw_type": "missing_escalation",
        "reference_id": row['alert_id'],
        "entity_id": row['entity_id']
    })

# --- 3. Flaw: Copy-paste notes (Execution Gap) ---
print("Planting Flaw: Copy-Paste Notes...")
lazy_analysts = random.sample(df_alerts['assigned_analyst'].dropna().unique().tolist(), 5)
canned_note = "Review completed. No malicious activity found. Proceeding with closure based on standard operating procedure guidelines."

for analyst in lazy_analysts:
    analyst_alerts = df_alerts[(df_alerts['assigned_analyst'] == analyst) & (df_alerts['status'] == 'Closed')].head(20)
    for idx, row in analyst_alerts.iterrows():
        df_alerts.at[idx, 'closure_note'] = canned_note
        ground_truth.append({
            "flaw_type": "copy_paste_notes",
            "reference_id": row['alert_id'],
            "entity_id": row['entity_id']
        })

# --- 4. Flaw: Silent Critical Assets (Negative Space) ---
print("Planting Flaw: Silent Critical Assets...")
critical_assets = df_assets[df_assets['criticality'] == 'Critical']
silent_assets = critical_assets.sample(n=10)
for idx, asset in silent_assets.iterrows():
    df_alerts = df_alerts[df_alerts['asset_id'] != asset['asset_id']]
    ground_truth.append({
        "flaw_type": "silent_critical_asset",
        "reference_id": asset['asset_id'],
        "entity_id": asset['entity_id']
    })

# --- 5. Flaw: Low-Activity Entities (Negative Space) ---
print("Planting Flaw: Low-Activity Entities...")
all_entities = df_assets['entity_id'].unique()
low_activity_entities = random.sample(list(all_entities), 2)

for entity in low_activity_entities:
    entity_alerts = df_alerts[df_alerts['entity_id'] == entity]
    alerts_to_drop = entity_alerts.sample(frac=0.98).index
    df_alerts = df_alerts.drop(alerts_to_drop)
    ground_truth.append({
        "flaw_type": "low_activity_entity",
        "reference_id": entity,
        "entity_id": entity
    })

# --- Save Poisoned Data and Ground Truth ---
print("Saving poisoned datasets and ground truth file...")
df_alerts['created_at'] = df_alerts['created_at'].dt.strftime('%Y-%m-%dT%H:%M:%S')
df_alerts['acknowledged_at'] = df_alerts['acknowledged_at'].dt.strftime('%Y-%m-%dT%H:%M:%S')
df_alerts['closed_at'] = df_alerts['closed_at'].dt.strftime('%Y-%m-%dT%H:%M:%S')

df_alerts.to_csv(os.path.join(script_dir, "alerts_poisoned.csv"), index=False)
df_assets.to_csv(os.path.join(script_dir, "asset_inventory_poisoned.csv"), index=False)
df_cases.to_csv(os.path.join(script_dir, "cases_poisoned.csv"), index=False)

df_ground_truth = pd.DataFrame(ground_truth)
df_ground_truth.to_csv(ground_truth_path, index=False)

print(f"Flaw injection complete! Files saved directly to your workspace.")
print(f"Total flaws injected: {len(df_ground_truth)}")