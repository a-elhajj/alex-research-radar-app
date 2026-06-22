// Global State
let currentItemIdForAction = null;
let feedsData = [];

// Helper: Get checked focus area categories
function getCheckedCategories() {
    const checked = [];
    document.querySelectorAll('input[name="category"]:checked').forEach(cb => {
        checked.push(cb.value);
    });
    return checked;
}

// -------------------------------------------------------------
// RADER MAIN FEED (Discovery Radar)
// -------------------------------------------------------------
function initRadarFeed() {
    const radarItemsList = document.getElementById('radarItemsList');
    const sourceFilter = document.getElementById('sourceFilter');
    const scoreFilter = document.getElementById('scoreFilter');
    const dateFilter = document.getElementById('dateFilter');
    const searchFilter = document.getElementById('searchFilter');
    const arxivCatFilter = document.getElementById('arxivCatFilter');
    const showIgnoredFilter = document.getElementById('showIgnoredFilter');
    const clearFiltersBtn = document.getElementById('clearFiltersBtn');
    
    // Load feed sources list
    fetch('/api/feeds')
        .then(res => res.json())
        .then(feeds => {
            feedsData = feeds;
            sourceFilter.innerHTML = '<option value="">All Sources</option>';
            // Unique sources sorted
            const uniqueSources = [...new Set(feeds.map(f => f.name))].sort();
            uniqueSources.forEach(src => {
                const opt = document.createElement('option');
                opt.value = src;
                opt.textContent = src;
                sourceFilter.appendChild(opt);
            });
        });

    function fetchItems() {
        radarItemsList.innerHTML = `<div class="loader-placeholder"><i class="fa-solid fa-circle-notch fa-spin"></i><p>Loading Radar Feed...</p></div>`;
        
        const sortBySelect = document.getElementById('sortBySelect');
        const sortBy = sortBySelect ? sortBySelect.value : 'date';
        
        const params = new URLSearchParams();
        if (searchFilter.value) params.append('search', searchFilter.value);
        if (sourceFilter.value) params.append('source', sourceFilter.value);
        if (arxivCatFilter.value) params.append('arxiv_cat', arxivCatFilter.value);
        if (dateFilter.value) params.append('date_range', dateFilter.value);
        if (scoreFilter.value) params.append('min_score', scoreFilter.value);
        if (showIgnoredFilter.checked) params.append('show_ignored', 'true');
        params.append('sort_by', sortBy);
        
        const cats = getCheckedCategories();
        cats.forEach(c => params.append('category', c));

        fetch(`/api/items?${params.toString()}`)
            .then(res => res.json())
            .then(items => {
                document.getElementById('itemCount').textContent = items.length;
                if (items.length === 0) {
                    radarItemsList.innerHTML = `
                        <div class="empty-state glass">
                            <i class="fa-solid fa-satellite-dish"></i>
                            <h3>No radar signals detected</h3>
                            <p>Try clearing filters or syncing new feeds.</p>
                        </div>
                    `;
                    return;
                }
                
                radarItemsList.innerHTML = '';
                items.forEach(item => {
                    const card = createRadarCard(item);
                    radarItemsList.appendChild(card);
                });
            })
            .catch(err => {
                radarItemsList.innerHTML = `<div class="error-state"><i class="fa-solid fa-triangle-exclamation"></i><p>Error loading items: ${err.message}</p></div>`;
            });
    }

    // Debounced search
    let searchTimeout;
    searchFilter.addEventListener('input', () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(fetchItems, 300);
    });

    // Other inputs change triggers
    const listeners = [sourceFilter, scoreFilter, dateFilter, arxivCatFilter, showIgnoredFilter];
    const sortBySelect = document.getElementById('sortBySelect');
    if (sortBySelect) listeners.push(sortBySelect);

    listeners.forEach(el => {
        if (el) el.addEventListener('change', fetchItems);
    });

    // Checkboxes change triggers
    document.querySelectorAll('input[name="category"]').forEach(cb => {
        cb.addEventListener('change', fetchItems);
    });

    // Reset filters
    clearFiltersBtn.addEventListener('click', () => {
        searchFilter.value = '';
        sourceFilter.value = '';
        scoreFilter.value = '';
        dateFilter.value = '';
        arxivCatFilter.value = '';
        showIgnoredFilter.checked = false;
        if (sortBySelect) sortBySelect.value = 'date';
        document.querySelectorAll('input[name="category"]').forEach(cb => cb.checked = false);
        fetchItems();
    });

    // Initial load
    fetchItems();
}

