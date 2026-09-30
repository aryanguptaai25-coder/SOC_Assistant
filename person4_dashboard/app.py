import streamlit as st
import pandas as pd
import sqlite3
import os
import ast

# Setup Paths
st.set_page_config(page_title="SAT-SA Dashboard", layout="wide")
script_dir = os.path.dirname(os.path.abspath(__file__))
soc_root = os.path.abspath(os.path.join(script_dir, ".."))

findings_path = os.path.join(soc_root, "master_all_findings.csv")
scores_path = os.path.join(soc_root, "person3_negative_space", "entity_risk_scores.csv")
db_path = os.path.join(script_dir, "audit_log.sqlite")

st.title(" SAT-SA: Supervisory Analytics Tool for SOC Assessment")
st.markdown("### Ranked Review Queue & Execution Gap Analysis")

# Load Data
@st.cache_data
def load_data():
    if os.path.exists(findings_path) and os.path.exists(scores_path):
        df_findings = pd.read_csv(findings_path)
        df_scores = pd.read_csv(scores_path)
        return df_findings, df_scores
    return None, None

df_findings, df_scores = load_data()

if df_findings is None:
    st.error("Data not found. Run Person 2 and Person 3 modules first.")
    st.stop()

# --- TAB 1: Entity Risk Ranking ---
tab1, tab2, tab3 = st.tabs(["Entity Risk Ranking", " Execution Gaps Review", " Audit Log"])

with tab1:
    st.subheader("Organizations Ranked by Risk Score")
    st.dataframe(df_scores.style.background_gradient(cmap='Reds', subset=['total_risk_score']), width='stretch')

# --- TAB 2: Review Queue ---
with tab2:
    st.subheader("Findings Review Queue")
    
    # Filter by Entity
    selected_entity = st.selectbox("Select Organization (Entity ID):", options=df_findings['entity_id'].unique())
    entity_data = df_findings[df_findings['entity_id'] == selected_entity]
    
    st.dataframe(entity_data[['finding_type', 'rule', 'value', 'severity_score', 'evidence_ids']], use_container_width=True)
    
    # Audit Logger UI
    st.markdown("### Log Review Action")
    with st.form("audit_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            reviewer = st.text_input("Reviewer Name", value="Supervisor_1")
            evidence_id = st.text_input("Evidence ID (e.g. ALERT-123)", value=entity_data['evidence_ids'].iloc[0] if not entity_data.empty else "")
        with col2:
            action = st.selectbox("Action Taken", ["WARNED_ANALYST", "ESCALATED_TO_MANAGEMENT", "MARKED_FALSE_POSITIVE", "REMEDIATION_ORDERED"])
            notes = st.text_area("Review Notes")
        
        submitted = st.form_submit_button("Submit Audit Log")
        if submitted:
            con = sqlite3.connect(db_path)
            cur = con.cursor()
            cur.execute('''
                INSERT INTO audit_log (reviewer_name, entity_id, evidence_id, finding_type, reviewer_action, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (reviewer, selected_entity, evidence_id, "Dashboard Review", action, notes))
            con.commit()
            con.close()
            st.success("Action permanently logged!")

# --- TAB 3: Audit Log ---
with tab3:
    st.subheader("Append-Only Audit Log")
    con = sqlite3.connect(db_path)
    df_audit = pd.read_sql_query("SELECT timestamp, reviewer_name, entity_id, reviewer_action, evidence_id FROM audit_log ORDER BY timestamp DESC", con)
    con.close()
    st.dataframe(df_audit, use_container_width=True)