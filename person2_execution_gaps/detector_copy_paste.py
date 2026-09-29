import duckdb
import pandas as pd
import numpy as np
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 1. Connect directly to Person 1's DuckDB database using the absolute path
db_path = "/home/aryan/Desktop/SOC/sat_sa.duckdb"
print(f"Connecting to database at: {db_path}")
con = duckdb.connect(db_path, read_only=True)

# 2. Query closed alerts containing closure notes
query = """
    SELECT 
        alert_id,
        entity_id,
        assigned_analyst,
        closure_note
    FROM alerts
    WHERE status = 'Closed' 
      AND closure_note IS NOT NULL 
      AND TRIM(closure_note) != ''
"""

df = con.execute(query).df()
con.close()

print(f"Loaded {len(df)} closed alerts with notes for copy-paste analysis.")

findings = []

# 3. Analyze notes per analyst using TF-IDF and Cosine Similarity
for analyst, group in df.groupby('assigned_analyst'):
    notes = group['closure_note'].tolist()
    alert_ids = group['alert_ids'] = group['alert_id'].tolist()
    entity_ids = group['entity_id'].tolist()
    
    if len(notes) < 5:
        continue # Skip analysts with too few notes to compare
        
    # Compute TF-IDF matrix for the notes
    vectorizer = TfidfVectorizer(stop_words='english')
    try:
        tfidf_matrix = vectorizer.fit_transform(notes)
    except ValueError:
        continue
        
    # Calculate pairwise cosine similarity between all notes by this analyst
    similarity_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)
    
    # Check for excessively high similarity (e.g., score >= 0.95, meaning identical template)
    n = len(notes)
    for i in range(n):
        for j in range(i + 1, n):
            if similarity_matrix[i, j] >= 0.95:
                findings.append({
                    "entity_id": entity_ids[i],
                    "finding_type": "execution_gap",
                    "rule": "copy_paste_closure_notes",
                    "value": f"High text similarity ({similarity_matrix[i, j]:.2f}) by analyst {analyst}",
                    "peer_baseline": "Unique investigative notes per incident",
                    "severity_score": 6.5,
                    "evidence_ids": [alert_ids[i], alert_ids[j]]
                })

df_findings = pd.DataFrame(findings).drop_duplicates(subset=['evidence_ids'])

print(f"\nSuccessfully detected {len(df_findings)} copy-paste/templated note execution gaps!")
if not df_findings.empty:
    print(df_findings.head(3))
    
    # 4. Save the findings for dashboard integration
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "findings_copy_paste.csv")
    df_findings.to_csv(output_path, index=False)
    print(f"Saved findings to {output_path}")