import sqlite3
import os
import datetime

# 1. Setup paths
script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, "audit_log.sqlite")

def initialize_audit_db():
    """Create the audit log database if it doesn't exist."""
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            reviewer_name TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            evidence_id TEXT NOT NULL,
            finding_type TEXT NOT NULL,
            reviewer_action TEXT NOT NULL,
            notes TEXT
        )
    ''')
    con.commit()
    con.close()
    print(f"Audit log database verified at: {db_path}")

def log_action(reviewer, entity, evidence, finding, action, notes=""):
    """Securely append a new review action to the log."""
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    
    # We only INSERT (append). No UPDATE or DELETE allows for tamper evidence.
    cur.execute('''
        INSERT INTO audit_log 
        (reviewer_name, entity_id, evidence_id, finding_type, reviewer_action, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (reviewer, entity, evidence, finding, action, notes))
    
    con.commit()
    con.close()
    print(f"Successfully logged action: {action} on {evidence} by {reviewer}")

def view_logs():
    """Retrieve the recent audit logs."""
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 5")
    rows = cur.fetchall()
    con.close()
    return rows

if __name__ == "__main__":
    # Test the logger
    initialize_audit_db()
    
    print("\nSimulating a Supervisor Reviewing a Finding...")
    log_action(
        reviewer="Supervisor_Aryan",
        entity="ORG-7",
        evidence="ALERT-45992",
        finding="critical_alert_no_escalation",
        action="ESCALATED_TO_MANAGEMENT",
        notes="Confirmed Tier-1 analyst bypassed protocol. Warning issued."
    )
    
    print("\n--- RECENT AUDIT LOGS ---")
    logs = view_logs()
    for log in logs:
        print(f"[{log[1]}] {log[2]} -> {log[6]} (Evidence: {log[4]})")