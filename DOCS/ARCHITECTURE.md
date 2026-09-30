SAT-SA: Supervisory Analytics Tool for SOC Assessment
Architecture and Machine Learning Overview
What this system is for

SAT-SA helps supervisors audit Security Operations Centers. It looks through historical alert and case records from several organizations and points out where things may have gone wrong: shortcuts in how analysts handled incidents, processes that broke down, and places where data that should exist simply isn't there.

It is an auditing tool, not a monitoring one. It runs entirely offline, on data you've already collected, and doesn't connect to a live SIEM or to anything outside the machine it's running on.

How it's built

The system is split into four pipelines, each with one job: getting data in, catching sloppy work, finding what's missing, and presenting the results.

**Phase 1: Getting the data in
**
Every organization keeps its records differently, so the first step is making them comparable. This layer takes alerts, cases, and asset inventories in whatever format they arrive, then uses a column-mapping configuration to translate them into one common schema.

Everything is stored in DuckDB, an embedded analytical database that runs locally. It handles well over 100,000 records comfortably and needs no database server.

**Phase 2: Spotting sloppy or gamed work
**
This engine looks at how analysts handle incidents and flags patterns that suggest corners are being cut or metrics are being gamed. It looks for:

Suspiciously fast closures on high-severity incidents
Missing escalation records on critical alerts that should have been escalated
Repeat alerts that keep firing without anyone fixing the root cause
Copy-paste closure notes, found by turning notes into TF-IDF vectors and grouping those with high cosine similarity

To decide what counts as "unusual", it uses the median and the median absolute deviation (MAD) rather than the mean and standard deviation. A few extreme values can badly skew an average, but they barely move a median, so the baselines stay trustworthy.

**Phase 3: Finding what's missing
**
Some of the most telling problems are things that aren't in the data. This engine looks for absences that shouldn't be there:

Silent critical assets. It scans the asset inventory for important systems that have produced no telemetry or alerts at all.
Quiet organizations. It builds peer-group baselines for alert volume (again using robust statistics) and flags entities whose activity is unusually low, which often means a telemetry blackout or a broken log forwarder.
Coverage gaps. It compares each organization's alert categories against global peer baselines to see which types of threats it isn't detecting.
**Phase 4: Validation, audit trail, and dashboard
**
This last layer checks the work and makes it usable.

Validation. An automated engine compares detector findings with ground-truth injection logs and calculates precision and recall, so we know how well the detectors perform.
Audit log. Every supervisor review action, note, and timestamp goes into an append-only SQLite database. Entries can't be quietly changed later, which gives you a tamper-evident record.
Dashboard. A Streamlit web interface shows entity risk rankings and review queues, and lets supervisors drill into the evidence behind any finding.
The machine learning component
The model

For unsupervised anomaly detection we use an Isolation Forest. It works by repeatedly picking a random feature and a random split value, building trees that carve up the data. Unusual points are easy to separate from the rest, so they end up isolated after only a few splits. A shorter path through the tree means a higher anomaly score.

What it looks at

The model works at the entity level, using three features aggregated from DuckDB:

Total alert volume per organization
Number of distinct alert categories reported
Number of distinct active assets producing telemetry
What it runs on

A standard laptop or supervisor workstation is enough (Intel/AMD x86_64 or Apple Silicon, with at least 8 GB of RAM). Everything runs on the CPU, and training and inference finish in under 5 seconds even on datasets larger than 100,000 records. No GPU is needed.

Training, updates, and deployment
Training happens locally in batch mode when the pipeline starts. Nothing goes to the cloud, no external APIs are called, and no telemetry leaves the machine.
Updates are on demand. Whenever new organizational data is loaded into DuckDB, the model is retrained locally.
Serialization uses joblib, so fitted models can be saved and reloaded for reproducible offline results.
Explainability and auditability

A bare anomaly score isn't much use to a supervisor, so each flagged entity comes with the specific feature deviations behind it, such as unusually low alert counts or a narrow range of alert categories. That makes it clear why the entity was flagged.

Every model prediction, detector finding, and human review action is permanently recorded in the append-only SQLite log, so anything can be traced back during a compliance check or post-assessment review.