function createRadarCard(item) {
    const div = document.createElement('div');
    div.className = `radar-card glass ${item.status === 'ignored' ? 'ignored-item' : ''}`;
    
    const maxSummaryLen = 220;
    const isLong = item.summary && item.summary.length > maxSummaryLen;
    const summaryShort = isLong ? item.summary.substring(0, maxSummaryLen) + '...' : item.summary;
    
    // Tag stringify
    let tagBadges = '';
    if (item.classification_tags) {
        item.classification_tags.forEach(tag => {
            tagBadges += `<span class="badge category-badge">${tag}</span>`;
        });
    }
    
    div.innerHTML = `
        <div class="card-header-meta">
            <span class="badge source-badge">${item.source}</span>
            <span class="badge score-badge-${item.signal_score}">Signal: ${item.signal_score}/5</span>
            <span class="card-date">${item.published_date}</span>
        </div>
        <h3 class="card-title"><a href="/item/${item.id}">${item.title}</a></h3>
        ${item.authors ? `<p class="card-authors">By: ${item.authors}</p>` : ''}
        
        <div class="card-summary">
            <p class="summary-text-short">${summaryShort}</p>
            ${isLong ? `
                <p class="summary-text-full" style="display: none;">${item.summary}</p>
                <button class="btn-text toggle-summary-btn">Read more <i class="fa-solid fa-chevron-down"></i></button>
            ` : ''}
        </div>

        <div class="card-why-matters">
            <span class="why-label"><i class="fa-solid fa-compass"></i> Why This Matters:</span>
            <p>${item.why_matters || 'No explanation generated.'}</p>
        </div>

        <div class="card-tags-row">
            ${tagBadges}
        </div>

        <div class="card-actions">
            ${item.status !== 'saved' ? `
                <button class="btn btn-secondary btn-save" onclick="saveItem(${item.id}, this)">
                    <i class="fa-solid fa-bookmark"></i> Save
                </button>
            ` : `
                <span class="btn btn-disabled text-success"><i class="fa-solid fa-check"></i> Saved</span>
            `}
            
            ${item.status !== 'ignored' ? `
                <button class="btn btn-secondary btn-ignore" onclick="ignoreItem(${item.id}, this)">
                    <i class="fa-solid fa-ban"></i> Ignore
                </button>
            ` : `
                <button class="btn btn-secondary btn-restore" onclick="saveItem(${item.id}, this)">
                    <i class="fa-solid fa-rotate-left"></i> Restore
                </button>
            `}
            
            <button class="btn btn-primary btn-action" onclick="openActionHub(${item.id})">
                <i class="fa-solid fa-bolt"></i> Action Hub
            </button>
        </div>
    `;

    // Hook up read more toggler
    const toggleBtn = div.querySelector('.toggle-summary-btn');
    if (toggleBtn) {
        const shortP = div.querySelector('.summary-text-short');
        const fullP = div.querySelector('.summary-text-full');
        toggleBtn.addEventListener('click', () => {
            if (fullP.style.display === 'none') {
                fullP.style.display = 'block';
                shortP.style.display = 'none';
                toggleBtn.innerHTML = 'Collapse <i class="fa-solid fa-chevron-up"></i>';
            } else {
                fullP.style.display = 'none';
                shortP.style.display = 'block';
                toggleBtn.innerHTML = 'Read more <i class="fa-solid fa-chevron-down"></i>';
            }
        });
    }

    return div;
}

