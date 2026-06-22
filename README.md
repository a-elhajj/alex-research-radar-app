# Research-to-Project Radar

A premium, cyber-themed personal AI research and engineering radar designed to monitor AI research feeds (ArXiv), developer blogs, and cloud release notes. It dynamically scores updates based on utility, automatically indexes them, and maps them to concrete portfolio projects, resume bullet templates, and social media posts.

## Core Tech Stack
* **Backend:** Python Flask, SQLite
* **Ingestion:** Feedparser, Requests (with timeouts)
* **Frontend:** Vanilla HTML5, Vanilla CSS3 (custom CSS design system with Glassmorphism, animations, responsive grid), Vanilla JavaScript (ES6)

---

## Getting Started

### 1. Prerequisite Packages
Verify you have python3 and pip installed.

### 2. Install Dependencies
Run:
```bash
pip install -r requirements.txt
```

### 3. Initialize & Launch the Application
Run the Flask server:
```bash
python app.py
```
By default, the server runs on `http://127.0.0.1:5001`. Open it in your web browser.

---

## Project Structure
```
├── app.py                   # Main Flask application with API & database logic
├── requirements.txt         # Project package requirements
├── config/
│   └── feeds.py             # Feed addresses configuration
├── static/
│   ├── app.js               # Main page rendering, filtering, dynamic actions
│   └── style.css            # Premium Cyber-Dark Glassmorphism stylesheet
└── templates/
    ├── base.html            # Base structural layout with Sidebar and Health status modal
    ├── index.html           # Discovery Radar Dashboard
    ├── saved.html           # Saved items and research notes manager
    ├── projects.html        # Portfolio projects clustered blueprints
    └── item.html            # Detailed feed updates metadata viewer
```

---

## Features Guide

### 1. Feed Syncing & Ingestion
* Feeds are fetched concurrently using `requests` with a strict `10` seconds timeout constraint to prevent blocking.
* Deduplication checks each item's URL to avoid duplicates.
* Click the **Sync Feeds** button at the top right of the dashboard. The status indicator will display the progress of active feed downloads in the background.

### 2. Monitoring Feed Health
* Click **Feed Health Status** in the bottom-left sidebar.
* A detailed modal opens showing the refresh history, status (`SUCCESS` / `FAILED`), and any error messages for each endpoint.

### 3. Signal Scoring (1 to 5 Scale)
The system parses the titles and abstracts of feeds, looking for specific high-value keywords to compute relevance scores:
* **5 (Highly Critical/Actionable):** Directly relevant keywords like `agents`, `rag`, `evaluation`, `vector database`, `tool use`, `planning`, `Vertex AI`, etc.
* **4 (Valuable AI/Data Engineering):** Key terms like `llm`, `fine-tuning`, `MLOps`, `data pipeline`, `Cloud Run`, `serverless`.
* **3 (Maybe Relevant):** General computing/ML words like `machine learning`, `deep learning`, `analytics`.
* **2 (Low Priority):** General developer terms or general system mentions.
* **1 (Ignore):** Minimal or zero AI/ML/Cloud context.

### 4. Classification & Blueprints
* Classification tags are dynamically assigned based on pattern matching rules.
* For all high-signal items (Score >= 4), the **Action Hub** can generate:
  * A full **Project Roadmap** (title, mvp scope, target tools, and difficulty).
  * A **Resume Bullet Draft** tailored to that roadmap.
  * Professional but authentic **LinkedIn** or short **X** posts ready for sharing.

### 5. Customizing Feeds
To add or modify RSS feeds, edit [config/feeds.py](file:///Users/alexanderel-hajj/ai_agents_intensive_course/antigravity-cli-projects/bq-releases-notes/config/feeds.py). Add an object containing:
```python
{
    "url": "https://example.com/feed.xml",
    "name": "My Custom Feed Name",
    "group": "ai-lab", # Group label: 'arxiv', 'ai-lab', or 'cloud-infra'
    "category": None   # Category string if applicable
}
```

### 6. Resetting the Database
To clear all data, delete the SQLite file:
```bash
rm data/radar.db
```
The application will automatically recreate the empty tables upon the next launch.
