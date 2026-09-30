SAT-SA: Supervisory Analytics Tool for SOC Assessment

Build Plan (SIH26157)

SAT-SA is an offline, air-gapped analytics tool designed to audit Security Operations Centers (SOCs). It takes alert and case records from multiple organizations and helps a human supervisor decide which organization needs attention, which specific cases to review, and why, with evidence attached.

It does not monitor in real-time and is not a SIEM. It detects:

1. Execution Gaps: Workflow data showing sloppy or gamed handling (e.g., critical alerts closed in 90 seconds, missing escalations, copy-pasted notes).
2. Negative Space: Evidence that should exist but doesn't (e.g., critical assets with zero alerts, entities falling far below peer activity baselines).

Data and Handoff
Due to GitHub's size limitations, the sat_sa.duckdb database (containing 100,000+ synthetic alerts) and the validation ground truth files are hosted externally.

Download the Data Here:
Google Drive Data Folder: [https://drive.google.com/drive/folders/1Uv_IYDz1e-TMFmKjxCz_zJpQKAGl5zQX?usp=sharing](https://drive.google.com/drive/folders/1Uv_IYDz1e-TMFmKjxCz_zJpQKAGl5zQX?usp=sharing)

Instructions:
Download all files from the Drive link and place them in the root directory of this repository before running the application.

Architecture and Separation of Concerns

The tool was built using a modular, four-phase pipeline:

* Person 1 (Ingestion): Generated 100,000+ synthetic alerts across 10 entities, planted specific labeled flaws (ground truth), and loaded the data into an offline DuckDB backend.
* Person 2 (Execution Gaps): Built robust statistical detectors (Median/MAD, Cosine Similarity) to catch fast closures, missing escalations, and metric gaming.
* Person 3 (Negative Space and ML): Built detectors for silent critical assets and low-activity entities, implemented an Isolation Forest ML model for unknown anomalies, and designed the entity Risk Scoring Engine.
* Person 4 (Dashboard and Audit): Built the Streamlit UI, the validation engine (Precision/Recall vs Ground Truth), and an append-only SQLite database for tamper-proof supervisor audit logging.

Offline Setup and Execution

SAT-SA is designed to run fully offline on standard hardware.

Prerequisites

* Python 3.9+
* pip package manager

1. Install Dependencies
pip install -r requirements.txt
(Required packages: duckdb, pandas, numpy, scikit-learn, streamlit, matplotlib)
2. Run the Analytics Pipeline
Generate the master findings and risk scores:
python person2_execution_gaps/detector_fast_closures.py
python person3_negative_space/scoring_engine.py
3. Launch the Supervisor Dashboard
Launch the interactive Streamlit interface:
streamlit run person4_dashboard/app.py
4. Run the Validation Engine
Verify the tool's precision and recall against the intentionally planted flaws:
python person4_dashboard/validation_engine.py