// -------------------------------------------------------------
// SAVED PAGE
// -------------------------------------------------------------
function initSavedPage() {
    const savedItemsList = document.getElementById('savedItemsList');
    const savedSearch = document.getElementById('savedSearch');
    
    function fetchSaved() {
        savedItemsList.innerHTML = `<div class="loader-placeholder"><i class="fa-solid fa-circle-notch fa-spin"></i><p>Loading Saved Items...</p></div>`;
        const search = savedSearch.value;
        const url = `/api/items?saved_only=true${search ? `&search=${encodeURIComponent(search)}` : ''}`;
        
        fetch(url)
            .then(res => res.json())
            .then(items => {
                document.getElementById('savedCount').textContent = items.length;
                if (items.length === 0) {
                    savedItemsList.innerHTML = `
                        <div class="empty-state glass">
                            <i class="fa-solid fa-bookmark"></i>
                            <h3>No saved radar updates</h3>
                            <p>Go to the Discovery Radar and save interesting papers or cloud releases.</p>
                        </div>
                    `;
                    return;
                }
                
                savedItemsList.innerHTML = '';
                items.forEach(item => {
                    const row = createSavedRow(item);
                    savedItemsList.appendChild(row);
                });
            })
            .catch(err => {
                savedItemsList.innerHTML = `<div class="error-state"><i class="fa-solid fa-triangle-exclamation"></i><p>Error loading saved items: ${err.message}</p></div>`;
            });
    }

    // Debounced search
    let searchTimeout;
    savedSearch.addEventListener('input', () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(fetchSaved, 300);
    });

    fetchSaved();
}

function createSavedRow(item) {
    const div = document.createElement('div');
    div.className = 'saved-row glass';
    
    let tagBadges = '';
    if (item.classification_tags) {
        item.classification_tags.forEach(tag => {
            tagBadges += `<span class="badge category-badge">${tag}</span>`;
        });
    }

    const statuses = ['To read', 'Reading', 'Build idea', 'Building', 'Posted', 'Done', 'Archived'];
    let statusOptions = '';
    statuses.forEach(st => {
        statusOptions += `<option value="${st}" ${item.project_status === st ? 'selected' : ''}>${st}</option>`;
    });

    div.innerHTML = `
        <div class="saved-row-header">
            <div class="saved-row-title-container">
                <span class="badge score-badge-${item.signal_score}">Signal: ${item.signal_score}/5</span>
                <h4><a href="/item/${item.id}">${item.title}</a></h4>
            </div>
            <div class="saved-row-actions">
                <button class="btn btn-sm btn-secondary" onclick="ignoreItem(${item.id}, this, true)">
                    <i class="fa-solid fa-trash-can"></i> Unsave
                </button>
                <button class="btn btn-sm btn-primary" onclick="openActionHub(${item.id})">
                    <i class="fa-solid fa-bolt"></i> Action Hub
                </button>
            </div>
        </div>
        <div class="saved-row-meta">
            <span><strong>Source:</strong> ${item.source}</span>
            <span><strong>Published:</strong> ${item.published_date}</span>
        </div>

        <div class="saved-row-tags">
            ${tagBadges}
        </div>

        <div class="saved-row-collapsible">
            <div class="saved-row-notes-grid">
                <div class="notes-box">
                    <label><i class="fa-solid fa-pen-nib"></i> My Personal Research Notes</label>
                    <textarea class="notes-editor" placeholder="Write paper insights, notes, or thoughts here... (autosaves)" oninput="debouncedSaveNotes(${item.id}, this)">${item.user_notes || ''}</textarea>
                    <span class="save-indicator" style="display: none;">Saved!</span>
                </div>
                <div class="status-box">
                    <label><i class="fa-solid fa-bars-progress"></i> Build & Post Status</label>
                    <select class="status-dropdown" onchange="updateProjectStatus(${item.id}, this.value)">
                        <option value="">-- Set Status --</option>
                        ${statusOptions}
                    </select>
                    
                    ${item.project_title ? `
                        <div class="saved-blueprint-preview">
                            <h5><i class="fa-solid fa-cubes text-gradient"></i> Blueprint Active</h5>
                            <p><strong>Title:</strong> ${item.project_title}</p>
                            <p><strong>Stack:</strong> ${item.project_tools}</p>
                        </div>
                    ` : `
                        <div class="saved-blueprint-missing">
                            <p>No project blueprint generated yet.</p>
                            <button class="btn btn-xs btn-primary-outline" onclick="openActionHub(${item.id})">Generate Roadmap</button>
                        </div>
                    `}
                </div>
            </div>
        </div>
    `;

    return div;
}

