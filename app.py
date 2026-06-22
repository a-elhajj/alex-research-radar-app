import os
import re
import datetime
import sqlite3
import threading
import json
import requests
import feedparser
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, jsonify, redirect, url_for

from config.feeds import FEEDS

app = Flask(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'radar.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Global refresh lock/status
is_refreshing = False
refresh_status_msg = ""
refresh_lock = threading.Lock()

# Define keywords
TIER_5_KEYWORDS = [
    r'\bagents?\b', r'\bagentic\b', r'\btool use\b', r'\bplanning\b', r'\breasoning\b', 
    r'\bmulti-agent\b', r'\bmemory\b', r'\brag\b', r'\bretrieval\b', r'\bvector database\b', 
    r'\bvector search\b', r'\bbenchmark\b', r'\bevaluation\b', r'\beval\b', r'\bhallucination\b', 
    r'\bsafety\b', r'\bgovernance\b', r'\blanggraph\b', r'\breact\b', r'\bmcp\b', 
    r'\bbigquery ml\b', r'\bvertex ai\b', r'\bgemini\b', r'\bmodel serving\b', 
    r'\bmodel deployment\b', r'\bagent governance\b'
]

TIER_4_KEYWORDS = [
    r'\bllm\b', r'\blanguage model\b', r'\btransformer\b', r'\bfine-tuning\b', r'\bpeft\b', 
    r'\blora\b', r'\bdistillation\b', r'\borchestration\b', r'\bworkflow\b', r'\bcloud run\b', 
    r'\bserverless\b', r'\bobservability\b', r'\btracing\b', r'\bml pipeline\b', 
    r'\bdata pipeline\b', r'\bfeature store\b', r'\bsecurity\b', r'\biam\b', r'\bgke\b', 
    r'\bkubernetes\b', r'\bbigquery\b', r'\bdataflow\b', r'\bpub/sub\b', r'\bpubsub\b'
]

TIER_3_KEYWORDS = [
    r'\bmachine learning\b', r'\bdeep learning\b', r'\bdataset\b', r'\bneural network\b', 
    r'\boptimization\b', r'\bcloud\b', r'\bapi\b', r'\bdatabase\b', r'\banalytics\b'
]

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # Create items table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            source TEXT NOT NULL,
            source_url TEXT,
            item_url TEXT UNIQUE NOT NULL,
            published_date TEXT,
            summary TEXT,
            authors TEXT,
            categories TEXT,
            fetched_at TEXT,
            signal_score INTEGER DEFAULT 1,
            classification_tags TEXT,
            status TEXT DEFAULT 'unread',
            user_notes TEXT,
            why_matters TEXT,
            project_title TEXT,
            project_why TEXT,
            project_scope TEXT,
            project_tools TEXT,
            project_difficulty TEXT,
            project_resume TEXT,
            project_status TEXT,
            project_cluster TEXT
        )
    ''')
    # Create feed_health table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS feed_health (
            url TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            last_status TEXT,
            last_success_at TEXT,
            error_message TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Ingest and classify utilities
def clean_html(html_content):
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text(separator=" ").strip()

def compute_signal_score(title, summary):
    text = f"{title} {summary}".lower()
    
    # Check Tier 5
    for kw in TIER_5_KEYWORDS:
        if re.search(kw, text):
            return 5
            
    # Check Tier 4
    for kw in TIER_4_KEYWORDS:
        if re.search(kw, text):
            return 4
            
    # Check Tier 3
    for kw in TIER_3_KEYWORDS:
        if re.search(kw, text):
            return 3
            
    # Check if there is some general AI match
    if 'ai' in text or 'ml' in text or 'model' in text or 'cloud' in text:
        return 2
        
    return 1

def classify_item(title, summary, is_arxiv, is_cloud):
    text = f"{title} {summary}".lower()
    tags = []
    
    if is_arxiv:
        tags.append("Research Paper")
    if is_cloud:
        tags.append("Product Release Note")
        
    # Check specific tags
    if any(re.search(kw, text) for kw in [r'\bagents?\b', r'\bagentic\b', r'\bplanning\b', r'\breasoning\b', r'\bmemory\b', r'\breact\b', r'\blanggraph\b', r'\bmcp\b']):
        tags.append("Agentic AI")
    if any(re.search(kw, text) for kw in [r'\bmulti-agent\b', r'\bmultiagent\b', r'\bswarm\b', r'\bcollaboration\b']):
        tags.append("Multi-Agent Systems")
    if any(re.search(kw, text) for kw in [r'\brag\b', r'\bretrieval\b', r'\bvector database\b', r'\bvector search\b', r'\bembeddings\b', r'\bsemantic search\b']):
        tags.append("RAG / Retrieval")
    if any(re.search(kw, text) for kw in [r'\bevaluation\b', r'\beval\b', r'\bevals\b', r'\bbenchmark\b', r'\bhallucination\b', r'\baccuracy\b']):
        tags.append("LLM Evaluation")
    if any(re.search(kw, text) for kw in [r'\bfine-tuning\b', r'\bpre-training\b', r'\bpretraining\b', r'\blora\b', r'\bpeft\b', r'\bdistillation\b', r'\bquantization\b', r'\brlhf\b', r'\bdpo\b']):
        tags.append("LLM Training / Fine-tuning")
    if any(re.search(kw, text) for kw in [r'\bmodel serving\b', r'\binference\b', r'\bserving\b', r'\bvllm\b', r'\btgi\b', r'\bollama\b']):
        tags.append("Model Serving / Inference")
    if any(re.search(kw, text) for kw in [r'\bmlops\b', r'\bml pipeline\b', r'\bfeature store\b', r'\bobservability\b', r'\btracing\b', r'\bweights & biases\b', r'\bmlflow\b']):
        tags.append("MLOps")
    if any(re.search(kw, text) for kw in [r'\bdata engineering\b', r'\bdata pipeline\b', r'\betl\b', r'\belt\b', r'\bdataflow\b', r'\bpub/sub\b', r'\bpubsub\b', r'\bkafka\b', r'\bspark\b']):
        tags.append("Data Engineering")
    if any(re.search(kw, text) for kw in [r'\bbigquery\b', r'\banalytics\b', r'\bdata warehouse\b', r'\bsql\b']):
        tags.append("BigQuery / Analytics")
    if any(re.search(kw, text) for kw in [r'\bvertex ai\b', r'\bvertex\b', r'\bgemini\b', r'\bpalm\b', r'\bduet ai\b']):
        tags.append("Vertex AI / Google Cloud AI")
    if any(re.search(kw, text) for kw in [r'\bcloud infrastructure\b', r'\bcloud run\b', r'\bserverless\b', r'\bgke\b', r'\bkubernetes\b', r'\bdocker\b', r'\bterraform\b']):
        tags.append("Cloud Infrastructure")
    if any(re.search(kw, text) for kw in [r'\bsecurity\b', r'\biam\b', r'\bgovernance\b', r'\bsafety\b', r'\bguardrails\b', r'\bred teaming\b', r'\bprivacy\b', r'\bsecret manager\b']):
        tags.append("Security / IAM / Governance")
    if any(re.search(kw, text) for kw in [r'\bsoftware engineering\b', r'\bgit\b', r'\bci/cd\b', r'\btesting\b', r'\bdevelopment framework\b']):
        tags.append("Software Engineering for AI")
        
    if not tags:
        tags.append("Other")
        
    return list(set(tags))

def generate_why_matters(title, summary, tags, score):
    if score >= 4:
        if "Agentic AI" in tags or "Multi-Agent Systems" in tags:
            return "This is high-signal because it connects to agent planning and evaluation. It could be useful for building a small benchmark or portfolio demo around multi-step LLM tool use."
        elif "RAG / Retrieval" in tags:
            return "This is high-signal because it addresses key retrieval or RAG challenges. Understanding this helps optimize vector indexing, retrieval quality, or context usage in production LLM applications."
        elif "LLM Evaluation" in tags:
            return "This is high-signal because it focuses on LLM evaluation or benchmarking. Rigorous evals are critical to moving agents and RAG pipelines into production."
        elif "Vertex AI / Google Cloud AI" in tags or "BigQuery / Analytics" in tags:
            return "This update bridges cloud data and enterprise AI. It provides an excellent template for building serverless AI analytics pipelines."
        else:
            return "This is a relevant update in cloud/AI infrastructure that helps streamline model deployment, scaling, or observability."
    return "This update has minor relevance to the core AI/ML stack but helps maintain awareness of general system/developer updates."

def generate_project_idea(title, summary, tags, item_id):
    # Cluster mapping based on tags
    cluster = "Research paper reproduction"
    if "Agentic AI" in tags or "Multi-Agent Systems" in tags:
        cluster = "Agent evaluation systems"
    elif "RAG / Retrieval" in tags:
        cluster = "RAG and retrieval benchmarks"
    elif "Vertex AI / Google Cloud AI" in tags or "BigQuery / Analytics" in tags:
        cluster = "Vertex AI / BigQuery ML demos"
    elif "Cloud Infrastructure" in tags:
        cluster = "Cloud Run agent deployment"
    elif "Security / IAM / Governance" in tags:
        cluster = "AI governance and safety"
    elif "LLM Training / Fine-tuning" in tags:
        cluster = "LLM fine-tuning and distillation"
    elif "Data Engineering" in tags:
        cluster = "Data engineering for AI systems"

    title_clean = title.split("(")[0].strip()
    
    # Formulate project title
    proj_title = f"Demo: {title_clean[:40]}..."
    if "Agentic AI" in tags:
        proj_title = f"Agent Benchmark: {title_clean[:35]}"
    elif "RAG / Retrieval" in tags:
        proj_title = f"RAG Evaluator: {title_clean[:35]}"
    elif "Vertex AI / Google Cloud AI" in tags:
        proj_title = f"Vertex AI Demo: {title_clean[:35]}"

    why = f"Inspired by updates in {', '.join(tags[:2])}. Validates how these concepts perform in a localized environment."
    scope = "Create a localized Flask interface implementing the core mechanism. Write unit tests to verify baseline behavior."
    tools = "Python, SQLite, Flask"
    if "Vertex AI / Google Cloud AI" in tags:
        tools += ", Vertex AI SDK, Gemini API"
    if "BigQuery / Analytics" in tags:
        tools += ", Google Cloud BigQuery"
    if "Cloud Infrastructure" in tags:
        tools += ", Cloud Run, Docker"

    difficulty = "medium"
    if "LLM Training / Fine-tuning" in tags:
        difficulty = "hard"
    elif "Cloud Infrastructure" in tags or "BigQuery / Analytics" in tags:
        difficulty = "easy"

    resume = f"Designed and prototyped a lightweight '{proj_title}' tool leveraging {tools} to demonstrate technical capability in {', '.join(tags[:2])}."

    return {
        "title": proj_title,
        "why": why,
        "scope": scope,
        "tools": tools,
        "difficulty": difficulty,
        "resume": resume,
        "cluster": cluster
    }

# Sync Background Worker
def fetch_feeds_task():
    global is_refreshing, refresh_status_msg
    with refresh_lock:
        is_refreshing = True
        refresh_status_msg = "Starting ingestion..."
        
    conn = get_db_connection()
    
    for feed in FEEDS:
        url = feed["url"]
        name = feed["name"]
        group = feed["group"]
        
        with refresh_lock:
            refresh_status_msg = f"Fetching: {name}..."
            
        try:
            # Fetch with 10s timeout
            response = requests.get(url, timeout=10, headers={'User-Agent': 'Research Radar Agent/1.0'})
            if response.status_code != 200:
                raise Exception(f"HTTP Status {response.status_code}")
                
            feed_data = feedparser.parse(response.content)
            
            if feed_data.bozo and not feed_data.entries:
                raise Exception(feed_data.bozo_exception or "Malformed XML parser failure")
                
            success_count = 0
            for entry in feed_data.entries:
                # Deduplicate by item URL
                item_url = entry.get("link", "")
                if not item_url:
                    continue
                
                # Check if it already exists
                cur = conn.execute("SELECT id FROM items WHERE item_url = ?", (item_url,))
                if cur.fetchone():
                    continue
                
                title = entry.get("title", "Untitled")
                
                # Extract summary/abstract
                summary_raw = entry.get("summary", "") or entry.get("description", "") or entry.get("content", [{"value": ""}])[0].get("value", "")
                summary = clean_html(summary_raw)
                
                # Authors
                authors_list = []
                if "authors" in entry:
                    authors_list = [a.get("name", "") for a in entry.authors if a.get("name")]
                elif "author" in entry:
                    authors_list = [entry.author]
                authors = ", ".join(authors_list)
                
                # Categories
                cats = []
                if "tags" in entry:
                    cats = [t.get("term", "") for t in entry.tags if t.get("term")]
                elif "categories" in entry:
                    cats = entry.categories
                categories_str = json.dumps(cats)
                
                # Published Date - parse to standard ISO format using published_parsed
                pub_date = None
                if "published_parsed" in entry and entry.published_parsed:
                    try:
                        dt = datetime.datetime(*entry.published_parsed[:6])
                        pub_date = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        pass
                if not pub_date:
                    # Fallback to updated_parsed if available
                    if "updated_parsed" in entry and entry.updated_parsed:
                        try:
                            dt = datetime.datetime(*entry.updated_parsed[:6])
                            pub_date = dt.strftime("%Y-%m-%d %H:%M:%S")
                        except:
                            pass
                if not pub_date:
                    # Raw parse fallback if struct parsing failed
                    raw_pub = entry.get("published", "") or entry.get("updated", "") or entry.get("pubDate", "")
                    if raw_pub:
                        pub_date = raw_pub
                    else:
                        pub_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                fetched_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Scoring & Classification
                is_arxiv = (group == "arxiv")
                is_cloud = (group == "cloud-infra")
                score = compute_signal_score(title, summary)
                tags = classify_item(title, summary, is_arxiv, is_cloud)
                why_matters = generate_why_matters(title, summary, tags, score)
                
                # Insert
                conn.execute('''
                    INSERT INTO items (
                        title, source, source_url, item_url, published_date, summary, authors, 
                        categories, fetched_at, signal_score, classification_tags, status, why_matters
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    title, name, url, item_url, pub_date, summary, authors, 
                    categories_str, fetched_at, score, json.dumps(tags), 'unread', why_matters
                ))
                success_count += 1
            
            # Update health
            conn.execute('''
                INSERT INTO feed_health (url, name, last_status, last_success_at, error_message)
                VALUES (?, ?, 'success', ?, NULL)
                ON CONFLICT(url) DO UPDATE SET
                    last_status='success',
                    last_success_at=?,
                    error_message=NULL
            ''', (url, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            
        except Exception as e:
            # Log failure in DB
            error_msg = str(e)
            conn.execute('''
                INSERT INTO feed_health (url, name, last_status, last_success_at, error_message)
                VALUES (?, ?, 'failed', NULL, ?)
                ON CONFLICT(url) DO UPDATE SET
                    last_status='failed',
                    error_message=?
            ''', (url, name, error_msg, error_msg))
            
        conn.commit()
        
    conn.close()
    
    with refresh_lock:
        is_refreshing = False
        refresh_status_msg = "Completed refresh."

# Web UI Routes

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/saved')
def saved():
    return render_template('saved.html')

@app.route('/projects')
def projects():
    return render_template('projects.html')

@app.route('/item/<int:item_id>')
def item_details(item_id):
    conn = get_db_connection()
    item = conn.execute('SELECT * FROM items WHERE id = ?', (item_id,)).fetchone()
    conn.close()
    if not item:
        return "Item not found", 404
    return render_template('item.html', item=item)

# API Endpoints

@app.route('/api/refresh', methods=['POST'])
def api_refresh():
    global is_refreshing
    if is_refreshing:
        return jsonify({"status": "already_refreshing", "msg": refresh_status_msg})
        
    thread = threading.Thread(target=fetch_feeds_task)
    thread.daemon = True
    thread.start()
    return jsonify({"status": "started", "msg": "Sync started in background."})

@app.route('/api/refresh/status', methods=['GET'])
def api_refresh_status():
    global is_refreshing, refresh_status_msg
    return jsonify({"refreshing": is_refreshing, "msg": refresh_status_msg})

@app.route('/api/feeds', methods=['GET'])
def api_feeds():
    conn = get_db_connection()
    health_rows = conn.execute('SELECT * FROM feed_health').fetchall()
    conn.close()
    
    feeds_list = []
    for h in health_rows:
        feeds_list.append({
            "url": h["url"],
            "name": h["name"],
            "last_status": h["last_status"],
            "last_success_at": h["last_success_at"],
            "error_message": h["error_message"]
        })
    return jsonify(feeds_list)

@app.route('/api/items', methods=['GET'])
def api_items():
    # Filter params
    search = request.args.get('search', '')
    source = request.args.get('source', '')
    arxiv_cat = request.args.get('arxiv_cat', '')
    date_range = request.args.get('date_range', '') # 'today', 'week', 'month', or empty
    min_score = request.args.get('min_score', '')
    saved_only = request.args.get('saved_only', 'false') == 'true'
    show_ignored = request.args.get('show_ignored', 'false') == 'true'
    sort_by = request.args.get('sort_by', 'date') # 'date' or 'score'
    
    # Classifications filters
    categories_filter = request.args.getlist('category') # list of classifications
    
    conn = get_db_connection()
    
    query = "SELECT * FROM items WHERE 1=1"
    params = []
    
    if not show_ignored and not saved_only:
        query += " AND status != 'ignored'"
        
    if saved_only:
        query += " AND status = 'saved'"
        
    if search:
        query += " AND (title LIKE ? OR summary LIKE ? OR authors LIKE ?)"
        params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
        
    if source:
        query += " AND source = ?"
        params.append(source)
        
    if arxiv_cat:
        # Check in categories column (JSON array string)
        query += " AND categories LIKE ?"
        params.append(f'%"{arxiv_cat}"%')
        
    if min_score:
        query += " AND signal_score >= ?"
        params.append(int(min_score))
        
    if date_range:
        now = datetime.datetime.now()
        if date_range == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_range == 'week':
            start_date = now - datetime.timedelta(days=7)
        elif date_range == 'month':
            start_date = now - datetime.timedelta(days=30)
            
        # Filter by normalized published_date
        query += " AND published_date >= ?"
        params.append(start_date.strftime("%Y-%m-%d %H:%M:%S"))
        
    # Get all matching items first, filter categories in python or SQLite
    if categories_filter:
        for cat in categories_filter:
            query += " AND classification_tags LIKE ?"
            params.append(f'%"{cat}"%')
            
    if sort_by == 'score':
        query += " ORDER BY signal_score DESC, published_date DESC, id DESC LIMIT 200"
    else:
        query += " ORDER BY published_date DESC, signal_score DESC, id DESC LIMIT 200"
    
    rows = conn.execute(query, params).fetchall()
    
    items = []
    for r in rows:
        # Load JSON fields
        try:
            cats = json.loads(r["categories"]) if r["categories"] else []
        except:
            cats = []
            
        try:
            tags = json.loads(r["classification_tags"]) if r["classification_tags"] else []
        except:
            tags = []
            
        items.append({
            "id": r["id"],
            "title": r["title"],
            "source": r["source"],
            "source_url": r["source_url"],
            "item_url": r["item_url"],
            "published_date": r["published_date"],
            "summary": r["summary"],
            "authors": r["authors"],
            "categories": cats,
            "fetched_at": r["fetched_at"],
            "signal_score": r["signal_score"],
            "classification_tags": tags,
            "status": r["status"],
            "user_notes": r["user_notes"],
            "why_matters": r["why_matters"],
            "project_title": r["project_title"],
            "project_why": r["project_why"],
            "project_scope": r["project_scope"],
            "project_tools": r["project_tools"],
            "project_difficulty": r["project_difficulty"],
            "project_resume": r["project_resume"],
            "project_status": r["project_status"],
            "project_cluster": r["project_cluster"]
        })
        
    conn.close()
    return jsonify(items)

@app.route('/api/item/<int:item_id>/save', methods=['POST'])
def api_save_item(item_id):
    conn = get_db_connection()
    conn.execute("UPDATE items SET status = 'saved' WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "status": "saved"})

@app.route('/api/item/<int:item_id>/ignore', methods=['POST'])
def api_ignore_item(item_id):
    conn = get_db_connection()
    conn.execute("UPDATE items SET status = 'ignored' WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "status": "ignored"})

@app.route('/api/item/<int:item_id>/notes', methods=['POST'])
def api_save_notes(item_id):
    data = request.json or {}
    notes = data.get("notes", "")
    conn = get_db_connection()
    conn.execute("UPDATE items SET user_notes = ? WHERE id = ?", (notes, item_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/item/<int:item_id>/status', methods=['POST'])
def api_save_project_status(item_id):
    data = request.json or {}
    status = data.get("status", "")
    conn = get_db_connection()
    conn.execute("UPDATE items SET project_status = ? WHERE id = ?", (status, item_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/item/<int:item_id>/project', methods=['POST'])
def api_generate_or_save_project(item_id):
    conn = get_db_connection()
    item = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    if not item:
        conn.close()
        return jsonify({"error": "Item not found"}), 404
        
    # Get current classification tags
    try:
        tags = json.loads(item["classification_tags"]) if item["classification_tags"] else []
    except:
        tags = ["Other"]
        
    # Generate project template
    idea = generate_project_idea(item["title"], item["summary"], tags, item_id)
    
    # Save to db
    conn.execute('''
        UPDATE items SET
            project_title = ?,
            project_why = ?,
            project_scope = ?,
            project_tools = ?,
            project_difficulty = ?,
            project_resume = ?,
            project_status = COALESCE(project_status, 'Build idea'),
            project_cluster = ?
        WHERE id = ?
    ''', (
        idea["title"], idea["why"], idea["scope"], idea["tools"], 
        idea["difficulty"], idea["resume"], idea["cluster"], item_id
    ))
    conn.commit()
    
    # Return updated project details
    updated = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    conn.close()
    
    return jsonify({
        "success": True,
        "project": {
            "title": updated["project_title"],
            "why": updated["project_why"],
            "scope": updated["project_scope"],
            "tools": updated["project_tools"],
            "difficulty": updated["project_difficulty"],
            "resume": updated["project_resume"],
            "status": updated["project_status"],
            "cluster": updated["project_cluster"]
        }
    })

# Project edit API
@app.route('/api/item/<int:item_id>/project/edit', methods=['POST'])
def api_edit_project(item_id):
    data = request.json or {}
    conn = get_db_connection()
    conn.execute('''
        UPDATE items SET
            project_title = ?,
            project_why = ?,
            project_scope = ?,
            project_tools = ?,
            project_difficulty = ?,
            project_resume = ?,
            project_cluster = ?
        WHERE id = ?
    ''', (
        data.get("title", ""),
        data.get("why", ""),
        data.get("scope", ""),
        data.get("tools", ""),
        data.get("difficulty", ""),
        data.get("resume", ""),
        data.get("cluster", ""),
        item_id
    ))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

# Ingest and classify social previews on-demand
@app.route('/api/item/<int:item_id>/social', methods=['GET'])
def api_social_previews(item_id):
    conn = get_db_connection()
    item = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    conn.close()
    if not item:
        return jsonify({"error": "Item not found"}), 404
        
    title = item["title"]
    url = item["item_url"]
    summary = item["summary"] or ""
    
    # Clean titles/remove tags
    title_clean = re.sub(r'\[.*?\]', '', title).strip()
    
    # Social Media Post Templates
    x_post = (
        f"Interesting update: {title_clean}\n\n"
        f"💡 Key takeaway: {summary[:180]}...\n\n"
        f"Read more: {url}"
    )
    
    try:
        tags = json.loads(item["classification_tags"]) if item["classification_tags"] else []
    except:
        tags = []
    hashtag_str = " ".join([f"#{t.replace(' ', '').replace('/', '')}" for t in tags[:3]])
    
    linkedin_post = (
        f"🔎 Industry Update: {title_clean}\n\n"
        f"I've been monitoring developments in {', '.join(tags[:3])}. "
        f"Here's why this matters:\n"
        f"• {item['why_matters']}\n\n"
        f"Summary: {summary[:280]}...\n\n"
        f"Link: {url}\n\n"
        f"{hashtag_str}"
    )
    
    tech_summary = (
        f"Title: {title}\n"
        f"Source: {item['source']}\n"
        f"Published: {item['published_date']}\n"
        f"Classification: {', '.join(tags)}\n\n"
        f"Why It Matters:\n{item['why_matters']}\n\n"
        f"Abstract / Summary:\n{summary}"
    )
    
    # Check if there is a resume bullet
    resume_bullet = item["project_resume"]
    if not resume_bullet:
        # Generate temporary draft
        proj = generate_project_idea(title, summary, tags, item_id)
        resume_bullet = proj["resume"]
        
    return jsonify({
        "x": x_post,
        "linkedin": linkedin_post,
        "summary": tech_summary,
        "resume": resume_bullet
    })


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5001, debug=True)
