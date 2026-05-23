/**
 * CareerForge Dashboard Main Script
 */

const DashboardApp = {
    token: localStorage.getItem('token'),
    pendingJobId: null,
    pollInterval: null,

    // ==========================================
    // CORE UTILS
    // ==========================================

    init() {
        this.initSidebar();
        if (!this.token && !window.location.pathname.includes('/login') && !window.location.pathname.includes('/register')) {
            this.toast('Please log in to view the dashboard', 'error');
            setTimeout(() => { window.location.href = '/login'; }, 1500);
        }
    },

    initSidebar() {
        const hamburger = document.getElementById('dbHamburger');
        const sidebar = document.getElementById('dbSidebar');
        if (hamburger && sidebar) {
            hamburger.addEventListener('click', () => {
                sidebar.classList.toggle('open');
            });
            document.addEventListener('click', (e) => {
                if (!sidebar.contains(e.target) && !hamburger.contains(e.target) && sidebar.classList.contains('open')) {
                    sidebar.classList.remove('open');
                }
            });
        }
    },

    toast(msg, type = 'info') {
        const container = document.getElementById('dbToastContainer');
        if (!container) return;
        const el = document.createElement('div');
        el.className = `db-toast ${type}`;

        let icon = '';
        if (type === 'success') icon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><polyline points="20 6 9 17 4 12"/></svg>';
        if (type === 'error') icon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>';
        if (type === 'info') icon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>';

        el.innerHTML = `${icon} <span>${msg}</span>`;
        container.appendChild(el);
        setTimeout(() => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(-10px)';
            el.style.pointerEvents = 'none';
            setTimeout(() => el.remove(), 300);
        }, 4000);
    },

    async authFetch(url, options = {}) {
        const headers = {
            'Authorization': `Bearer ${this.token}`,
            ...options.headers
        };
        if (!(options.body instanceof FormData) && options.body && typeof options.body !== 'string') {
            options.body = JSON.stringify(options.body);
            headers['Content-Type'] = 'application/json';
        }
        options.headers = headers;

        try {
            const res = await fetch(url, options);
            if (res.status === 401 || res.status === 403) {
                this.toast('Session expired. Please log in again.', 'error');
                localStorage.removeItem('token');
                setTimeout(() => { window.location.href = '/login'; }, 1500);
                return null;
            }
            return await res.json();
        } catch (err) {
            console.error('Fetch error:', err);
            return { success: false, message: 'Network error occurred.' };
        }
    },

    // ==========================================
    // OVERVIEW PAGE
    // ==========================================

    initOverview() {
        this.fetchStats();
        this.initUpload();
    },

    async fetchStats() {
        // In a real app we'd fetch this from /api/dashboard/stats
        // For now, we simulate fetching user's last analysis from localStorage
        const cached = localStorage.getItem('lastAnalysis');
        if (cached) {
            try {
                const data = JSON.parse(cached);
                this.updateStatCards(data);
                this.updateHistoryTable([data]); // Mock history
            } catch (e) { console.error('Cache parse error'); }
        }
    },

    updateStatCards(data) {
        if (!data || !data.score) return;

        // Update ATS Score
        const scoreEl = document.getElementById('statScoreValue');
        const cardEl = document.getElementById('statCardScore');
        if (scoreEl) scoreEl.textContent = data.score;
        if (cardEl) {
            cardEl.className = 'db-stat-card';
            if (data.score >= 70) cardEl.classList.add('score-green');
            else if (data.score >= 50) cardEl.classList.add('score-amber');
            else cardEl.classList.add('score-red');
        }

        // Update Profile Strength
        const strengthEl = document.getElementById('statStrengthValue');
        if (strengthEl) strengthEl.textContent = data.score_level || 'Good';

        // Update Skill gaps
        const gapsEl = document.getElementById('statGapsValue');
        if (gapsEl) {
            const gapCount = data.skill_gap && data.skill_gap.missing ? data.skill_gap.missing.length : 0;
            gapsEl.textContent = gapCount;
        }
    },

    updateHistoryTable(records) {
        const tbody = document.getElementById('historyTableBody');
        if (!tbody || !records || !records.length) return;

        tbody.innerHTML = '';
        records.forEach(r => {
            const date = new Date().toLocaleDateString();
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${date}</td>
                <td>${r.filename || 'resume.pdf'}</td>
                <td style="font-weight:600;color:var(--primary)">${r.score || 0}</td>
                <td><span class="db-badge green">Completed</span></td>
            `;
            tbody.appendChild(tr);
        });
    },

    initUpload() {
        const dropzone = document.getElementById('uploadDropzone');
        const fileInput = document.getElementById('resumeFileInput');
        if (!dropzone || !fileInput) return;

        dropzone.addEventListener('click', () => fileInput.click());

        dropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropzone.classList.add('drag-over');
        });

        dropzone.addEventListener('dragleave', () => {
            dropzone.classList.remove('drag-over');
        });

        dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropzone.classList.remove('drag-over');
            if (e.dataTransfer.files && e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                this.handleFileUpload(fileInput.files[0]);
            }
        });

        fileInput.addEventListener('change', () => {
            if (fileInput.files.length) {
                this.handleFileUpload(fileInput.files[0]);
            }
        });
    },

    async handleFileUpload(file) {
        if (!file || !file.name.toLowerCase().endsWith('.pdf')) {
            this.toast('Please upload a PDF file', 'error');
            return;
        }

        const wrap = document.getElementById('uploadProgressWrap');
        const bar = document.getElementById('uploadProgressBar');
        const statusText = document.getElementById('uploadStatusText');
        const percentText = document.getElementById('uploadPercentText');

        if (wrap) wrap.classList.add('visible');
        if (bar) bar.style.width = '10%';
        if (statusText) statusText.textContent = 'Uploading...';
        if (percentText) percentText.textContent = '10%';

        const formData = new FormData();
        formData.append('resume', file);

        // Simulate fast upload
        if (bar) bar.style.width = '40%';
        if (percentText) percentText.textContent = '40%';
        if (statusText) statusText.textContent = 'Analyzing with AI...';

        const data = await this.authFetch('/upload', {
            method: 'POST',
            body: formData
        });

        if (data && data.success && data.job_id) {
            if (bar) bar.style.width = '70%';
            if (percentText) percentText.textContent = '70%';

            this.pendingJobId = data.job_id;
            this.pollInterval = setInterval(() => this.pollAnalysisStatus(), 2000);
        } else {
            if (wrap) wrap.classList.remove('visible');
            this.toast(data?.message || 'Upload failed.', 'error');
        }
    },

    async pollAnalysisStatus() {
        if (!this.pendingJobId) return;

        const data = await this.authFetch(`/api/analysis/${this.pendingJobId}/status`);
        if (!data || !data.success) {
            clearInterval(this.pollInterval);
            this.toast('Error tracking analysis status', 'error');
            return;
        }

        if (data.status === 'completed') {
            clearInterval(this.pollInterval);

            const bar = document.getElementById('uploadProgressBar');
            const percentText = document.getElementById('uploadPercentText');
            const statusText = document.getElementById('uploadStatusText');

            if (bar) bar.style.width = '100%';
            if (percentText) percentText.textContent = '100%';
            if (statusText) statusText.textContent = 'Complete!';

            this.toast('Analysis complete!', 'success');

            // Cache result for cross-page use
            localStorage.setItem('lastAnalysis', JSON.stringify(data.result));

            // Update UI
            this.updateStatCards(data.result);
            this.updateHistoryTable([data.result]);

            setTimeout(() => {
                const wrap = document.getElementById('uploadProgressWrap');
                if (wrap) wrap.classList.remove('visible');

                // Redirect to detail page
                window.location.href = '/dashboard/resume';
            }, 1500);

        } else if (data.status === 'failed') {
            clearInterval(this.pollInterval);
            this.toast('Analysis failed. Please try again.', 'error');
            const wrap = document.getElementById('uploadProgressWrap');
            if (wrap) wrap.classList.remove('visible');
        }
        // if 'pending' or 'processing', do nothing, let it poll
    },

    // ==========================================
    // RESUME DETAIL PAGE
    // ==========================================

    initResumeAnalysis() {
        const cached = localStorage.getItem('lastAnalysis');
        if (!cached) {
            const empty = document.getElementById('resumeEmptyState');
            if (empty) empty.style.display = 'block';

            ['resumeContentCard', 'resumeFeedbackCard', 'resumeSuggestionsCard'].forEach(id => {
                const el = document.getElementById(id);
                if (el) el.style.display = 'none';
            });
            return;
        }

        try {
            const data = JSON.parse(cached);
            this.renderResumeData(data);
        } catch (e) {
            console.error(e);
            this.toast('Failed to load analysis data', 'error');
        }
    },

    renderResumeData(data) {
        if (!data) return;

        // Extracted Text
        const textEl = document.getElementById('resumeTextPreview');
        if (textEl && data.extracted_text) {
            textEl.textContent = data.extracted_text;
        }

        // Overall Score
        const scoreEl = document.getElementById('atsTotalScore');
        if (scoreEl && data.score) {
            scoreEl.textContent = data.score;
        }

        // Score Breakdown
        const breakdownWrap = document.getElementById('atsScoreBars');
        if (breakdownWrap && data.score_breakdown) {
            breakdownWrap.innerHTML = '';
            for (const [key, value] of Object.entries(data.score_breakdown)) {
                let displayKey = key.replace('_', ' ').toUpperCase();
                let percentage = value;
                // Determine color
                let colorClass = percentage > 70 ? 'green' : (percentage > 50 ? 'amber' : 'red');
                const pValue = typeof percentage === 'number' ? Math.round(percentage) : percentage;
                const progressWidth = typeof percentage === 'number' ? Math.min(percentage, 100) : 0;

                const row = document.createElement('div');
                row.className = 'db-score-bar-row';
                row.innerHTML = `
                   <div class="db-score-bar-label">${displayKey}</div>
                   <div class="db-score-bar-track">
                      <div class="db-score-bar-fill ${colorClass}" style="width: ${progressWidth}%"></div>
                   </div>
                   <div class="db-score-bar-val">${pValue}/100</div>
                `;
                breakdownWrap.appendChild(row);
            }
        }

        // Keywords
        const matchedWrap = document.getElementById('matchedKeywords');
        const missingWrap = document.getElementById('missingKeywords');

        if (matchedWrap && data.skills) {
            matchedWrap.innerHTML = data.skills.map(s =>
                `<span class="db-keyword-pill matched">${s}</span>`
            ).join('');
        }

        if (missingWrap && data.skill_gap && data.skill_gap.missing) {
            // Sort by priority if applicable, fallback to normal map
            const missingList = data.skill_gap.missing;
            missingWrap.innerHTML = missingList.map(s => {
                let name = typeof s === 'string' ? s : (s.skill || s.name || 'Unknown');
                return `<span class="db-keyword-pill missing">${name}</span>`;
            }).join('');
        }

        // Suggestions (Mocking this currently as it comes from a different AI flow for now)
        const suggestionsWrap = document.getElementById('suggestionsList');
        if (suggestionsWrap) {
            let suggestionsHTML = '';

            // Generate some mock suggestions based on gaps
            const gaps = data.skill_gap && data.skill_gap.missing ? data.skill_gap.missing : [];
            if (gaps.length > 0) {
                const gapName = typeof gaps[0] === 'string' ? gaps[0] : (gaps[0].skill || 'relevant skills');
                suggestionsHTML += `
                 <div class="db-suggestion-row">
                    <div class="db-suggestion-before">"Managed team of developers to build web application."</div>
                    <div class="db-suggestion-after">"Led a cross-functional team of 6 developers to architect and deploy a scalable web app using ${gapName}, resulting in 30% faster project delivery."</div>
                 </div>
                `;
            } else {
                suggestionsHTML += `<div style="padding:16px;color:var(--text-secondary)">Your phrasing is excellent, no major improvements found.</div>`;
            }

            suggestionsWrap.innerHTML = suggestionsHTML;
        }
    },

    // ==========================================
    // JOB MATCHER PAGE
    // ==========================================

    initJobMatcher() {
        const btn = document.getElementById('analyzeJobBtn');
        const jdInput = document.getElementById('jobDescriptionInput');
        const titleInput = document.getElementById('jobTitleInput');
        const resultCard = document.getElementById('matchResultCard');

        if (!btn || !jdInput) return;

        btn.addEventListener('click', () => {
            const jd = jdInput.value.trim();
            const title = titleInput.value.trim() || 'Software Engineer';
            if (!jd) {
                this.toast('Please paste a job description first', 'error');
                return;
            }

            btn.classList.add('loading');
            resultCard.classList.remove('visible');

            // Simulate AI Analysis delay
            setTimeout(() => {
                btn.classList.remove('loading');
                this.toast('Analysis complete!', 'success');
                this.renderJobMatchResult(title, jd);
            }, 1800);
        });

        // Save
        const saveBtn = document.getElementById('saveJobBtn');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => {
                const title = titleInput.value.trim() || 'Software Engineer';
                this.saveJobResult(title);
                this.toast('Job saved to your list', 'success');
            });
        }

        this.renderSavedJobs();
    },

    renderJobMatchResult(title, jd) {
        const resultCard = document.getElementById('matchResultCard');
        if (!resultCard) return;
        resultCard.classList.add('visible');

        // Generate pseudo-random match score between 50-95 for demo
        const matchScore = Math.floor(Math.random() * 45) + 50;

        const ring = document.getElementById('matchScoreRing');
        const scoreText = document.getElementById('matchScoreText');
        const statusText = document.getElementById('matchStatusText');

        if (scoreText) scoreText.textContent = matchScore + '%';
        if (ring) {
            if (matchScore >= 80) ring.style.borderColor = 'var(--success)';
            else if (matchScore >= 60) ring.style.borderColor = 'var(--warning)';
            else ring.style.borderColor = 'var(--danger)';
        }

        if (statusText) {
            if (matchScore >= 80) {
                statusText.textContent = 'Excellent match! Your resume is highly aligned with this role.';
                statusText.style.color = 'var(--success)';
            } else if (matchScore >= 60) {
                statusText.textContent = 'Good match, but consider updating your resume with missing keywords.';
                statusText.style.color = 'var(--warning)';
            } else {
                statusText.textContent = 'Low match. Major skill gaps detected. Major resume updates required.';
                statusText.style.color = 'var(--danger)';
            }
        }

        const mCount = document.getElementById('skillsMatchedCount');
        const misCount = document.getElementById('skillsMissingCount');
        const expMatch = document.getElementById('experienceMatchCount');

        const matched = Math.floor(Math.random() * 8) + 4;
        const missing = Math.floor(Math.random() * 5) + 1;

        if (mCount) mCount.textContent = matched;
        if (misCount) misCount.textContent = missing;
        if (expMatch) expMatch.textContent = matchScore > 70 ? 'Yes' : 'No';

        // Cache current match for "Save" functionality
        this.currentMatch = {
            title: title,
            score: matchScore,
            date: new Date().toLocaleDateString()
        };
    },

    saveJobResult(title) {
        if (!this.currentMatch) return;

        let saved = [];
        try { saved = JSON.parse(localStorage.getItem('savedJobs') || '[]'); } catch (e) { }

        saved.unshift(this.currentMatch);
        if (saved.length > 10) saved = saved.slice(0, 10);

        localStorage.setItem('savedJobs', JSON.stringify(saved));
        this.renderSavedJobs();
    },

    renderSavedJobs() {
        const wrap = document.getElementById('savedJobsList');
        const empty = document.getElementById('noSavedJobs');
        if (!wrap) return;

        let saved = [];
        try { saved = JSON.parse(localStorage.getItem('savedJobs') || '[]'); } catch (e) { }

        // remove existing rows
        Array.from(wrap.children).forEach(c => {
            if (c.id !== 'noSavedJobs') c.remove();
        });

        if (saved.length === 0) {
            if (empty) empty.style.display = 'flex';
            return;
        }

        if (empty) empty.style.display = 'none';

        saved.forEach(j => {
            const div = document.createElement('div');
            div.className = 'db-saved-job';
            let color = j.score >= 80 ? 'green' : (j.score >= 60 ? 'amber' : 'red');
            div.innerHTML = `
                <div>
                   <div class="db-saved-job-title">${j.title}</div>
                   <div class="db-saved-job-meta">Saved on ${j.date}</div>
                </div>
                <div>
                   <span class="db-badge ${color}">${j.score}% Match</span>
                </div>
            `;
            wrap.appendChild(div);
        });
    }

};

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    DashboardApp.init();
});
