# Feed configuration for Research-to-Project Radar

FEEDS = [
    # arXiv Atom API Query Feeds (Standardized to query latest 50 publications)
    {
        "url": "https://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=lastUpdatedDate&sortOrder=descending&max_results=50",
        "name": "cs.AI (Artificial Intelligence)",
        "group": "arxiv",
        "category": "cs.AI"
    },
    {
        "url": "https://export.arxiv.org/api/query?search_query=cat:cs.CL&sortBy=lastUpdatedDate&sortOrder=descending&max_results=50",
        "name": "cs.CL (Computation and Language)",
        "group": "arxiv",
        "category": "cs.CL"
    },
    {
        "url": "https://export.arxiv.org/api/query?search_query=cat:cs.LG&sortBy=lastUpdatedDate&sortOrder=descending&max_results=50",
        "name": "cs.LG (Machine Learning)",
        "group": "arxiv",
        "category": "cs.LG"
    },
    {
        "url": "https://export.arxiv.org/api/query?search_query=cat:cs.IR&sortBy=lastUpdatedDate&sortOrder=descending&max_results=50",
        "name": "cs.IR (Information Retrieval)",
        "group": "arxiv",
        "category": "cs.IR"
    },
    {
        "url": "https://export.arxiv.org/api/query?search_query=cat:cs.DB&sortBy=lastUpdatedDate&sortOrder=descending&max_results=50",
        "name": "cs.DB (Databases)",
        "group": "arxiv",
        "category": "cs.DB"
    },
    {
        "url": "https://export.arxiv.org/api/query?search_query=cat:cs.SE&sortBy=lastUpdatedDate&sortOrder=descending&max_results=50",
        "name": "cs.SE (Software Engineering)",
        "group": "arxiv",
        "category": "cs.SE"
    },
    {
        "url": "https://export.arxiv.org/api/query?search_query=cat:cs.DC&sortBy=lastUpdatedDate&sortOrder=descending&max_results=50",
        "name": "cs.DC (Distributed, Parallel, and Cluster Computing)",
        "group": "arxiv",
        "category": "cs.DC"
    },
    {
        "url": "https://export.arxiv.org/api/query?search_query=cat:cs.CR&sortBy=lastUpdatedDate&sortOrder=descending&max_results=50",
        "name": "cs.CR (Cryptography and Security)",
        "group": "arxiv",
        "category": "cs.CR"
    },
    {
        "url": "https://export.arxiv.org/api/query?search_query=cat:cs.MA&sortBy=lastUpdatedDate&sortOrder=descending&max_results=50",
        "name": "cs.MA (Multiagent Systems)",
        "group": "arxiv",
        "category": "cs.MA"
    },
    {
        "url": "https://export.arxiv.org/api/query?search_query=cat:cs.RO&sortBy=lastUpdatedDate&sortOrder=descending&max_results=50",
        "name": "cs.RO (Robotics)",
        "group": "arxiv",
        "category": "cs.RO"
    },
    {
        "url": "https://export.arxiv.org/api/query?search_query=cat:cs.CV&sortBy=lastUpdatedDate&sortOrder=descending&max_results=50",
        "name": "cs.CV (Computer Vision)",
        "group": "arxiv",
        "category": "cs.CV"
    },
    {
        "url": "https://export.arxiv.org/api/query?search_query=cat:stat.ML&sortBy=lastUpdatedDate&sortOrder=descending&max_results=50",
        "name": "stat.ML (Machine Learning Stats)",
        "group": "arxiv",
        "category": "stat.ML"
    },

    # Optional AI/Research feeds
    {
        "url": "https://deepmind.google/blog/rss.xml",
        "name": "Google DeepMind Blog",
        "group": "ai-lab",
        "category": None
    },
    {
        "url": "https://openai.com/news/rss.xml",
        "name": "OpenAI News & Blog",
        "group": "ai-lab",
        "category": None
    },
    {
        "url": "https://www.anthropic.com/news/rss.xml",
        "name": "Anthropic News & Research",
        "group": "ai-lab",
        "category": None
    },
    {
        "url": "https://huggingface.co/blog/feed.xml",
        "name": "Hugging Face Blog",
        "group": "ai-lab",
        "category": None
    },
    {
        "url": "https://papers.takara.ai/api/feed",
        "name": "Takara AI Papers",
        "group": "ai-lab",
        "category": None
    },
    {
        "url": "https://bair.berkeley.edu/blog/feed.xml",
        "name": "Berkeley AI Research (BAIR)",
        "group": "ai-lab",
        "category": None
    },
    {
        "url": "https://news.mit.edu/rss/topic/artificial-intelligence2",
        "name": "MIT News - AI",
        "group": "ai-lab",
        "category": None
    },
    {
        "url": "https://www.microsoft.com/en-us/research/feed/",
        "name": "Microsoft Research",
        "group": "ai-lab",
        "category": None
    },
    {
        "url": "https://research.facebook.com/feed/",
        "name": "Meta Research",
        "group": "ai-lab",
        "category": None
    },

    # Google Cloud / AI infrastructure feeds
    {
        "url": "https://cloud.google.com/feeds/bigquery-release-notes.xml",
        "name": "BigQuery Release Notes",
        "group": "cloud-infra",
        "category": None
    },
    {
        "url": "https://cloud.google.com/feeds/bigquery-ml-release-notes.xml",
        "name": "BigQuery ML Release Notes",
        "group": "cloud-infra",
        "category": None
    },
    {
        "url": "https://cloud.google.com/feeds/vertex-ai-release-notes.xml",
        "name": "Vertex AI Release Notes",
        "group": "cloud-infra",
        "category": None
    },
    {
        "url": "https://cloud.google.com/feeds/vertex-ai-product-group-release-notes.xml",
        "name": "Vertex AI Product Group Release Notes",
        "group": "cloud-infra",
        "category": None
    },
    {
        "url": "https://cloud.google.com/feeds/cloud-run-release-notes.xml",
        "name": "Cloud Run Release Notes",
        "group": "cloud-infra",
        "category": None
    },
    {
        "url": "https://cloud.google.com/feeds/cloud-functions-release-notes.xml",
        "name": "Cloud Functions Release Notes",
        "group": "cloud-infra",
        "category": None
    },
    {
        "url": "https://cloud.google.com/feeds/cloud-pub-sub-release-notes.xml",
        "name": "Cloud Pub/Sub Release Notes",
        "group": "cloud-infra",
        "category": None
    },
    {
        "url": "https://cloud.google.com/feeds/dataflow-release-notes.xml",
        "name": "Dataflow Release Notes",
        "group": "cloud-infra",
        "category": None
    },
    {
        "url": "https://cloud.google.com/feeds/kubernetes-engine-release-notes.xml",
        "name": "Google Kubernetes Engine (GKE) Release Notes",
        "group": "cloud-infra",
        "category": None
    },
    {
        "url": "https://cloud.google.com/feeds/cloud-iam-release-notes.xml",
        "name": "Cloud IAM Release Notes",
        "group": "cloud-infra",
        "category": None
    },
    {
        "url": "https://cloud.google.com/feeds/secret-manager-release-notes.xml",
        "name": "Secret Manager Release Notes",
        "group": "cloud-infra",
        "category": None
    }
]
