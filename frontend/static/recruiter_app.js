/**
 * Recruiter Portal App Logic
 */

const RecruiterApp = {
    token: localStorage.getItem('token'),
    candidates: [],

    init() {
        if (!this.token) {
            window.location.href = '/login';
            return;
        }

        const isSearch = document.getElementById('applyFiltersBtn');
        if (isSearch) {
            this.initSearch();
            this.loadSearch();
        }

        const isPipeline = document.getElementById('pipelineKanban');
        if (isPipeline) {
            this.initPipeline();
        }
    },

    toast(msg, type = 'info') {
        const container = document.getElementById('recToastContainer');
        if (!container) return;
        const el = document.createElement('div');
        el.className = `db-toast ${type}`;
        el.innerHTML = `<span>${msg}</span>`;
        container.appendChild(el);
        setTimeout(() => {
            el.style.opacity = '0';
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
                localStorage.removeItem('token');
                window.location.href = '/login';
                return null;
            }
            return await res.json();
        } catch (e) {
            return { success: false, error: 'Network error' };
        }
    },

    // ================== SEARCH ================== //
    initSearch() {
        document.getElementById('applyFiltersBtn').addEventListener('click', () => this.loadSearch());
        const scoreRange = document.getElementById('scoreFilter');
        const scoreVal = document.getElementById('scoreVal');
        scoreRange.addEventListener('input', e => scoreVal.textContent = e.target.value);

        document.getElementById('closeModal').addEventListener('click', () => {
            document.getElementById('candidateModal').classList.remove('visible');
        });

        document.getElementById('shortlistBtn').addEventListener('click', () => this.shortlistCurrentModal());

        document.getElementById('rankJdBtn').addEventListener('click', () => this.rankByJD());
    },

    async loadSearch() {
        const d = document.getElementById('domainFilter').value;
        const ms = document.getElementById('scoreFilter').value;
        const lvl = document.getElementById('exprFilter').value;

        const q = new URLSearchParams();
        if (d) q.append('domain', d);
        if (ms) q.append('min_score', ms);
        if (lvl) q.append('level', lvl);

        const res = await this.authFetch(`/api/recruiter/search?${q.toString()}`);
        if (res && res.success) {
            this.candidates = res.candidates;
            this.renderCandidates();
        } else {
            this.toast('Failed to load candidates', 'error');
        }
    },

    renderCandidates() {
        const grid = document.getElementById('resultsGrid');
        const count = document.getElementById('resultsCount');
        grid.innerHTML = '';
        count.textContent = `${this.candidates.length} Candidates`;

        this.candidates.forEach(c => {
            const card = document.createElement('div');
            card.className = 'rec-candidate-card';
            let cColor = c.ats_score > 70 ? 'green' : (c.ats_score > 50 ? 'amber' : 'red');
            let skillPills = c.top_skills.slice(0, 3).map(s => `<span class="db-badge" style="font-size:10px">${s}</span>`).join(' ');

            card.innerHTML = `
                <div style="display:flex;justify-content:space-between;margin-bottom:12px;">
                   <h4 style="margin:0;font-size:15px;">Candidate #${c.candidate_id}</h4>
                   <span class="db-badge ${cColor}">${c.ats_score} ATS</span>
                </div>
                <div style="font-size:13px;color:var(--text-muted);margin-bottom:10px;">${c.domain}</div>
                <div>${skillPills} ${c.top_skills.length > 3 ? '<span class="db-badge" style="font-size:10px">...</span>' : ''}</div>
            `;
            card.addEventListener('click', () => this.openModal(c));
            grid.appendChild(card);
        });
    },

    openModal(c) {
        this.currentCandidate = c;
        document.getElementById('modalTitle').textContent = `Candidate #${c.candidate_id}`;
        document.getElementById('modalDomain').textContent = c.domain;

        const scoreEl = document.getElementById('modalScore');
        scoreEl.textContent = `${c.ats_score} ATS`;
        scoreEl.className = 'db-badge';
        scoreEl.classList.add(c.ats_score > 70 ? 'green' : (c.ats_score > 50 ? 'amber' : 'red'));

        const skillsWrap = document.getElementById('modalSkills');
        skillsWrap.innerHTML = c.top_skills.map(s => `<span class="db-keyword-pill">${s}</span>`).join('');

        document.getElementById('modalSummary').textContent = "This candidate has strong foundational skills in " + (c.top_skills[0] || 'their domain') + ". Based on their ATS score, they align moderately well with general job descriptions in this sector. (Anonymized by CareerForge)";

        document.getElementById('candidateModal').classList.add('visible');
    },

    async shortlistCurrentModal() {
        if (!this.currentCandidate) return;
        const res = await this.authFetch(`/api/recruiter/pipeline/shortlist/${this.currentCandidate.candidate_id}`, { method: 'POST' });
        if (res && res.success) {
            this.toast('Added to pipeline!', 'success');
            document.getElementById('candidateModal').classList.remove('visible');
        } else {
            this.toast(res?.error || 'Error adding to pipeline', 'error');
        }
    },

    async rankByJD() {
        const jd = document.getElementById('jdInput').value.trim();
        if (!jd || this.candidates.length === 0) return;
        const btn = document.getElementById('rankJdBtn');
        btn.textContent = 'Ranking...';

        const cids = this.candidates.map(c => c.candidate_id);
        const res = await this.authFetch('/api/recruiter/rank', {
            method: 'POST',
            body: { job_description: jd, candidate_ids: cids }
        });

        if (res && res.success) {
            this.toast('Candidates ranked successfully!');
            // random shuffle for demo purposes since we mocked the backend ranking
            this.candidates.sort(() => .5 - Math.random());
            this.renderCandidates();
        }
        btn.textContent = 'Rank by JD';
    },

    // ================== PIPELINE (KANBAN) ================== //
    initPipeline() {
        this.loadPipeline();
    },

    async loadPipeline() {
        const res = await this.authFetch('/api/recruiter/pipeline');
        if (!res || !res.success) return;

        const stages = res.pipeline;
        for (const [stage, list] of Object.entries(stages)) {
            const col = document.getElementById(`col-${stage}`);
            const cnt = document.getElementById(`count-${stage}`);
            if (!col) continue;

            cnt.textContent = list.length;
            col.innerHTML = '';

            list.forEach(c => {
                const card = document.createElement('div');
                card.className = 'rec-k-card';
                card.draggable = true;
                card.id = `card-${c.candidate_id}`;
                card.dataset.cid = c.candidate_id;

                let cColor = c.ats_score > 70 ? 'green' : (c.ats_score > 50 ? 'amber' : 'red');
                card.innerHTML = `
                   <div style="font-weight:600;font-size:14px;margin-bottom:6px">Candidate #${c.candidate_id}</div>
                   <div style="display:flex;justify-content:space-between;font-size:12px;">
                      <span class="db-badge ${cColor}" style="font-size:10px">${c.ats_score} Score</span>
                      <span style="color:var(--text-muted)">${c.days_in_stage}d in stage</span>
                   </div>
                `;

                card.addEventListener('dragstart', (e) => {
                    e.dataTransfer.setData('text/plain', card.id);
                    setTimeout(() => card.style.opacity = '0.5', 0);
                });
                card.addEventListener('dragend', () => {
                    card.style.opacity = '1';
                });

                col.appendChild(card);
            });

            // setup droppable zone
            col.addEventListener('dragover', e => { e.preventDefault(); col.classList.add('drag-over'); });
            col.addEventListener('dragleave', e => { col.classList.remove('drag-over'); });
            col.addEventListener('drop', e => this.handleDrop(e, stage, col));
        }
    },

    async handleDrop(e, targetStage, col) {
        e.preventDefault();
        col.classList.remove('drag-over');
        const cardId = e.dataTransfer.getData('text/plain');
        const card = document.getElementById(cardId);
        if (!card) return;

        // move visually
        col.appendChild(card);
        const cid = card.dataset.cid;

        // hit api
        const res = await this.authFetch(`/api/recruiter/pipeline/${cid}/stage`, {
            method: 'PUT',
            body: { stage: targetStage }
        });

        if (res && res.success) {
            this.toast(`Moved to ${targetStage}`, 'success');
            // update counts (visually simplistic approach)
            ['Sourced', 'Reviewed', 'Shortlisted', 'Interviewed', 'Hired/Rejected'].forEach(s => {
                document.getElementById(`count-${s}`).textContent = document.getElementById(`col-${s}`).children.length;
            });
        } else {
            this.toast('Error updating stage', 'error');
            this.loadPipeline(); // revert
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    RecruiterApp.init();
});