// Debounced Notes Autosave
let notesTimeout;
function debouncedSaveNotes(itemId, textarea) {
    const indicator = textarea.parentElement.querySelector('.save-indicator');
    indicator.style.display = 'block';
    indicator.textContent = 'Saving...';
    
    clearTimeout(notesTimeout);
    notesTimeout = setTimeout(() => {
        fetch(`/api/item/${itemId}/notes`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ notes: textarea.value })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                indicator.textContent = 'Saved!';
                setTimeout(() => { indicator.style.display = 'none'; }, 1500);
            }
        });
    }, 800);
}

function updateProjectStatus(itemId, status) {
    fetch(`/api/item/${itemId}/status`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: status })
    });
}

// -------------------------------------------------------------
// PORTFOLIO PROJECTS PAGE
// -------------------------------------------------------------
function initProjectsPage() {
    const container = document.getElementById('projectClustersContainer');
    
    fetch('/api/items?saved_only=true')
        .then(res => res.json())
        .then(items => {
            // Filter only items with generated project blueprints
            const projectItems = items.filter(it => it.project_title);
            
            if (projectItems.length === 0) {
                container.innerHTML = `
                    <div class="empty-state glass">
                        <i class="fa-solid fa-cubes"></i>
                        <h3>No projects in the pipeline</h3>
                        <p>Save high-signal radar items, open the <strong>Action Hub</strong>, and generate custom blueprints.</p>
                    </div>
                `;
                return;
            }
            
            // Group by cluster
            const clusters = {
                "Agent evaluation systems": [],
                "RAG and retrieval benchmarks": [],
                "Vertex AI / BigQuery ML demos": [],
                "Cloud Run agent deployment": [],
                "AI governance and safety": [],
                "LLM fine-tuning and distillation": [],
                "Research paper reproduction": [],
                "Data engineering for AI systems": []
            };
            
            projectItems.forEach(it => {
                const clusterName = it.project_cluster || "Research paper reproduction";
                if (!clusters[clusterName]) {
                    clusters[clusterName] = [];
                }
                clusters[clusterName].push(it);
            });
            
            container.innerHTML = '';
            
            Object.keys(clusters).forEach(clusterName => {
                const list = clusters[clusterName];
                if (list.length === 0) return; // Only show active clusters
                
                const groupDiv = document.createElement('div');
                groupDiv.className = 'project-cluster-group glass';
                
                let projectCardsHtml = '';
                list.forEach(p => {
                    projectCardsHtml += `
                        <div class="project-roadmap-card">
                            <div class="roadmap-card-header">
                                <div>
                                    <span class="badge diff-badge-${p.project_difficulty}">${p.project_difficulty.toUpperCase()}</span>
                                    <h4>${p.project_title}</h4>
                                </div>
                                <div class="roadmap-card-actions">
                                    <button class="btn btn-xs btn-secondary" onclick="openEditProject(${p.id})">
                                        <i class="fa-solid fa-pen-to-square"></i> Edit
                                    </button>
                                </div>
                            </div>
                            <div class="roadmap-details">
                                <p><strong>Source Update:</strong> <a href="/item/${p.id}" class="source-link">${p.title}</a></p>
                                <p><strong>Why It Matters:</strong> ${p.project_why}</p>
                                <p><strong>MVP Scope:</strong> ${p.project_scope}</p>
                                <p><strong>Tools & SDKs:</strong> <code class="code-font">${p.project_tools}</code></p>
                                
                                <div class="resume-bullet-box">
                                    <div class="resume-bullet-header">
                                        <span>Resume Bullet Draft</span>
                                        <button class="btn btn-xs btn-secondary-outline copy-btn" data-text="${p.project_resume.replace(/"/g, '&quot;')}">
                                            <i class="fa-solid fa-copy"></i> Copy Bullet
                                        </button>
                                    </div>
                                    <p class="resume-bullet-text">"${p.project_resume}"</p>
                                </div>
                            </div>
                        </div>
                    `;
                });
                
                groupDiv.innerHTML = `
                    <div class="cluster-header" onclick="toggleClusterCollapse(this)">
                        <div class="cluster-title">
                            <i class="fa-solid fa-folder-open text-gradient"></i>
                            <h3>${clusterName}</h3>
                            <span class="count-badge">${list.length}</span>
                        </div>
                        <i class="fa-solid fa-chevron-up toggle-icon"></i>
                    </div>
                    <div class="cluster-body">
                        <div class="roadmaps-grid">
                            ${projectCardsHtml}
                        </div>
                    </div>
                `;
                
                container.appendChild(groupDiv);
            });
            
            // Re-init copy event listeners
            initCopyButtons();
        });
}

