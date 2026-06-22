# 📋 Project Task Board: Research-to-Project Radar

Use this file to track completed tasks, ongoing updates, and future feature implementations.

---

## 🛠️ Phase 1: Core MVP Setup (Completed)
- [x] **Project Scaffolding**: Setup Flask application structure, dependency files, and `.gitignore`.
- [x] **Database Initialization**: Setup SQLite schemas for ingested items and feed ingestion health tracking.
- [x] **Core Feeds Ingestion**: Implement robust concurrent XML/Atom fetching with timeouts using `feedparser` and `requests`.
- [x] **Ingestion Deduplication**: Ensure feed updates are matched against unique item URLs before inserting.
- [x] **Heuristic Scoring (1-5)**: Setup pattern matching rules to score papers based on AI, RAG, and agentic keywords.
- [x] **Heuristic Classifications**: Map incoming items to custom categories (e.g. Agentic AI, LLM Evaluation, Product Release Note).
- [x] **Action Hub Panel**: Create project blueprint templates, professional resume bullets, and short LinkedIn/X share cards.
- [x] **Research Saved Page**: Implement notes editing with debounced autosave and build status tags (e.g. To read, Reading, Build idea).
- [x] **Project Clusters Portfolio View**: Group blueprints by domain classifications and include a markdown resume-bullet copy widget.
- [x] **Security Auditing**: Sanitize repository and push MVP code to public GitHub repository: [alex-research-radar-app](https://github.com/a-elhajj/alex-research-radar-app).
- [x] **Date Sorting & Normalization**: Normalize inconsistent feed publication formats to standard UTC/ISO timestamps in the database, adding Ascending/Descending controls to the UI.

---

## 🚀 Phase 2: Next Steps & Feature Roadmap (Pending)
- [ ] **Semantic LLM Re-Scoring**:
  * Integrate lightweight Gemini API calls to parse paper abstracts.
  * Improve keyword heuristics with semantic rating of paper impact.
- [ ] **Automated Background Refresh**:
  * Implement cron tasks to trigger feed ingestion in the background automatically (e.g. every 12 hours).
- [ ] **Email/Webhook Digests**:
  * Create a daily or weekly brief outlining the top 5 highest-signal portfolio project opportunities.
- [ ] **Custom Feed Dashboard**:
  * Build a UI settings panel to add, remove, and test custom XML/RSS feeds directly inside the browser.
- [ ] **Static Assets Bundle Production Build**:
  * Optimize CSS & JS scripts for faster loading and responsiveness.
