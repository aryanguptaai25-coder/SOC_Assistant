# Person 2: Execution Gap Detection Methodology

## Overview
The Execution Gap module is designed to detect workflow manipulations, shortcuts, and metric-gaming behaviors within Security Operations Centers (SOCs). Rather than evaluating alerts purely on face value, these detectors uncover sloppy or gamed handling by analyzing operational timelines, escalation rules, remediation records, and analyst notes.

---

## Implemented Detectors & Rules

### 1. Fast Closure Outliers (`fast_closure_outlier`)
* **Objective:** Flag critical or high-severity alerts closed abnormally fast.
* **Methodology:** Computes robust statistical baselines—specifically the **Median** and **Median Absolute Deviation (MAD)**—for closure durations grouped by severity. Critical alerts resolved in under 90 seconds are flagged as execution gaps indicative of queue-clearing without genuine investigation.

### 2. Critical Alerts Without Escalation (`critical_alert_no_escalation`)
* **Objective:** Detect workflow rule violations on high-impact security incidents.
* **Methodology:** Scans for alerts where `severity = 'Critical'` and `status = 'Closed'` but `escalated` is `FALSE` or `escalated_at` is missing, identifying Tier-1 analysts bypassing mandatory Tier-2/3 review.

### 3. Repeat Alerts with No Remediation (`repeat_alerts_no_remediation`)
* **Objective:** Catch chronic underlying vulnerabilities left unpatched on recurring assets.
* **Methodology:** Cross-references the `alerts` and `cases` tables. Assets accumulating multiple recurring alerts whose linked case files contain blank or missing `remediation_action` fields are flagged.

### 4. Template / Copy-Paste Note Detection (`copy_paste_closure_notes`)
* **Objective:** Spot lazy or automated note-taking across distinct incidents.
* **Methodology:** Extracts analyst closure notes and utilizes **TF-IDF Vectorization** alongside **Cosine Similarity** to group clusters of identical or heavily templated text (`similarity >= 0.95`) authored by the same analyst.

### 5. Metric-Gaming & Bulk Closures (`metric_gaming_bulk_closures`)
* **Objective:** Identify artificial queue-clearing around shift changes or deadlines.
* **Methodology:** Analyzes hourly closure distributions per analyst, establishing a robust threshold (`Median + 3*MAD`) to flag unnatural spikes or bulk mass-closures.

---

## Shared Findings Contract Schema
Every detector programmatically emits structured findings adhering to the agreed team format:
`entity_id, finding_type, rule, value, peer_baseline, severity_score, evidence_ids[]`