function toggleClusterCollapse(header) {
    const body = header.nextElementSibling;
    const icon = header.querySelector('.toggle-icon');
    if (body.style.display === 'none') {
        body.style.display = 'block';
        icon.className = 'fa-solid fa-chevron-up toggle-icon';
    } else {
        body.style.display = 'none';
        icon.className = 'fa-solid fa-chevron-down toggle-icon';
    }
}

// -------------------------------------------------------------
// SAVE / IGNORE ACTIONS
// -------------------------------------------------------------
function saveItem(id, btn, isSavedPage = false) {
    fetch(`/api/item/${id}/save`, { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                if (isSavedPage) {
                    location.reload();
                } else {
                    btn.outerHTML = `<span class="btn btn-disabled text-success"><i class="fa-solid fa-check"></i> Saved</span>`;
                }
            }
        });
}

function ignoreItem(id, btn, isSavedPage = false) {
    fetch(`/api/item/${id}/ignore`, { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                if (isSavedPage) {
                    btn.closest('.saved-row').remove();
                    const countEl = document.getElementById('savedCount');
                    countEl.textContent = parseInt(countEl.textContent) - 1;
                } else {
                    const card = btn.closest('.radar-card');
                    card.classList.add('ignored-item');
                    btn.outerHTML = `<button class="btn btn-secondary btn-restore" onclick="saveItem(${id}, this)"><i class="fa-solid fa-rotate-left"></i> Restore</button>`;
                }
            }
        });
}

// -------------------------------------------------------------
// ACTION HUB / MODAL
// -------------------------------------------------------------
function openActionHub(itemId) {
    currentItemIdForAction = itemId;
    const modal = document.getElementById('radarActionModal');
    modal.style.display = 'flex';
    
    // Default Tab
    switchTab('tab-project');
    
    // Load social previews
    fetch(`/api/item/${itemId}/social`)
        .then(res => res.json())
        .then(data => {
            document.getElementById('socialXText').value = data.x;
            document.getElementById('socialLinkedInText').value = data.linkedin;
            document.getElementById('techSummaryText').value = data.summary;
        });

    // Populate Project form if already generated, else fetch auto-generated blueprint
    document.getElementById('projectSpinner').style.display = 'block';
    document.getElementById('projectFormContainer').style.display = 'none';
    
    // Run project endpoint which generates dynamically if empty
    fetch(`/api/item/${itemId}/project`, { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            document.getElementById('projectSpinner').style.display = 'none';
            document.getElementById('projectFormContainer').style.display = 'block';
            
            const proj = data.project;
            document.getElementById('projTitle').value = proj.title;
            document.getElementById('projDifficulty').value = proj.difficulty;
            document.getElementById('projWhy').value = proj.why;
            document.getElementById('projScope').value = proj.scope;
            document.getElementById('projTools').value = proj.tools;
            document.getElementById('projResume').value = proj.resume;
            document.getElementById('projCluster').value = proj.cluster || "Research paper reproduction";
        });
}

