import pandas as pd
import random
import uuid
from faker import Faker
from datetime import datetime, timedelta

fake = Faker()

# Configuration
NUM_ENTITIES = 12
NUM_ASSETS = 500
NUM_ALERTS = 105000 
NUM_CASES = 5000
START_DATE = datetime(2026, 1, 1)
END_DATE = datetime(2026, 9, 29) # Current date

# Helper to generate random timestamps
def random_date(start, end):
    return start + timedelta(
        seconds=random.randint(0, int((end - start).total_seconds())),
    )

# 1. Generate Entities (Organizations)
print("Generating Entities...")
entities = [f"ENT_{str(i).zfill(3)}" for i in range(1, NUM_ENTITIES + 1)]

# 2. Generate Asset Inventory
print("Generating Asset Inventory...")
asset_types = ["Server", "Workstation", "Database", "Firewall", "Router", "Cloud Storage"]
criticalities = ["Low", "Medium", "High", "Critical"]
environments = ["Production", "Staging", "Development", "Corp"]

assets_data = []
for _ in range(NUM_ASSETS):
    assets_data.append({
        "asset_id": f"AST_{uuid.uuid4().hex[:8].upper()}",
        "entity_id": random.choice(entities), # Link asset to an entity
        "asset_type": random.choice(asset_types),
        "criticality": random.choices(criticalities, weights=[40, 30, 20, 10])[0], 
        "environment": random.choices(environments, weights=[50, 20, 15, 15])[0]
    })
df_assets = pd.DataFrame(assets_data)

# 3. Generate Alerts
print("Generating Alerts...")
source_tools = ["CrowdStrike", "Splunk", "AWS GuardDuty", "Palo Alto", "Azure Sentinel"]
categories = ["Malware", "Phishing", "Unauthorized Access", "Data Exfiltration", "Privilege Escalation", "Reconnaissance"]
severities = ["Low", "Medium", "High", "Critical"]
statuses = ["Open", "Investigating", "Closed"]
dispositions = ["True Positive", "False Positive", "Benign True Positive"]
analysts = [fake.name() for _ in range(20)] # Pool of 20 SOC analysts

alerts_data = []
for i in range(NUM_ALERTS):
    created_at = random_date(START_DATE, END_DATE)
    
    # Logic for timestamps based on status
    status = random.choices(statuses, weights=[5, 10, 85])[0]
    
    if status != "Open":
       acknowledged_at = created_at + timedelta(minutes=random.randint(5, 60))
    else:
       acknowledged_at = None
       
    if status == "Closed":
        closed_at = acknowledged_at + timedelta(minutes=random.randint(15, 1440)) # 15 mins to 24 hrs
        disposition = random.choice(dispositions)
        closure_note = fake.sentence(nb_words=10)
    else:
        closed_at = None
        disposition = None
        closure_note = None

    escalated = random.choice([True, False]) if status == "Closed" else False
    escalated_at = acknowledged_at + timedelta(minutes=random.randint(10, 120)) if escalated else None

    # Pick a random asset and get its entity
    asset = random.choice(assets_data)

    alerts_data.append({
        "alert_id": f"ALT_{uuid.uuid4().hex[:8].upper()}",
        "entity_id": asset["entity_id"],
        "asset_id": asset["asset_id"],
        "asset_criticality": asset["criticality"],
        "source_tool": random.choice(source_tools),
        "category": random.choice(categories),
        "severity": random.choices(severities, weights=[50, 30, 15, 5])[0],
        "created_at": created_at.isoformat(),
        "acknowledged_at": acknowledged_at.isoformat() if acknowledged_at else None,
        "closed_at": closed_at.isoformat() if closed_at else None,
        "status": status,
        "disposition": disposition,
        "escalated": escalated,
        "escalated_at": escalated_at.isoformat() if escalated_at else None,
        "assigned_analyst": random.choice(analysts),
        "closure_note": closure_note
    })
df_alerts = pd.DataFrame(alerts_data)

# 4. Generate Cases
print("Generating Cases...")
cases_data = []
for _ in range(NUM_CASES):
    # Link 1 to 5 random closed alerts to this case
    linked_alerts = df_alerts[df_alerts['status'] == 'Closed'].sample(n=random.randint(1, 5))
    linked_alert_ids = linked_alerts['alert_id'].tolist()
    
    # Determine case timestamps based on the linked alerts
    opened_at_datetime = datetime.fromisoformat(linked_alerts['created_at'].min())
    closed_at_datetime = opened_at_datetime + timedelta(days=random.randint(1, 14))

    cases_data.append({
        "case_id": f"CAS_{uuid.uuid4().hex[:8].upper()}",
        "linked_alert_ids": str(linked_alert_ids), 
        "opened_at": opened_at_datetime.isoformat(),
        "investigation_steps": fake.paragraph(nb_sentences=3),
        "escalated_to": random.choice(["Tier 2", "Tier 3", "Incident Response", None]),
        "root_cause": fake.sentence(),
        "remediation_action": fake.sentence(),
        "closed_at": closed_at_datetime.isoformat(),
        "closure_reason": random.choice(["Remediated", "Risk Accepted", "False Positive"])
    })
df_cases = pd.DataFrame(cases_data)

# Save to CSVs for inspection before database load
df_assets.to_csv("asset_inventory.csv", index=False)
df_alerts.to_csv("alerts.csv", index=False)
df_cases.to_csv("cases.csv", index=False)

print("Baseline data generation complete. Saved to CSVs.")