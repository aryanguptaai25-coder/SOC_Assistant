import pandas as pd
import os
import glob

script_dir = os.path.dirname(os.path.abspath(__file__))
soc_root = os.path.abspath(os.path.join(script_dir, ".."))

# 1. Gather ALL findings across both Person 2 and Person 3 folders
person2_master = os.path.join(soc_root, "person2_execution_gaps", "master_execution_gap_findings.csv")
person3_files = glob.glob(os.path.join(script_dir, "findings_*.csv"))

all_dataframes = []

if os.path.exists(person2_master):
    all_dataframes.append(pd.read_csv(person2_master))
else:
    print("Warning: Person 2 master findings not found!")

for f in person3_files:
    all_dataframes.append(pd.read_csv(f))

if all_dataframes:
    # 2. Combine everything into one giant dataset
    master_findings = pd.concat(all_dataframes, ignore_index=True)
    
    # Save the ultimate master list for Person 4's dashboard
    master_output_path = os.path.join(soc_root, "master_all_findings.csv")
    master_findings.to_csv(master_output_path, index=False)
    print(f"Saved Global Master Findings to: {master_output_path}")
    
    # 3. Calculate Risk Scores by Entity (Sum of all severity scores)
    risk_scores = master_findings.groupby('entity_id')['severity_score'].sum().reset_index()
    risk_scores = risk_scores.sort_values(by='severity_score', ascending=False)
    risk_scores.rename(columns={'severity_score': 'total_risk_score'}, inplace=True)
    
    scores_output_path = os.path.join(script_dir, "entity_risk_scores.csv")
    risk_scores.to_csv(scores_output_path, index=False)
    
    print("\n--- FINAL ENTITY RISK RANKING ---")
    print(risk_scores.to_string(index=False))
    print(f"\nSaved Entity Risk Scores to: {scores_output_path}")