// Modal tab switcher
function switchTab(tabId) {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('data-tab') === tabId) {
            btn.classList.add('active');
        }
    });
    document.querySelectorAll('.tab-content').forEach(content => {
        content.style.display = 'none';
    });
    document.getElementById(tabId).style.display = 'block';
}

// Save custom edited blueprint
document.getElementById('saveProjectBtn')?.addEventListener('click', () => {
    if (!currentItemIdForAction) return;
    
    const body = {
        title: document.getElementById('projTitle').value,
        difficulty: document.getElementById('projDifficulty').value,
        why: document.getElementById('projWhy').value,
        scope: document.getElementById('projScope').value,
        tools: document.getElementById('projTools').value,
        resume: document.getElementById('projResume').value,
        cluster: document.getElementById('projCluster').value
    };

    fetch(`/api/item/${currentItemIdForAction}/project/edit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            // Unconditionally save to Saved status
            fetch(`/api/item/${currentItemIdForAction}/save`, { method: 'POST' })
                .then(() => {
                    alert("Portfolio blueprint saved successfully!");
                    document.getElementById('radarActionModal').style.display = 'none';
                    if (window.location.pathname === '/saved' || window.location.pathname === '/projects') {
                        location.reload();
                    }
                });
        }
    });
});

// Edit Project Blueprint from Projects page
function openEditProject(itemId) {
    currentItemIdForAction = itemId;
    const modal = document.getElementById('editProjectModal');
    modal.style.display = 'flex';
    
    // Fetch current project fields
    fetch(`/api/items?saved_only=true`)
        .then(res => res.json())
        .then(items => {
            const item = items.find(it => it.id === itemId);
            if (item) {
                document.getElementById('editProjItemId').value = itemId;
                document.getElementById('editProjTitle').value = item.project_title;
                document.getElementById('editProjDifficulty').value = item.project_difficulty;
                document.getElementById('editProjWhy').value = item.project_why;
                document.getElementById('editProjScope').value = item.project_scope;
                document.getElementById('editProjTools').value = item.project_tools;
                document.getElementById('editProjResume').value = item.project_resume;
                document.getElementById('editProjCluster').value = item.project_cluster || "Research paper reproduction";
            }
        });
}

document.getElementById('saveEditProjectBtn')?.addEventListener('click', () => {
    const itemId = document.getElementById('editProjItemId').value;
    const body = {
        title: document.getElementById('editProjTitle').value,
        difficulty: document.getElementById('editProjDifficulty').value,
        why: document.getElementById('editProjWhy').value,
        scope: document.getElementById('editProjScope').value,
        tools: document.getElementById('editProjTools').value,
        resume: document.getElementById('editProjResume').value,
        cluster: document.getElementById('editProjCluster').value
    };

    fetch(`/api/item/${itemId}/project/edit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            alert("Blueprint updated!");
            document.getElementById('editProjectModal').style.display = 'none';
            location.reload();
        }
    });
});

// Tab navigation bindings
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        switchTab(btn.getAttribute('data-tab'));
    });
});

// Close Action Modals
document.getElementById('closeActionModalBtn')?.addEventListener('click', () => {
    document.getElementById('radarActionModal').style.display = 'none';
});
document.getElementById('closeEditProjectModalBtn')?.addEventListener('click', () => {
    document.getElementById('editProjectModal').style.display = 'none';
});

// -------------------------------------------------------------
// FEED HEALTH POPUP
// -------------------------------------------------------------
document.getElementById('feedHealthBtn').addEventListener('click', () => {
    const modal = document.getElementById('feedHealthModal');
    modal.style.display = 'flex';
    const list = document.getElementById('feedHealthList');
    
    list.innerHTML = `<div class="loader-placeholder"><i class="fa-solid fa-circle-notch fa-spin"></i> Loading health stats...</div>`;
    
    fetch('/api/feeds')
        .then(res => res.json())
        .then(feeds => {
            if (feeds.length === 0) {
                list.innerHTML = '<p class="text-muted">No feed sync metadata recorded yet. Click Sync Feeds.</p>';
                return;
            }
            
            list.innerHTML = '';
            feeds.forEach(f => {
                const item = document.createElement('div');
                item.className = 'feed-health-item';
                
                const statusClass = f.last_status === 'success' ? 'status-success' : 'status-failed';
                const statusIcon = f.last_status === 'success' ? 'fa-solid fa-circle-check' : 'fa-solid fa-triangle-exclamation';
                
                item.innerHTML = `
                    <div class="health-meta">
                        <span class="health-status-badge ${statusClass}">
                            <i class="${statusIcon}"></i> ${f.last_status.toUpperCase()}
                        </span>
                        <h4>${f.name}</h4>
                        <span class="small-text-url">${f.url}</span>
                    </div>
                    <div class="health-times">
                        <span><strong>Last Refreshed:</strong> ${f.last_success_at || 'Never'}</span>
                        ${f.error_message ? `<p class="error-msg text-danger"><strong>Error:</strong> ${f.error_message}</p>` : ''}
                    </div>
                `;
                list.appendChild(item);
            });
        });
});

document.getElementById('closeFeedHealthBtn').addEventListener('click', () => {
    document.getElementById('feedHealthModal').style.display = 'none';
});

// -------------------------------------------------------------
// REFRESH / INGEST TRIGGER
// -------------------------------------------------------------
const refreshBtn = document.getElementById('refreshBtn');
const refreshIndicator = document.getElementById('refreshIndicator');
const refreshText = document.getElementById('refreshText');

let refreshCheckInterval = null;

function checkRefreshStatus() {
    fetch('/api/refresh/status')
        .then(res => res.json())
        .then(data => {
            if (data.refreshing) {
                refreshIndicator.style.display = 'flex';
                refreshText.textContent = data.msg || "Refreshing feeds...";
                refreshBtn.disabled = true;
                refreshBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Syncing...`;
            } else {
                refreshIndicator.style.display = 'none';
                refreshBtn.disabled = false;
                refreshBtn.innerHTML = `<i class="fa-solid fa-rotate"></i> Sync Feeds`;
                clearInterval(refreshCheckInterval);
                refreshCheckInterval = null;
                // If on Discovery/Radar page, reload cards
                if (document.getElementById('radarItemsList')) {
                    initRadarFeed();
                }
            }
        });
}

refreshBtn.addEventListener('click', () => {
    fetch('/api/refresh', { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'started' || data.status === 'already_refreshing') {
                if (!refreshCheckInterval) {
                    refreshCheckInterval = setInterval(checkRefreshStatus, 1500);
                }
                checkRefreshStatus();
            }
        });
});

// Check if running on page load
checkRefreshStatus();

// -------------------------------------------------------------
// UTILITIES / COPY SYSTEM
// -------------------------------------------------------------
function initCopyButtons() {
    document.querySelectorAll('.copy-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            let text = '';
            const targetId = btn.getAttribute('data-target');
            
            if (targetId) {
                text = document.getElementById(targetId).value;
            } else {
                text = btn.getAttribute('data-text');
            }
            
            navigator.clipboard.writeText(text).then(() => {
                const originalHtml = btn.innerHTML;
                btn.innerHTML = `<i class="fa-solid fa-check"></i> Copied!`;
                btn.classList.add('copied');
                setTimeout(() => {
                    btn.innerHTML = originalHtml;
                    btn.classList.remove('copied');
                }, 2000);
            });
        });
    });
}

// Global invocation of copying
document.addEventListener('click', (e) => {
    if (e.target && e.target.closest('.copy-btn')) {
        const btn = e.target.closest('.copy-btn');
        let text = '';
        const targetId = btn.getAttribute('data-target');
        
        if (targetId) {
            text = document.getElementById(targetId).value;
        } else {
            text = btn.getAttribute('data-text');
        }
        
        navigator.clipboard.writeText(text).then(() => {
            const originalHtml = btn.innerHTML;
            btn.innerHTML = `<i class="fa-solid fa-check"></i> Copied!`;
            btn.classList.add('copied');
            setTimeout(() => {
                btn.innerHTML = originalHtml;
                btn.classList.remove('copied');
            }, 2000);
        });
    }
});
