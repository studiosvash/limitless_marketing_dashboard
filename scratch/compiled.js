class Component extends DCLogic {
    state = {
    tab: 'overview', seoOpen: true, adsOpen: true,
    cmpFilter: 'all', cmpSearch: '', cmpOpenId: null, cmpSort: { key: 'spend', dir: -1 },
    editBudgetId: null, editBudgetVal: '', termFilter: 'all', termCampaign: null,
    trmSearch: '', trmMatch: 'all', trmSort: { key: 'cost', dir: -1 }, trmSel: [], trmPage: 0, trmPer: 10, negMenuFor: null,
    projectId: 'fusehealth', projects: [],
    addSiteOpen: false, addSiteDomain: '', addSiteName: '', addSiteError: null, addSiteBusy: false,
    range: '30d',
    cache: {}, loading: true, error: null,
    sync: { active: false, progress: 0, step: '', cost: 0 },
    freshness: 'Weekly · Mon',
    explorerQ: '', explorerLoc: 'United States', research: null, researching: false,
    matchType: 'broad', selectedKws: [], sendOpen: false, exportOpen: false, sendSub: null, newListName: '', kwLists: [], toast: null, showLists: false,
    resVolMin: 0, resKdMin: 0, resKdMax: 100, resIntents: [], resIncl: '', resExcl: '', resOpenFilter: null, resGroup: null, resGroupMode: 'number', resDrawer: null,
    kwSeg: null, kwSort: { key: 'clicks', dir: -1 },
    blFilter: 'all', blSort: { key: 'rank', dir: -1 },
    blTab: 'overview', blFollow: 'all', gapOnly: true,
    offSort: { key: 'sessions', dir: -1 },
    pgSort: { key: 'clicks', dir: -1 },
    auSub: 'overview', auSev: 'all', auCat: 'all', auSearch: '', auOpen: null, auView: 'table', auPgSearch: '', auPgSort: { key: 'score', dir: 1 },
    auCmpA: null, auCmpB: null, auCmpFilter: 'all', auProg: { score: true, errors: true, warnings: true, notices: false, pages: false },
    aiSub: 'visibility', aiPlat: { chatgpt: true, perplexity: true }, aiOpen: null,
    aiWiz: 1, aiWizBrand: null, aiWizAliases: null, aiWizComps: null, aiWizCompInput: '', aiWizSel: null, aiWizCustom: '', aiWizBusy: false,
    aiTgOpen: false, aiListFilter: 'all', aiListsOpen: false, aiNewPlName: '',
    aiComposerOpen: false, aiComposerText: '', aiComposerList: null,
    aiCfgOpen: null, aiCfgDraft: null,
    aiExpQ: '', aiExploring: false, aiExp: null, aiExpSel: [], aiExpAddOpen: false,
    aiKwQ: '', aiKwSeg: 'all', aiKwSel: [], aiKwAddOpen: false,
    aiInspQ: '', aiInspecting: false, aiInspEntry: null,
    crawlCfg: null, crawlSaved: false, auPage: null, rules: null,
    alFilter: 'all',
    creds: { gsc: '', ga4: '' }, credsFor: null, credsSaved: false,
    prefs: null, prefsFor: null,
    settingsSub: 'general', setFor: null,
    wsDraft: null, notifDraft: null, aiDraft: null, secDraft: null, dataDraft: null, teamDraft: null,
    syncCfg: null, platConn: null, budgetCap: 75, budgetEnforce: true,
    savedWs: false, savedNotif: false, savedAi: false, savedData: false, savedBudget: false,
    inviteEmail: '', inviteRole: 'Analyst', newTokenName: '',
    inviteMode: 'email', inviteStatusMsg: null, inviteErrorMsg: null,
    acceptInviteToken: null, acceptEmail: '', acceptRole: '', acceptInvitedBy: '', acceptUsername: '', acceptPassword: '', acceptError: null, acceptSuccess: null,
    cpwOld: '', cpwNew: '', cpwNew2: '', cpwErr: false, cpwMsg: '', cpwBusy: false
  };

  /* ---------- constants ---------- */
  get VALID() { return ['overview', 'seo', 'keywords', 'positioning', 'backlinks', 'offsite', 'pages', 'ai', 'ads', 'campaigns', 'terms', 'attribution', 'alerts', 'settings']; }
  get SEOTABS() { return ['seo', 'keywords', 'positioning', 'backlinks', 'offsite', 'pages', 'ai']; }
  get ADSTABS() { return ['ads', 'campaigns', 'terms', 'attribution']; }
  get RES() { return { overview: 'overview', seo: 'seo', keywords: 'keywords', positioning: 'positions', backlinks: 'backlinks', offsite: 'offsite', pages: 'audit', ai: 'ai', ads: 'ads', campaigns: 'ads', terms: 'ads', attribution: 'ads', alerts: 'alerts', settings: 'settings' }; }

  /* ---------- lifecycle ---------- */
  componentDidMount() {
    this._alive = true;
    this._onHash = () => {
      const raw = (location.hash || '').slice(1);
      if (raw.startsWith('accept-invite')) {
        const q = raw.split('?')[1] || '';
        const params = new URLSearchParams(q);
        const token = params.get('token');
        if (token && token !== this.state.acceptInviteToken) {
          this.setState({ acceptInviteToken: token });
          this.checkInviteStatus(token);
        }
      } else {
        const t = raw;
        if (this.state.acceptInviteToken) this.setState({ acceptInviteToken: null });
        if (this.VALID.includes(t) && t !== this.state.tab) this.go(t);
      }
    };
    window.addEventListener('hashchange', this._onHash);
    this.installA11y();
    const wait = () => {
      if (!this._alive) return;
      if (window.FuseAPI && window.FuseFixtures) this.boot(); else setTimeout(wait, 40);
    };
    wait();
  }
  componentWillUnmount() {
    this._alive = false;
    window.removeEventListener('hashchange', this._onHash);
    if (this._iv) clearInterval(this._iv);
    if (this._a11yObs) this._a11yObs.disconnect();
    document.removeEventListener('keydown', this._onKeyAct);
    document.removeEventListener('keydown', this._onEsc);
  }

  /* ---------- accessibility: keyboard operability for all clickable UI ---------- */
  installA11y() {
    /* Enter / Space activates any element with a button/switch role (native handling
       is left alone for real <button>/<a>/form controls). */
    this._onKeyAct = (e) => {
      if (e.key !== 'Enter' && e.key !== ' ' && e.key !== 'Spacebar') return;
      const t = e.target;
      if (!t || !t.getAttribute) return;
      const role = t.getAttribute('role');
      if (role !== 'button' && role !== 'switch') return;
      const tag = t.tagName.toLowerCase();
      if (tag === 'input' || tag === 'select' || tag === 'textarea' || tag === 'button' || tag === 'a') return;
      e.preventDefault();
      t.click();
    };
    document.addEventListener('keydown', this._onKeyAct);
    /* Escape closes transient popovers / menus */
    this._onEsc = (e) => {
      if (e.key !== 'Escape') return;
      const s = this.state;
      if (s.addSiteOpen || s.negMenuFor || s.sendOpen || s.exportOpen) {
        this.setState({ addSiteOpen: false, negMenuFor: null, sendOpen: false, exportOpen: false });
      }
    };
    document.addEventListener('keydown', this._onEsc);
    /* re-sweep on every render (screen switches, drawers opening, etc.) */
    this._a11yObs = new MutationObserver(() => {
      if (this._a11yRaf) return;
      this._a11yRaf = requestAnimationFrame(() => { this._a11yRaf = 0; this.a11ySweep(); });
    });
    this._a11yObs.observe(document.body, { childList: true, subtree: true });
    this.a11ySweep();
  }

  a11ySweep() {
    /* 1. make anything already tagged with a role keyboard-focusable */
    document.querySelectorAll('[role="button"]:not([tabindex]),[role="switch"]:not([tabindex])')
      .forEach(el => el.setAttribute('tabindex', '0'));
    /* 2. promote leaf clickables (pointer cursor, no interactive descendant) to buttons.
       Table structural tags are excluded — role=button is invalid on tr/td. */
    const cand = document.querySelectorAll('div,span,li,p');
    const ptr = new WeakSet();
    const list = [];
    for (let i = 0; i < cand.length; i++) {
      const el = cand[i];
      let cs;
      try { cs = getComputedStyle(el); } catch (e) { continue; }
      if (cs.cursor === 'pointer') { ptr.add(el); list.push(el); }
    }
    for (let k = 0; k < list.length; k++) {
      const el = list[k];
      if (el.getAttribute('data-a11y') != null) continue;
      if (el.hasAttribute('role') || el.hasAttribute('tabindex')) { el.setAttribute('data-a11y', ''); continue; }
      const kids = el.getElementsByTagName('*');
      let leaf = true;
      for (let j = 0; j < kids.length; j++) { if (ptr.has(kids[j])) { leaf = false; break; } }
      if (!leaf) continue;
      el.setAttribute('role', 'button');
      el.setAttribute('tabindex', '0');
      el.setAttribute('data-a11y', '');
    }
  }

  boot() {
    const api = window.FuseAPI;
    const base = (this.props.apiBaseUrl || '').trim();
    if (base) api.config.baseUrl = base;
    if (this.props.demoLatency === false) { api.config.minLatency = 0; api.config.maxLatency = 0; }
    const hh = (location.hash || '').slice(1);
    if (hh.startsWith('accept-invite')) {
      const q = hh.split('?')[1] || '';
      const params = new URLSearchParams(q);
      const token = params.get('token');
      if (token) {
        this.setState({ acceptInviteToken: token });
        this.checkInviteStatus(token);
      }
    }
    const tab = this.VALID.includes(hh) ? hh : this.state.tab;
    const range = ['7d', '30d', '90d'].includes(this.props.defaultRange) ? this.props.defaultRange : this.state.range;
    let kwLists = [];
    try { kwLists = JSON.parse(localStorage.getItem('fh_keyword_lists') || '[]') || []; } catch (e) {}
    if (!kwLists.length) kwLists = [{ id: 'l1', name: 'Priority targets', keywords: [] }];
    /* Served-copy patch: restore the last selected project across page reloads (the upstream
       design file resets to the hardcoded default project on every reload). Falls back to
       the first real project if the remembered one no longer exists. */
    let pid = this.state.projectId;
    try { pid = localStorage.getItem('fh_selected_project') || pid; } catch (e) {}
    this.setState({ tab, range, kwLists, projectId: pid, seoOpen: this.state.seoOpen || this.SEOTABS.includes(tab), adsOpen: this.state.adsOpen || this.ADSTABS.includes(tab) });
    this._hist = [Object.assign(this.navSnapshot(), { tab, projectId: pid })];
    this._histIdx = 0;
    api.get('/api/projects').then(ps => {
      if (!this._alive) return;
      this.setState({ projects: ps });
      if (ps.length && !ps.some(p => p.id === pid)) {
        this.setState({ projectId: ps[0].id });
        this.fetchTab(tab, ps[0].id, range, false);
        if (tab !== 'alerts') this.fetchTab('alerts', ps[0].id, range, false);
      }
    }).catch(() => {});
    this.fetchTab(tab, pid, range, false);
    if (tab !== 'alerts') this.fetchTab('alerts', pid, range, false);
    fetch('/static/spa/us_cities.json').then(r => r.json()).then(locs => { this.setState({ allUsCities: locs }); }).catch(() => {});
  }

  /* ---------- data ---------- */
  key(tab, pid, range) {
    pid = pid || this.state.projectId; range = range || this.state.range;
    return pid + ':' + tab + (tab === 'overview' || tab === 'offsite' || this.RES[tab] === 'ads' ? ':' + range : '');
  }

  fetchTab(tab, pid, range, force) {
    pid = pid || this.state.projectId; range = range || this.state.range;
    const k = this.key(tab, pid, range);
    if (!force && this.state.cache[k]) { if (tab === this.state.tab) this.setState({ loading: false }); return; }
    if (tab === this.state.tab) this.setState({ loading: true, error: null });
    const params = (tab === 'overview' || tab === 'positioning' || tab === 'offsite' || this.RES[tab] === 'ads') ? { range } : undefined;
    window.FuseAPI.get('/api/projects/' + pid + '/' + this.RES[tab], params)
      .then(data => {
        if (!this._alive) return;
        this.setState(s => {
          const next = { cache: Object.assign({}, s.cache) };
          next.cache[k] = data;
          if (s.tab === tab) next.loading = false;
          if (tab === 'settings' && s.credsFor !== pid) {
            next.creds = { gsc: data.credentials.gsc_property, ga4: data.credentials.ga4_property_id };
            next.credsFor = pid;
          }
          if (tab === 'settings' && s.prefsFor !== pid) {
            next.prefs = Object.assign({}, data.prefs);
            next.prefsFor = pid;
          }
          if (tab === 'settings' && (force || s.setFor !== pid)) {
            next.wsDraft = Object.assign({}, data.workspace);
            next.notifDraft = Object.assign({}, data.notifications);
            next.aiDraft = Object.assign({}, data.aiConfig);
            next.secDraft = JSON.parse(JSON.stringify(data.security));
            next.dataDraft = Object.assign({}, data.dataPrefs);
            next.teamDraft = JSON.parse(JSON.stringify(data.team));
            next.syncCfg = Object.assign({}, data.syncConfig);
            next.platConn = Object.assign({}, data.platformConnectors);
            next.budgetCap = data.budget.cap;
            next.budgetEnforce = data.budget.enforce;
            next.setFor = pid;
          }
          return next;
        });
      })
      .catch(e => { if (this._alive) this.setState({ loading: false, error: (e && e.message) || 'Request failed' }); });
  }

  go(tab) {
    this.pushNav({ tab });
    this.setState({ tab, seoOpen: this.state.seoOpen || this.SEOTABS.includes(tab), adsOpen: this.state.adsOpen || this.ADSTABS.includes(tab), error: null });
    try { if (('#' + tab) !== location.hash) history.replaceState(null, '', '#' + tab); } catch (e) {}
    this.fetchTab(tab, this.state.projectId, this.state.range, false);
  }

  /* ---------- universal in-app navigation history ---------- */
  navSnapshot() {
    const s = this.state;
    return { tab: s.tab, projectId: s.projectId, research: s.research, kwSeg: s.kwSeg, blFilter: s.blFilter, alFilter: s.alFilter, auSub: s.auSub, aiSub: s.aiSub };
  }
  sameNav(a, b) {
    return a && b && a.tab === b.tab && a.projectId === b.projectId && a.research === b.research && a.kwSeg === b.kwSeg && a.blFilter === b.blFilter && a.alFilter === b.alFilter && a.auSub === b.auSub && a.aiSub === b.aiSub;
  }
  pushNav(overrides) {
    if (this._navApplying) return;
    const snap = Object.assign(this.navSnapshot(), overrides || {});
    if (!this._hist) { this._hist = [snap]; this._histIdx = 0; return; }
    if (this.sameNav(this._hist[this._histIdx], snap)) return;
    this._hist = this._hist.slice(0, this._histIdx + 1);
    this._hist.push(snap);
    this._histIdx = this._hist.length - 1;
  }
  applyNav(idx) {
    const snap = this._hist && this._hist[idx];
    if (!snap) return;
    this._histIdx = idx;
    this._navApplying = true;
    const pidChanged = snap.projectId !== this.state.projectId;
    this.setState({
      tab: snap.tab, projectId: snap.projectId, research: snap.research,
      kwSeg: snap.kwSeg, blFilter: snap.blFilter, alFilter: snap.alFilter,
      auSub: snap.auSub || 'overview', auOpen: null,
      aiSub: snap.aiSub || 'visibility', aiOpen: null,
      seoOpen: this.state.seoOpen || this.SEOTABS.includes(snap.tab), adsOpen: this.state.adsOpen || this.ADSTABS.includes(snap.tab), error: null,
      selectedKws: [], sendOpen: false, exportOpen: false, sendSub: null, showLists: false
    });
    try { if (('#' + snap.tab) !== location.hash) history.replaceState(null, '', '#' + snap.tab); } catch (e) {}
    this.fetchTab(snap.tab, snap.projectId, this.state.range, false);
    if (pidChanged && snap.tab !== 'alerts') this.fetchTab('alerts', snap.projectId, this.state.range, false);
    setTimeout(() => { this._navApplying = false; }, 0);
  }
  histBack() { if (this._hist && this._histIdx > 0) this.applyNav(this._histIdx - 1); }
  histFwd() { if (this._hist && this._histIdx < this._hist.length - 1) this.applyNav(this._histIdx + 1); }

  toggleAddSite() {
    this.setState(s => ({ addSiteOpen: !s.addSiteOpen, addSiteDomain: '', addSiteName: '', addSiteError: null }));
  }
  addSiteSubmit() {
    if (this.state.addSiteBusy) return;
    const domain = this.state.addSiteDomain.trim().toLowerCase().replace(/^https?:\/\//, '').replace(/\/$/, '');
    if (!domain || !/^[a-z0-9][a-z0-9\-\.]*\.[a-z]{2,}$/.test(domain)) {
      this.setState({ addSiteError: 'Enter a valid domain, e.g. example.com' });
      return;
    }
    if (this.state.projects.some(p => p.domain === domain)) {
      this.setState({ addSiteError: 'That site is already added' });
      return;
    }
    this.setState({ addSiteBusy: true, addSiteError: null });
    window.FuseAPI.post('/api/projects', { domain, name: this.state.addSiteName.trim() || undefined })
      .then(p => {
        if (!this._alive) return;
        this.setState(s => ({ projects: s.projects.concat([p]), addSiteBusy: false, addSiteOpen: false, addSiteDomain: '', addSiteName: '' }));
        if (p.gsc_connected === false) {
          this.notify('Site added, but not found in Search Console. Please connect account in Settings.');
        } else {
          this.notify('Added ' + p.domain + ' — fetching data…');
        }
        this.setProject(p.id);
        // Auto-start the initial sync that the backend kicked off when creating the site.
        // p.sync_task_id is the task_id returned by POST /api/projects; passing it to
        // startSync() skips the redundant POST /sync and goes straight to polling.
        if (p.sync_task_id != null) {
          setTimeout(() => { if (this._alive) this.startSync('all', p.sync_task_id); }, 300);
        }
      })
      .catch(err => { if (this._alive) this.setState({ addSiteBusy: false, addSiteError: err.detail || 'Could not add site' }); });
  }
  setProject(pid) {
    try { localStorage.setItem('fh_selected_project', pid); } catch (e) {}
    this.pushNav({ projectId: pid, research: null, kwSeg: null, blFilter: 'all', alFilter: 'all' });
    this.setState({ projectId: pid, research: null, kwSeg: null, blFilter: 'all', alFilter: 'all', crawlCfg: null, crawlSaved: false, auPage: null, rules: null, termCampaign: null, cmpSearch: '', cmpOpenId: null, editBudgetId: null });
    this.fetchTab(this.state.tab, pid, this.state.range, false);
    if (this.state.tab !== 'alerts') this.fetchTab('alerts', pid, this.state.range, false);
    if (this.state.tab !== 'settings') { /* creds/prefs re-seed on next settings visit */ }
    this.setState({ credsFor: null, prefsFor: null });
  }

  setRange(r) {
    this.setState({ range: r });
    if (this.state.tab === 'overview' || this.state.tab === 'positioning' || this.state.tab === 'offsite' || this.ADSTABS.includes(this.state.tab)) {
      this.fetchTab(this.state.tab, this.state.projectId, r, false);
    }
  }

  /* ---------- sync ---------- */
  /* startSync(scope, preTaskId)
   *   scope      – 'all' | 'positions' | 'backlinks' | etc.
   *   preTaskId  – (optional) task_id already created server-side (e.g., from POST /api/projects).
   *                When supplied the POST /api/projects/<slug>/sync call is skipped and we go
   *                straight to polling, avoiding a redundant second sync run. */
  startSync(scope, preTaskId) {
    if (this.state.sync.active && (!this.state.sync.projectId || this.state.sync.projectId === this.state.projectId)) return;
    const pid = this.state.projectId;
    const activeScope = scope || 'all';

    const _startPolling = (t) => {
      if (!this._alive) return;
      this.setState({ sync: { active: true, scope: activeScope, progress: 0.02, step: (t.steps && t.steps[0]) || 'Starting…', cost: t.est_cost || 0, projectId: pid } });
      this._iv = setInterval(() => {
        window.FuseAPI.get('/api/tasks/' + t.task_id).then(st => {
          if (!this._alive) { clearInterval(this._iv); return; }
          if (st.done) {
            clearInterval(this._iv); this._iv = null;
            this.setState(s => {
              const cache = {};
              Object.keys(s.cache).forEach(k2 => { if (k2.indexOf(pid + ':') !== 0) cache[k2] = s.cache[k2]; });
              return { sync: { active: false, scope: null, progress: 1, step: 'Done', cost: t.est_cost || 0, projectId: null }, freshness: 'Just now', cache };
            });
            this.fetchTab(this.state.tab, pid, this.state.range, true);
            if (this.state.tab !== 'alerts') this.fetchTab('alerts', pid, this.state.range, false);
            const proj = this.state.projects.find(p => p.id === pid) || {};
            const dom = proj.domain || pid;
            const scopeNotif = { audit: 'Crawl complete — Site Audit refreshed for ' + dom, positions: 'Positioning data refreshed for ' + dom, positioning: 'Positioning data refreshed for ' + dom, keywords: 'Keywords data refreshed for ' + dom, backlinks: 'Backlinks data refreshed for ' + dom, ads: 'Ads data refreshed for ' + dom, ai: 'AI Optimization data refreshed for ' + dom, overview: 'Overview data refreshed for ' + dom, seo: 'SEO data refreshed for ' + dom };
            this.notify(scopeNotif[activeScope] || (activeScope === 'all' ? ('All modules refreshed for ' + dom) : (activeScope + ' refreshed for ' + dom)));
          } else {
            this.setState({ sync: { active: true, scope: activeScope, progress: st.progress, step: st.step, cost: t.est_cost || 0, projectId: pid } });
          }
        }).catch(() => {});
      }, 500);
    };

    if (preTaskId != null) {
      // Task already created server-side — skip POST /sync and go straight to polling.
      _startPolling({ task_id: preTaskId, est_cost: 0, steps: ['Syncing…'] });
      return;
    }

    window.FuseAPI.post('/api/projects/' + pid + '/sync', { scope: activeScope })
      .then(t => { _startPolling(t); })
      .catch(err => { if (this._alive) this.notify(err.detail || 'Could not start sync'); });
  }

  /* ---------- keyword explorer ---------- */
  runResearch() {
    const q = this.state.explorerQ.trim();
    if (!q || this.state.researching) return;
    this.setState({ researching: true, selectedKws: [], sendOpen: false, exportOpen: false, sendSub: null });
    window.FuseAPI.post('/api/research', { project: this.state.projectId, keywords: q.split(','), location: this.state.explorerLoc })
      .then(r => { if (this._alive) { r.seeds = q.toLowerCase(); this.setState({ researching: false, research: r, matchType: 'broad', resGroup: null, resDrawer: null, resVolMin: 0, resKdMin: 0, resKdMax: 100, resIntents: [], resIncl: '', resExcl: '', resOpenFilter: null }); this.pushNav({ research: r }); } })
      .catch(() => { if (this._alive) this.setState({ researching: false, error: 'Research request failed' }); });
  }

  // rows visible under the current match-type tab + filters (server-side over the cached expansion set in prod)
  matchRows(skipGroup) {
    const s = this.state;
    if (!s.research || !s.research.rows) return [];
    const sets = {
      all: null,
      broad: ['broad', 'phrase', 'exact'],
      phrase: ['phrase', 'exact'],
      exact: ['exact'],
      questions: ['questions'],
      related: ['related']
    };
    const allow = sets[s.matchType];
    let rows = allow ? s.research.rows.filter(r => allow.includes(r.match)) : s.research.rows.slice();
    if (s.resVolMin > 0) rows = rows.filter(r => r.volume >= s.resVolMin);
    if (s.resKdMin > 0 || s.resKdMax < 100) rows = rows.filter(r => r.kd >= s.resKdMin && r.kd <= s.resKdMax);
    if (s.resIntents.length) rows = rows.filter(r => s.resIntents.includes(r.intent));
    if (s.resIncl.trim()) { const t = s.resIncl.toLowerCase().split(',').map(x => x.trim()).filter(Boolean); rows = rows.filter(r => t.every(x => (r.kw || '').toLowerCase().indexOf(x) >= 0)); }
    if (s.resExcl.trim()) { const t = s.resExcl.toLowerCase().split(',').map(x => x.trim()).filter(Boolean); rows = rows.filter(r => !t.some(x => (r.kw || '').toLowerCase().indexOf(x) >= 0)); }
    if (!skipGroup && s.resGroup) { const grp = (s.resGroup || '').toLowerCase(); rows = rows.filter(r => { const kw = (r.kw || '').toLowerCase(); return (' ' + kw + ' ').indexOf(' ' + grp + ' ') >= 0 || kw.indexOf(grp) >= 0; }); }
    return rows;
  }

  rfToggle(name) {
    this.setState(st => ({ resOpenFilter: st.resOpenFilter === name ? null : name, sendOpen: false, exportOpen: false, sendSub: null }));
  }

  // token-based grouping over the visible (pre-group) set — the "By number / By volume" sidebar
  resGroups() {
    const s = this.state;
    const rows = this.matchRows(true);
    const seedTokens = new Set(((s.research && s.research.seeds) || s.explorerQ || '').toLowerCase().split(/[,\s]+/).filter(Boolean));
    const stop = new Set(['for', 'the', 'a', 'to', 'of', 'and', 'vs', 'is', 'how', 'what', 'does', 'can', 'why', 'when', 'where', 'who', 'much', 'get', 'near', 'me', 'at', 'in', 'on', 'you', 'similar', 'cover']);
    const gm = new Map();
    rows.forEach(r => {
      const seen = new Set();
      r.kw.split(' ').forEach(w => {
        if (seedTokens.has(w) || stop.has(w) || w.length < 3 || seen.has(w)) return;
        seen.add(w);
        const g = gm.get(w) || { word: w, count: 0, volume: 0 };
        g.count++; g.volume += r.volume; gm.set(w, g);
      });
    });
    const arr = Array.from(gm.values()).filter(g => g.count >= 2);
    arr.sort((a, b) => s.resGroupMode === 'volume' ? b.volume - a.volume : b.count - a.count);
    return arr.slice(0, 14);
  }

  selectedRows() {
    const set = new Set(this.state.selectedKws);
    return this.matchRows().filter(r => set.has(r.kw));
  }

  persistLists(lists) { try { localStorage.setItem('fh_keyword_lists', JSON.stringify(lists)); } catch (e) {} }

  // add a batch of keywords to a project's tracking (Position Tracking)
  sendKwsToTracking(pid, rows) {
    if (!rows.length) return;
    const payload = {
      keywords: rows.map(r => ({ kw: r.kw, volume: r.volume, kd: r.kd, cpc: r.cpc, intent: r.intent }))
    };
    window.FuseAPI.post('/api/projects/' + pid + '/keywords', payload).catch(() => {}).then(() => {
      if (!this._alive) return;
      this.setState(s => {
        const trackSet = new Set(rows.map(r => r.kw));
        const research = s.research ? Object.assign({}, s.research, {
          rows: s.research.rows.map(r => trackSet.has(r.kw) ? Object.assign({}, r, { tracked: true }) : r)
        }) : null;
        const cache = {};
        Object.keys(s.cache).forEach(k2 => {
          const t = k2.split(':')[1];
          if (k2.indexOf(pid + ':') === 0 && ['keywords', 'positioning', 'overview', 'settings'].includes(t)) return;
          cache[k2] = s.cache[k2];
        });
        return { research, cache, selectedKws: [], sendOpen: false, sendSub: null };
      });
      if (['keywords', 'positioning', 'overview'].includes(this.state.tab)) {
        this.fetchTab(this.state.tab, pid, this.state.range, true);
      }
      window.FuseAPI.get('/api/projects').then(ps => { if (this._alive) this.setState({ projects: ps }); }).catch(() => {});
      const proj = (this.state.projects.find(p => p.id === pid) || {}).domain || 'project';
      this.notify(rows.length + ' keyword' + (rows.length === 1 ? '' : 's') + ' sent to Position Tracking · ' + proj);
    });
  }

  addKwsToList(listId, rows) {
    const kws = rows.map(r => r.kw);
    const lists = this.state.kwLists.map(l => {
      if (l.id !== listId) return l;
      const merged = l.keywords.slice();
      kws.forEach(k => { if (!merged.includes(k)) merged.push(k); });
      return Object.assign({}, l, { keywords: merged });
    });
    this.persistLists(lists);
    const nm = (lists.find(l => l.id === listId) || {}).name || 'list';
    this.setState({ kwLists: lists, selectedKws: [], sendOpen: false, sendSub: null });
    this.notify(kws.length + ' keyword' + (kws.length === 1 ? '' : 's') + ' added to "' + nm + '"');
  }

  createListWith(name, rows) {
    const nm = (name || '').trim() || 'Keyword list ' + (this.state.kwLists.length + 1);
    const id = 'l' + Date.now();
    const lists = this.state.kwLists.concat([{ id, name: nm, keywords: rows.map(r => r.kw) }]);
    this.persistLists(lists);
    this.setState({ kwLists: lists, newListName: '', selectedKws: [], sendOpen: false, sendSub: null });
    this.notify('Created "' + nm + '" with ' + rows.length + ' keyword' + (rows.length === 1 ? '' : 's'));
  }

  deleteList(listId) {
    const lists = this.state.kwLists.filter(l => l.id !== listId);
    this.persistLists(lists);
    this.setState({ kwLists: lists });
    this.notify('List deleted');
  }

  removeKwFromList(listId, kw) {
    const lists = this.state.kwLists.map(l => l.id === listId ? Object.assign({}, l, { keywords: l.keywords.filter(k => k !== kw) }) : l);
    this.persistLists(lists);
    this.setState({ kwLists: lists });
  }

  sendListToTracking(listId) {
    const l = this.state.kwLists.find(x => x.id === listId);
    if (!l || !l.keywords.length) { this.notify('This list is empty'); return; }
    this.sendKwsToTracking(this.state.projectId, l.keywords.map(kw => ({ kw })));
  }

  // export selected (or all visible) rows as CSV or Excel-readable .xls
  exportRows(rows, format) {
    if (!rows.length) return;
    const cols = ['Keyword', 'Intent', 'Volume', 'KD%', 'CPC'];
    const val = r => [r.kw, r.intent, r.volume, r.kd, r.cpc];
    const base = (this.state.projectId || 'keywords') + '-keywords';
    let blob, name;
    if (format === 'xls') {
      const esc = v => String(v == null ? '' : v).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
      const head = '<tr>' + cols.map(c => '<th>' + esc(c) + '</th>').join('') + '</tr>';
      const body = rows.map(r => '<tr>' + val(r).map(v => '<td>' + esc(v) + '</td>').join('') + '</tr>').join('');
      const html = '<html xmlns:x="urn:schemas-microsoft-com:office:excel"><head><meta charset="utf-8"></head><body><table border="1">' + head + body + '</table></body></html>';
      blob = new Blob([html], { type: 'application/vnd.ms-excel' });
      name = base + '.xls';
    } else {
      const esc = v => '"' + String(v == null ? '' : v).replace(/"/g, '""') + '"';
      const text = [cols.join(',')].concat(rows.map(r => val(r).map(esc).join(','))).join('\n');
      blob = new Blob([text], { type: 'text/csv' });
      name = base + '.csv';
    }
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = name; a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 2000);
    this.setState({ exportOpen: false });
    this.notify('Exported ' + rows.length + ' keyword' + (rows.length === 1 ? '' : 's') + ' (' + format.toUpperCase() + ')');
  }

  /* ---------- ads actions ---------- */
  adsInvalidate(pid) {
    this.setState(s => {
      const cache = {};
      Object.keys(s.cache).forEach(k => { if (k.indexOf(pid + ':ads') !== 0) cache[k] = s.cache[k]; });
      return { cache };
    });
    this.fetchTab(this.state.tab, pid, this.state.range, true);
  }
  setCampaignStatus(c) {
    const pid = this.state.projectId;
    const next = c.status === 'enabled' ? 'paused' : 'enabled';
    window.FuseAPI.post('/api/projects/' + pid + '/ads/status', { campaignId: c.id, status: next })
      .then(() => { if (!this._alive) return; this.notify('"' + c.name + '" ' + (next === 'enabled' ? 'enabled — resumes serving on next sync' : 'paused')); this.adsInvalidate(pid); })
      .catch(() => this.notify('Could not update campaign'));
  }
  saveBudget(c) {
    const pid = this.state.projectId;
    const v = parseFloat(this.state.editBudgetVal);
    if (!v || v <= 0 || Math.round(v) === c.budget_daily) { this.setState({ editBudgetId: null }); return; }
    window.FuseAPI.post('/api/projects/' + pid + '/ads/budget', { campaignId: c.id, budgetDaily: v })
      .then(r => { if (!this._alive) return; this.setState({ editBudgetId: null }); this.notify('Daily budget for "' + c.name + '" set to $' + r.budgetDaily); this.adsInvalidate(pid); })
      .catch(() => { if (this._alive) { this.setState({ editBudgetId: null }); this.notify('Could not update budget'); } });
  }
  addNegative(t, matchType) {
    const pid = this.state.projectId;
    const mt = matchType || 'phrase';
    this.setState({ negMenuFor: null });
    window.FuseAPI.post('/api/projects/' + pid + '/ads/negatives', { term: t.term, matchType: mt, campaignId: t.campaignId })
      .then(() => { if (!this._alive) return; this.notify('"' + t.term + '" added as a ' + mt + '-match negative — written back to Google Ads on next sync'); this.adsInvalidate(pid); })
      .catch(() => this.notify('Could not add negative'));
  }

  bulkNegatives(list, matchType) {
    const pid = this.state.projectId;
    if (!list.length) return;
    Promise.all(list.map(t => window.FuseAPI.post('/api/projects/' + pid + '/ads/negatives', { term: t.term, matchType: matchType || 'phrase', campaignId: t.campaignId })))
      .then(() => { if (!this._alive) return; this.notify(list.length + ' negative keyword' + (list.length === 1 ? '' : 's') + ' queued — written back via CampaignCriterionService on next sync'); this.setState({ trmSel: [] }); this.adsInvalidate(pid); })
      .catch(() => this.notify('Could not add negatives'));
  }

  bulkPromote(list) {
    const pid = this.state.projectId;
    if (!list.length) return;
    Promise.all(list.map(t => window.FuseAPI.post('/api/projects/' + pid + '/ads/promote', { term: t.term })))
      .then(() => { if (!this._alive) return; this.notify(list.length + ' term' + (list.length === 1 ? '' : 's') + ' added to organic keyword tracking'); this.setState({ trmSel: [] }); this.adsInvalidate(pid); })
      .catch(() => this.notify('Could not add keywords'));
  }
  promoteTerm(t) {
    const pid = this.state.projectId;
    window.FuseAPI.post('/api/projects/' + pid + '/ads/promote', { term: t.term })
      .then(() => {
        if (!this._alive) return;
        this.notify('"' + t.term + '" added to organic keyword tracking');
        this.setState(s => { const cache = {}; Object.keys(s.cache).forEach(k => { if (k.indexOf(pid + ':') !== 0) cache[k] = s.cache[k]; }); return { cache }; });
        this.fetchTab(this.state.tab, pid, this.state.range, true);
      })
      .catch(() => this.notify('Could not add keyword'));
  }

  notify(msg) { this.setState({ toast: msg }); clearTimeout(this._nt); this._nt = setTimeout(() => { if (this._alive) this.setState({ toast: null }); }, 2600); }

  /* ---------- clipboard & bulk QoL helpers ---------- */
  copyText(txt, msg) {
    const done = () => this.notify(msg || 'Copied to clipboard');
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(txt).then(done).catch(() => { this.copyFallback(txt); done(); });
    } else { this.copyFallback(txt); done(); }
  }
  copyFallback(txt) {
    const ta = document.createElement('textarea');
    ta.value = txt; ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta); ta.select();
    try { document.execCommand('copy'); } catch (e) {}
    document.body.removeChild(ta);
  }
  copySelectedKws() {
    const rows = this.selectedRows();
    if (!rows.length) return;
    this.copyText(rows.map(r => r.kw).join('\n'), rows.length + ' keyword' + (rows.length === 1 ? '' : 's') + ' copied to clipboard');
  }
  copySummary() {
    const d = this.state.cache[this.key('overview')];
    if (!d) return;
    const proj = (this.state.projects.find(p => p.id === this.state.projectId) || {}).domain || '';
    const sec = (t, arr) => arr && arr.length ? t + ':\n' + arr.map(x => '\u2022 ' + x).join('\n') : '';
    const txt = ['Weekly summary \u2014 ' + proj, sec('Wins', d.summary.wins), sec('Critical', d.summary.critical), sec('Watch', d.summary.watch)].filter(Boolean).join('\n\n');
    this.copyText(txt, 'Weekly summary copied \u2014 paste into email or Slack');
  }
  ackAllAlerts() {
    const d = this.state.cache[this.key('alerts')];
    if (!d) return;
    const un = d.feed.filter(f => !f.acknowledged);
    if (!un.length) return;
    un.forEach(f => this.ackAlert(f.id));
    this.notify(un.length + ' alert' + (un.length === 1 ? '' : 's') + ' acknowledged');
  }

  /* ---------- crawl settings ---------- */
  editCrawl(patch, flipKey) {
    this.setState(st => {
      const data = st.cache[this.key('settings')];
      const base = st.crawlCfg || (data && data.crawl) || { maxPages: 500, frequency: 'monthly', jsRendering: false, respectRobots: true, excludedPaths: '' };
      const next = Object.assign({}, base, patch || {});
      if (flipKey) next[flipKey] = !base[flipKey];
      return { crawlCfg: next, crawlSaved: false };
    });
  }
  editRule(ruleId, patch) {
    const data = this.state.cache[this.key('settings')];
    const base = this.state.rules || (data && data.alertRules) || [];
    const next = base.map(r => r.id === ruleId ? Object.assign({}, r, patch) : r);
    this.setState({ rules: next });
    clearTimeout(this._rt);
    this._rt = setTimeout(() => {
      window.FuseAPI.put('/api/projects/' + this.state.projectId + '/settings', { alertRules: next })
        .then(() => { if (this._alive) this.notify('Alert rules updated'); }).catch(() => {});
    }, 600);
  }

  saveCrawl() {
    const cfg = this.state.crawlCfg;
    if (!cfg) { this.setState({ crawlSaved: true }); return; }
    window.FuseAPI.put('/api/projects/' + this.state.projectId + '/settings', { crawl: cfg }).then(() => {
      if (!this._alive) return;
      this.setState({ crawlSaved: true });
      this.notify('Crawl settings saved — applies to the next crawl');
    }).catch(() => {});
  }

  /* ---------- alerts ---------- */
  ackAlert(id) {
    const pid = this.state.projectId;
    window.FuseAPI.post('/api/alerts/' + id + '/ack', {}).then(() => {
      if (!this._alive) return;
      this.setState(s => {
        const k = this.key('alerts', pid, s.range);
        const cur = s.cache[k];
        if (!cur) return {};
        const cache = Object.assign({}, s.cache);
        cache[k] = { feed: cur.feed.map(f => f.id === id ? Object.assign({}, f, { acknowledged: true }) : f) };
        return { cache };
      });
    }).catch(() => {});
  }

  /* ---------- settings ---------- */
  saveCreds() {
    const pid = this.state.projectId;
    window.FuseAPI.put('/api/projects/' + pid + '/settings', {
      credentials: { gsc_property: this.state.creds.gsc, ga4_property_id: this.state.creds.ga4 }
    }).then(() => {
      if (!this._alive) return;
      this.setState({ credsSaved: true });
      setTimeout(() => { if (this._alive) this.setState({ credsSaved: false }); }, 1800);
    }).catch(() => {});
  }

  togglePref(keyName) {
    const prefs = Object.assign({}, this.state.prefs || {});
    prefs[keyName] = !prefs[keyName];
    this.setState({ prefs });
    window.FuseAPI.put('/api/projects/' + this.state.projectId + '/settings', { prefs }).catch(() => {});
  }

  /* ---------- extended settings ---------- */
  putSettings(body, msg, flag) {
    window.FuseAPI.put('/api/projects/' + this.state.projectId + '/settings', body).then(() => {
      if (!this._alive) return;
      if (flag) { this.setState({ [flag]: true }); setTimeout(() => { if (this._alive) this.setState({ [flag]: false }); }, 1800); }
      if (msg) this.notify(msg);
    }).catch(() => {});
  }
  editWs(patch) { this.setState(s => ({ wsDraft: Object.assign({}, s.wsDraft, patch), savedWs: false })); }
  saveWs() { this.putSettings({ workspace: this.state.wsDraft }, 'Workspace saved', 'savedWs'); }
  clearData() {
    if (window.confirm("Are you sure you want to permanently delete all synced analytics data for this project? This action cannot be undone.")) {
      const pid = this.props.ctx.route.params.id || window.activeProject;
      window.FuseAPI.del('/api/projects/' + pid + '/data')
        .then(() => {
          this.notify("Data cleared successfully. Reloading...");
          setTimeout(() => window.location.reload(), 1500);
        })
        .catch(e => this.notify("Failed to clear data: " + (e.message || "Unknown error")));
    }
  }
  editNotif(patch) { this.setState(s => ({ notifDraft: Object.assign({}, s.notifDraft, patch), savedNotif: false })); }
  toggleNotif(key) { this.setState(s => ({ notifDraft: Object.assign({}, s.notifDraft, { [key]: !s.notifDraft[key] }), savedNotif: false })); }
  saveNotif() { this.putSettings({ notifications: this.state.notifDraft }, 'Notification settings saved', 'savedNotif'); }
  editAi(patch) { this.setState(s => ({ aiDraft: Object.assign({}, s.aiDraft, patch), savedAi: false })); }
  saveAi() { this.putSettings({ aiConfig: this.state.aiDraft }, 'AI summary settings saved', 'savedAi'); }
  editData(patch) { this.setState(s => ({ dataDraft: Object.assign({}, s.dataDraft, patch), savedData: false })); }
  saveData() { this.putSettings({ dataPrefs: this.state.dataDraft }, 'Data preferences saved', 'savedData'); }
  editSyncCfg(module, cadence) {
    const next = Object.assign({}, this.state.syncCfg, { [module]: cadence });
    this.setState({ syncCfg: next });
    this.putSettings({ syncConfig: next }, 'Sync schedule updated');
  }
  togglePlatform(key) {
    const next = Object.assign({}, this.state.platConn, { [key]: !this.state.platConn[key] });
    this.setState({ platConn: next });
    this.putSettings({ platformConnectors: next }, (next[key] ? 'Connected ' : 'Disconnected ') + key);
  }
  setBudgetCap(v) {
    const cap = Math.max(5, parseInt(v, 10) || 5);
    this.setState({ budgetCap: cap, savedBudget: false });
    clearTimeout(this._bt); this._bt = setTimeout(() => this.putSettings({ budgetCap: cap }, 'Budget cap set to $' + cap, 'savedBudget'), 500);
  }
  toggleEnforce() {
    const v = !this.state.budgetEnforce;
    this.setState({ budgetEnforce: v });
    this.putSettings({ budgetEnforce: v }, v ? 'Soft cap enabled' : 'Soft cap disabled');
  }
  setInviteRole(r) { this.setState({ inviteRole: r }); }
  setInviteMode(m) {
    this.setState({ inviteMode: m, createUserError: null, inviteErrorMsg: null, inviteStatusMsg: null });
  }
  sendInvite() {
    const email = (this.state.inviteEmail || '').trim();
    const role = this.state.inviteRole || 'Analyst';
    if (!email || email.indexOf('@') < 0) { this.setState({ inviteErrorMsg: 'Enter a valid email address.' }); return; }
    this.setState({ inviteErrorMsg: null, inviteStatusMsg: 'Sending invitation...' });
    const pid = this.state.projectId;
    window.FuseAPI.post('/api/projects/' + pid + '/invite', { email, role })
      .then(res => {
        if (!this._alive) return;
        this.setState({ inviteEmail: '', inviteErrorMsg: null, inviteStatusMsg: 'Invitation sent to ' + email });
        this.notify('Invitation sent to ' + email);
        this.invalidateSettingsCacheAndReload(pid);
      })
      .catch(err => {
        const msg = (err && (err.detail || err.message)) || 'Could not send invitation. Check permissions.';
        this.setState({ inviteErrorMsg: msg, inviteStatusMsg: null });
      });
  }
  resendInvite(inviteId) {
    const pid = this.state.projectId;
    window.FuseAPI.post('/api/projects/' + pid + '/invite/' + inviteId + '/resend', {})
      .then(res => {
        if (!this._alive) return;
        this.notify('Invitation reminder sent!');
        this.invalidateSettingsCacheAndReload(pid);
      })
      .catch(err => {
        const msg = (err && (err.detail || err.message)) || 'Could not resend invitation.';
        this.notify(msg);
      });
  }
  revokeInvite(inviteId) {
    if (!window.confirm('Revoke this pending invitation?')) return;
    const pid = this.state.projectId;
    window.FuseAPI.del('/api/projects/' + pid + '/invite/' + inviteId)
      .then(() => {
        if (!this._alive) return;
        this.notify('Invitation revoked.');
        this.invalidateSettingsCacheAndReload(pid);
      })
      .catch(err => {
        const msg = (err && (err.detail || err.message)) || 'Could not revoke invitation.';
        this.notify(msg);
      });
  }
  invalidateSettingsCacheAndReload(pid) {
    this.setState(s => {
      const cache = {};
      Object.keys(s.cache).forEach(k => { if (k.indexOf(pid + ':settings') !== 0) cache[k] = s.cache[k]; });
      return { cache, setFor: null };
    });
    this.fetchTab('settings', pid, this.state.range, true);
  }
  checkInviteStatus(token) {
    this.setState({ acceptError: null, acceptSuccess: null, acceptEmail: '', acceptRole: '' });
    window.FuseAPI.get('/api/auth/invite-status?token=' + encodeURIComponent(token))
      .then(res => {
        if (!this._alive) return;
        if (res.valid) {
          this.setState({ acceptEmail: res.email, acceptRole: res.role, acceptInvitedBy: res.invited_by });
        } else {
          this.setState({ acceptError: 'This invitation link is no longer valid (' + (res.reason || 'expired') + ').' });
        }
      })
      .catch(err => {
        if (!this._alive) return;
        const msg = (err && (err.detail || err.message)) || 'Could not verify invitation link. It may have expired or already been accepted.';
        this.setState({ acceptError: msg });
      });
  }
  submitAcceptInvite() {
    const token = this.state.acceptInviteToken;
    const username = (this.state.acceptUsername || '').trim();
    const password = (this.state.acceptPassword || '').trim();
    if (!username) { this.setState({ acceptError: 'Please enter a username.' }); return; }
    if (password.length < 8) { this.setState({ acceptError: 'Password must be at least 8 characters long.' }); return; }
    this.setState({ acceptError: null });
    window.FuseAPI.post('/api/auth/accept-invite', { token, username, password })
      .then(res => {
        if (!this._alive) return;
        this.setState({ acceptSuccess: true, acceptInviteToken: null });
        this.notify('Account activated successfully! You can now log in.');
        setTimeout(() => {
          window.location.hash = '#/overview';
        }, 2000);
      })
      .catch(err => {
        if (!this._alive) return;
        const msg = (err && (err.detail || err.message)) || 'Could not accept invitation.';
        this.setState({ acceptError: msg });
      });
  }
  createUser() {
    const email = (this.state.inviteEmail || '').trim();
    const username = (this.state.inviteUsername || '').trim();
    const password = (this.state.invitePassword || '').trim();
    const role = this.state.inviteRole || 'Analyst';
    if (!email || email.indexOf('@') < 0) { this.setState({ createUserError: 'Enter a valid email address.' }); return; }
    if (!username) { this.setState({ createUserError: 'Username is required.' }); return; }
    if (password.length < 8) { this.setState({ createUserError: 'Password must be at least 8 characters.' }); return; }
    this.setState({ createUserError: null });
    const pid = this.state.projectId;
    window.FuseAPI.post('/api/projects/' + pid + '/team', { email, username, password, role })
      .then(() => {
        if (!this._alive) return;
        this.setState({ inviteEmail: '', inviteUsername: '', invitePassword: '', createUserError: null });
        this.notify('User "' + username + '" created successfully.');
        // Invalidate settings cache and team draft to reload team list
        this.setState(s => {
          const cache = {};
          Object.keys(s.cache).forEach(k => { if (k.indexOf(pid + ':settings') !== 0) cache[k] = s.cache[k]; });
          return { cache, teamDraft: null, setFor: null };
        });
        this.fetchTab('settings', pid, this.state.range, true);
      })
      .catch(err => {
        const msg = (err && (err.detail || err.message)) || 'Could not create user. Please try again.';
        this.setState({ createUserError: msg });
      });
  }
  changeRole(id, role) {
    const team = (this.state.teamDraft || []).map(m => m.id === id ? Object.assign({}, m, { role }) : m);
    this.setState({ teamDraft: team });
    this.putSettings({ team }, 'Role updated');
  }
  removeMember(id) {
    if (!window.confirm('Are you sure you want to permanently delete this user? This cannot be undone.')) return;
    const pid = this.state.projectId;
    window.FuseAPI.del('/api/projects/' + pid + '/team/' + id)
      .then(() => {
        if (!this._alive) return;
        this.notify('User deleted.');
        this.setState(s => {
          const cache = {};
          Object.keys(s.cache).forEach(k => { if (k.indexOf(pid + ':settings') !== 0) cache[k] = s.cache[k]; });
          return { cache, teamDraft: null, setFor: null };
        });
        this.fetchTab('settings', pid, this.state.range, true);
      })
      .catch(err => {
        const msg = (err && (err.detail || err.message)) || 'Could not delete user.';
        this.notify(msg);
      });
  }
  toggle2fa() {
    const sec = Object.assign({}, this.state.secDraft, { twofa: !this.state.secDraft.twofa });
    this.setState({ secDraft: sec });
    this.putSettings({ security: sec }, sec.twofa ? 'Two-factor enabled' : 'Two-factor disabled');
  }
  toggleSso() {
    const sec = Object.assign({}, this.state.secDraft, { sso: !this.state.secDraft.sso });
    this.setState({ secDraft: sec });
    this.putSettings({ security: sec }, sec.sso ? 'SSO enabled' : 'SSO disabled');
  }
  revokeSession(id) {
    const sec = Object.assign({}, this.state.secDraft, { sessions: this.state.secDraft.sessions.filter(x => x.id !== id) });
    this.setState({ secDraft: sec });
    this.putSettings({ security: sec }, 'Session revoked');
  }
  revokeToken(id) {
    const sec = Object.assign({}, this.state.secDraft, { tokens: this.state.secDraft.tokens.filter(x => x.id !== id) });
    this.setState({ secDraft: sec });
    this.putSettings({ security: sec }, 'Token revoked');
  }
  createToken() {
    const name = (this.state.newTokenName || '').trim();
    if (!name) { this.notify('Name the token first'); return; }
    const tok = { id: 'tk' + Date.now().toString(36), name, prefix: 'lm_live_' + Math.random().toString(36).slice(2, 6), created: new Date().toISOString().slice(0, 10), last_used: null };
    const sec = Object.assign({}, this.state.secDraft, { tokens: this.state.secDraft.tokens.concat([tok]) });
    this.setState({ secDraft: sec, newTokenName: '' });
    this.putSettings({ security: sec }, 'API token created — copy it now');
  }
  changePassword() {
    const s = this.state;
    if (s.cpwBusy) return;
    if (!s.cpwOld) { this.setState({ cpwErr: true, cpwMsg: 'Current password is required.' }); return; }
    if (s.cpwNew.length < 8) { this.setState({ cpwErr: true, cpwMsg: 'New password must be at least 8 characters.' }); return; }
    if (s.cpwNew !== s.cpwNew2) { this.setState({ cpwErr: true, cpwMsg: 'New passwords do not match.' }); return; }
    this.setState({ cpwBusy: true, cpwErr: false, cpwMsg: '' });
    window.FuseAPI.post('/api/auth/password', { old_password: s.cpwOld, new_password: s.cpwNew })
      .then(res => {
        if (!this._alive) return;
        this.setState({ cpwBusy: false, cpwOld: '', cpwNew: '', cpwNew2: '', cpwErr: false, cpwMsg: 'Password updated successfully.' });
        setTimeout(() => { if (this._alive) this.setState({ cpwMsg: '' }); }, 3000);
      })
      .catch(err => {
        if (!this._alive) return;
        this.setState({ cpwBusy: false, cpwErr: true, cpwMsg: err.detail || 'Failed to update password.' });
      });
  }

  setSettingsSub(sub) { this.setState({ settingsSub: sub }); }

  /* ---------- csv ---------- */
  downloadCsv(name, cols, rows) {
    const esc = v => '"' + String(v == null ? '' : v).replace(/"/g, '""') + '"';
    const text = [cols.map(c => c[0]).join(',')]
      .concat(rows.map(r => cols.map(c => esc(r[c[1]])).join(','))).join('\n');
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([text], { type: 'text/csv' }));
    a.download = name; a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  }

  /* ---------- formatting helpers ---------- */
  blHash(str) {
    let h = 1779033703 ^ str.length;
    for (let i = 0; i < str.length; i++) { h = Math.imul(h ^ str.charCodeAt(i), 3432918353); h = (h << 13) | (h >>> 19); }
    return function () { h = Math.imul(h ^ (h >>> 16), 2246822507); h = Math.imul(h ^ (h >>> 13), 3266489909); return ((h ^= h >>> 16) >>> 0) / 4294967296; };
  }
  fmt(n) {
    if (n == null) return '—';
    if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
    if (n >= 100000) return Math.round(n / 1000) + 'K';
    return n.toLocaleString('en-US');
  }
  money(n) { return '$' + (n == null ? '0.00' : Number(n).toFixed(2)); }
  posBadge(p) {
    const base = { display: 'inline-flex', alignItems: 'center', justifyContent: 'center', minWidth: '28px', height: '24px', borderRadius: '4px', fontSize: '12px', fontWeight: 600 };
    if (p == null) return Object.assign(base, { background: 'transparent', color: '#cbd5e1' });
    if (p <= 3) return Object.assign(base, { background: '#d1fae5', color: '#047857' });
    if (p <= 10) return Object.assign(base, { background: '#dbeafe', color: '#1d4ed8' });
    if (p <= 20) return Object.assign(base, { background: '#fef3c7', color: '#b45309' });
    return Object.assign(base, { background: '#f1f5f9', color: '#64748b' });
  }
  kdColor(kd) { return kd < 30 ? '#10b981' : kd < 60 ? '#f59e0b' : '#ef4444'; }
  intentView(intent) {
    const map = {
      informational: ['Info', '#dbeafe', '#1d4ed8'],
      commercial: ['Comm', '#d1fae5', '#047857'],
      transactional: ['Trans', '#ffedd5', '#c2410c'],
      navigational: ['Nav', '#f3e8ff', '#7e22ce']
    };
    const m = map[intent] || map.informational;
    return { label: m[0], style: { fontSize: '10px', fontWeight: 600, textTransform: 'uppercase', background: m[1], color: m[2], padding: '2px 6px', borderRadius: '4px' } };
  }
  sevChip(sev) {
    const map = { high: ['#fee2e2', '#b91c1c'], medium: ['#fef9c3', '#a16207'], info: ['#f1f5f9', '#64748b'] };
    const m = map[sev] || map.info;
    return { padding: '3px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', background: m[0], color: m[1], flexShrink: 0 };
  }
  spark(arr, w, hgt) {
    if (!arr || !arr.length) return '';
    const min = Math.min.apply(null, arr), max = Math.max.apply(null, arr);
    const span = (max - min) || 1;
    return arr.map((v, i) => {
      const x = (i * (w / (arr.length - 1))).toFixed(1);
      const y = (hgt - 1 - ((v - min) / span) * (hgt - 2)).toFixed(1);
      return x + ',' + y;
    }).join(' ');
  }
  linePts(arr, keyName, w, hgt) {
    if (!arr || !arr.length) return '';
    const max = Math.max.apply(null, arr.map(d => d[keyName])) || 1;
    return arr.map((d, i) => {
      const x = (i * (w / Math.max(1, arr.length - 1))).toFixed(1);
      const y = (hgt - 10 - (d[keyName] / max) * (hgt - 30)).toFixed(1);
      return x + ',' + y;
    }).join(' ');
  }
  toggleAuditCheck(checkId) {
    const pid = this.state.projectId;
    window.FuseAPI.post('/api/projects/' + pid + '/audit/toggle-check', { checkId }).then(() => {
      if (!this._alive) return;
      this.setState({ auOpen: null });
      this.fetchTab('pages', pid, this.state.range, true);
    }).catch(() => {});
  }

  sortRows(rows, sort) {
    const dir = sort.dir;
    return rows.slice().sort((a, b) => {
      const av = a[sort.key], bv = b[sort.key];
      if (typeof av === 'string' || typeof bv === 'string') return String(av || '').localeCompare(String(bv || '')) * dir;
      return ((av == null ? -1 : av) - (bv == null ? -1 : bv)) * dir;
    });
  }
  arrow(sort, keyName) { return sort.key === keyName ? (sort.dir === -1 ? ' ↓' : ' ↑') : ''; }
  mkSortHandler(stateKey, keyName) {
    return () => this.setState(s => {
      const cur = s[stateKey];
      return { [stateKey]: { key: keyName, dir: cur.key === keyName ? -cur.dir : -1 } };
    });
  }

  /* ---------- AI Optimization actions ---------- */
  aiPost(action, body) { return window.FuseAPI.post('/api/projects/' + this.state.projectId + '/ai/' + action, body || {}); }
  aiReload() {
    const pid = this.state.projectId;
    const k = this.key('ai', pid, this.state.range);
    window.FuseAPI.get('/api/projects/' + pid + '/ai').then(data => {
      if (!this._alive) return;
      this.setState(s => { const cache = Object.assign({}, s.cache); cache[k] = data; return { cache }; });
    }).catch(() => {});
  }
  aiFinishSetup(d) {
    if (this.state.aiWizBusy) return;
    const s = this.state;
    const brand = ((s.aiWizBrand != null ? s.aiWizBrand : d.targets.brand) || '').trim() || d.targets.brand;
    const aliases = (s.aiWizAliases != null ? s.aiWizAliases : d.targets.aliases.join(', ')).split(',').map(x => x.trim()).filter(Boolean);
    const comps = s.aiWizComps || d.targets.competitors;
    const selArr = s.aiWizSel || d.suggestions.slice(0, 6).map(x => x.id);
    const selSet = new Set(selArr);
    const texts = d.suggestions.filter(x => selSet.has(x.id)).map(x => x.text)
      .concat((s.aiWizCustom || '').split('\n').map(x => x.trim()).filter(Boolean));
    this.setState({ aiWizBusy: true });
    this.aiPost('setup', { brand, aliases, competitors: comps, prompts: texts })
      .then(() => {
        if (!this._alive) return;
        this.setState({ aiWizBusy: false, aiWiz: 1, aiWizBrand: null, aiWizAliases: null, aiWizComps: null, aiWizSel: null, aiWizCustom: '' });
        this.aiReload();
        this.notify('AI tracking configured — ' + texts.length + ' prompt' + (texts.length === 1 ? '' : 's') + ' on the weekly schedule');
      })
      .catch(() => { if (this._alive) this.setState({ aiWizBusy: false }); });
  }
  aiSaveTargets(d) {
    const s = this.state;
    const brand = ((s.aiWizBrand != null ? s.aiWizBrand : d.targets.brand) || '').trim() || d.targets.brand;
    const aliases = (s.aiWizAliases != null ? s.aiWizAliases : d.targets.aliases.join(', ')).split(',').map(x => x.trim()).filter(Boolean);
    const comps = s.aiWizComps || d.targets.competitors;
    this.aiPost('targets', { brand, aliases, competitors: comps })
      .then(() => {
        if (!this._alive) return;
        this.setState({ aiTgOpen: false, aiWizBrand: null, aiWizAliases: null, aiWizComps: null, aiWizCompInput: '' });
        this.aiReload();
        this.notify('Tracked targets updated');
      }).catch(() => {});
  }
  aiAddPrompts(texts, listId, after) {
    if (!texts.length) return;
    this.aiPost('prompts', { texts, listId })
      .then(r => {
        if (!this._alive) return;
        this.aiReload();
        this.notify(r.added + ' prompt' + (r.added === 1 ? '' : 's') + ' added — first run on the weekly schedule');
        if (after) after();
      }).catch(() => {});
  }
  aiRun(body) {
    this.aiPost('run', body)
      .then(r => {
        if (!this._alive) return;
        this.aiReload();
        this.notify('Ran ' + r.ran + ' prompt' + (r.ran === 1 ? '' : 's') + ' across LLMs · ' + this.money(r.cost));
      }).catch(() => {});
  }
  aiInspect(question, promptId) {
    question = (question || '').trim();
    if (!question || this.state.aiInspecting) return;
    this.setState({ aiInspecting: true, aiSub: 'inspector' });
    this.aiPost('inspect', { question, promptId })
      .then(e => {
        if (!this._alive) return;
        this.setState({ aiInspecting: false, aiInspEntry: e, aiInspQ: '' });
        this.aiReload();
        this.notify('Inspection saved to History · ' + this.money(e.cost));
      })
      .catch(() => { if (this._alive) this.setState({ aiInspecting: false }); });
  }
  aiExplore() {
    const q = this.state.aiExpQ.trim();
    if (!q || this.state.aiExploring) return;
    this.setState({ aiExploring: true, aiExpSel: [], aiExpAddOpen: false });
    window.FuseAPI.post('/api/prompt-research', { project: this.state.projectId, seeds: q.split(',') })
      .then(r => { if (this._alive) this.setState({ aiExploring: false, aiExp: r }); })
      .catch(() => { if (this._alive) this.setState({ aiExploring: false }); });
  }
  aiListOp(op, id, name, after) {
    this.aiPost('lists', { op, id, name })
      .then(() => { if (!this._alive) return; this.aiReload(); if (after) after(); }).catch(() => {});
  }

  /* ---------- renderVals ---------- */
  renderVals() {
    const s = this.state;
    const tab = s.tab;
    const project = (s.projects.find(p => p.id === s.projectId)) || { domain: 'fusehealth.com', name: 'FuseHealth' };

    /* nav */
    const navBase = { display: 'flex', alignItems: 'center', gap: '12px', padding: '8px 12px', borderRadius: '8px', color: '#475569', marginBottom: '2px', cursor: 'pointer' };
    const navActive = Object.assign({}, navBase, { background: '#eef2ff', color: '#4338ca', fontWeight: 500 });
    const subBase = { display: 'flex', alignItems: 'center', gap: '10px', padding: '7px 10px', borderRadius: '8px', color: '#475569', fontSize: '13px', marginBottom: '1px', cursor: 'pointer' };
    const subActive = Object.assign({}, subBase, { background: '#eef2ff', color: '#4338ca', fontWeight: 500 });
    const mk = k => (tab === k ? navActive : navBase);
    const sub = k => (tab === k ? subActive : subBase);
    const dot = k => ({ width: '8px', height: '8px', borderRadius: '2px', background: tab === k ? '#4f46e5' : '#cbd5e1', flexShrink: 0 });
    const sdot = k => ({ width: '5px', height: '5px', borderRadius: '2px', background: tab === k ? '#4f46e5' : '#cbd5e1', flexShrink: 0 });

    const titles = {
      overview: ['Overview', 'Your traffic, rankings, and what needs attention'],
      seo: ['SEO Performance', 'Opportunities, anomalies, and technical issues'],
      keywords: ['Keyword Research', 'Your organic keyword portfolio — powered by DataForSEO'],
      positioning: ['Position Tracking', 'Weekly SERP snapshots, competitors, and movement'],
      backlinks: ['Backlinks', 'Live and lost links with referring domain quality'],
      offsite: ['Off-site SEO', 'Off-site organic interactions from GA4 — referral, social & video'],
      pages: ['Site Audit', 'Crawl health, indexing, and page speed — merged view'],
      ai: ['AI Optimization', 'Brand visibility across ChatGPT, AI Overviews, Claude, Gemini & Perplexity'],
      ads: ['Paid Overview', 'Google Ads & GA4 — spend, outcomes, and pacing'],
      campaigns: ['Campaigns', 'Budgets, delivery, and results by campaign'],
      terms: ['Search Terms', 'The real queries your ads matched — cut waste, find keywords'],
      attribution: ['Attribution', 'Google Ads conversions vs. GA4 key events, side by side'],
      alerts: ['Alerts', 'Everything that changed and needs a decision'],
      settings: ['Settings', 'Project configuration, connectors, sync schedule, budget'],
    };

    /* range + refresh */
    const rBase = { padding: '6px 12px', color: '#64748b', cursor: 'pointer' };
    const rActive = { padding: '6px 12px', background: '#f1f5f9', color: '#1e293b', fontWeight: 500, cursor: 'pointer' };
    const syncing = s.sync.active && (!s.sync.projectId || s.sync.projectId === s.projectId);
    const activeScope = syncing ? (s.sync.scope || 'all') : null;
    const isPageSyncing = syncing && activeScope && activeScope !== 'all';
    const isAllSyncing = syncing && activeScope === 'all';

    const tabToScope = {
      overview: 'overview',
      seo: 'overview',
      keywords: 'keywords',
      positioning: 'positions',
      backlinks: 'backlinks',
      pages: 'audit',
      ai: 'ai',
      ads: 'ads',
      campaigns: 'ads',
      terms: 'ads'
    };
    const tabToLabel = {
      overview: 'Fetch Overview',
      seo: 'Fetch SEO Data',
      keywords: 'Fetch Keywords',
      positioning: 'Fetch Positions',
      backlinks: 'Fetch Backlinks',
      pages: 'Fetch Site Audit',
      ai: 'Fetch AI Data',
      ads: 'Fetch Ads',
      campaigns: 'Fetch Campaigns',
      terms: 'Fetch Terms'
    };
    const pageScope = tabToScope[tab];

    const data = s.cache[this.key(tab)];
    const alertsData = s.cache[this.key('alerts')];
    const unacked = alertsData ? alertsData.feed.filter(f => !f.acknowledged && f.severity !== 'info').length : 0;

    const h = {
      logout: () => { try { localStorage.clear(); sessionStorage.clear(); } catch (e) {} window.location.href = '/logout/'; },
      navOverview: () => this.go('overview'), navSeo: () => this.go('seo'),
      navKeywords: () => this.go('keywords'), navPositioning: () => this.go('positioning'),
      navBacklinks: () => this.go('backlinks'), navOffsite: () => this.go('offsite'), navPages: () => this.go('pages'), navAi: () => this.go('ai'),
      navAds: () => this.go('ads'), navCampaigns: () => this.go('campaigns'), navTerms: () => this.go('terms'), navAttribution: () => this.go('attribution'),
      navAlerts: () => this.go('alerts'), navSettings: () => { if (this.state.userRole !== 'Analyst') this.go('settings'); else this.notify('Settings require Owner or Admin access.'); },
      goConnections: () => { if (this.state.userRole === 'Analyst') { this.notify('Connecting social platforms requires Owner or Admin access.'); } else { this.setState({ tab: 'settings', settingsSub: 'connections' }); this.pushNav({ tab: 'settings', settingsSub: 'connections' }); } },
      cmpSearch: e => this.setState({ cmpSearch: e.target.value }),
      exportCampaigns: () => { const d = s.cache[this.key(s.tab)]; if (d) this.downloadCsv(project.domain + '-campaigns.csv', [['campaign', 'name'], ['platform', 'platform'], ['type', 'type'], ['status', 'status'], ['budget_daily', 'budget_daily'], ['spend', 'spend'], ['impressions', 'impressions'], ['clicks', 'clicks'], ['ctr', 'ctr'], ['cpc', 'cpc'], ['conversions', 'conversions'], ['cpa', 'cpa'], ['roas', 'roas'], ['lost_is_budget', 'lost_is_budget']], d.campaigns); },
      exportTerms: () => { const d = s.cache[this.key(s.tab)]; if (d) this.downloadCsv(project.domain + '-search-terms.csv', [['term', 'term'], ['matched_keyword', 'matchedKeyword'], ['match_type', 'matchType'], ['campaign', 'campaign'], ['impressions', 'impressions'], ['clicks', 'clicks'], ['cost', 'cost'], ['conversions', 'conversions'], ['status', 'status']], d.searchTerms); },
      setProject: e => this.setProject(e.target.value),
      toggleAddSite: () => this.toggleAddSite(),
      addSiteDomainSet: e => this.setState({ addSiteDomain: e.target.value, addSiteError: null }),
      addSiteNameSet: e => this.setState({ addSiteName: e.target.value }),
      addSiteKeyDown: e => { if (e.key === 'Enter') this.addSiteSubmit(); if (e.key === 'Escape') this.toggleAddSite(); },
      addSiteSubmit: () => this.addSiteSubmit(),
      range7: () => this.setRange('7d'), range30: () => this.setRange('30d'), range90: () => this.setRange('90d'),
      refreshPage: () => { if (pageScope) this.startSync(pageScope); },
      refreshAll: () => this.startSync('all'),
      retry: () => this.fetchTab(tab, s.projectId, s.range, true),
      explorerInput: e => this.setState({ explorerQ: e.target.value }),
      explorerKey: e => { if (e.key === 'Enter') this.runResearch(); },
      explorerLocSet: e => this.setState({ explorerLoc: e.target.value }),
      runResearch: () => this.runResearch(),
      clearResearch: () => { this.pushNav({ research: null }); this.setState({ research: null, selectedKws: [], sendOpen: false, exportOpen: false, sendSub: null, resGroup: null, resDrawer: null, resOpenFilter: null }); },
      histBack: () => this.histBack(),
      histFwd: () => this.histFwd(),
      toggleLists: () => this.setState(st => ({ showLists: !st.showLists })),
      setMatch: mt => this.setState({ matchType: mt, selectedKws: [], sendOpen: false, exportOpen: false, sendSub: null, resOpenFilter: null }),
      rfVol: () => this.rfToggle('vol'),
      rfKd: () => this.rfToggle('kd'),
      rfIntent: () => this.rfToggle('intent'),
      rfIncl: () => this.rfToggle('incl'),
      rfExcl: () => this.rfToggle('excl'),
      rfInclSet: e => this.setState({ resIncl: e.target.value }),
      rfExclSet: e => this.setState({ resExcl: e.target.value }),
      rfKey: e => { if (e.key === 'Enter') this.setState({ resOpenFilter: null }); },
      rfApply: () => this.setState({ resOpenFilter: null }),
      rfReset: () => this.setState({ resVolMin: 0, resKdMin: 0, resKdMax: 100, resIntents: [], resIncl: '', resExcl: '', resOpenFilter: null, resGroup: null }),
      rgByNumber: () => this.setState({ resGroupMode: 'number' }),
      rgByVolume: () => this.setState({ resGroupMode: 'volume' }),
      rgAll: () => this.setState({ resGroup: null }),
      rdClose: () => this.setState({ resDrawer: null }),
      toggleRow: kw => this.setState(st => ({ selectedKws: st.selectedKws.includes(kw) ? st.selectedKws.filter(k => k !== kw) : st.selectedKws.concat([kw]) })),
      toggleAll: () => {
        const vis = this.matchRows().map(r => r.kw);
        const allOn = vis.length > 0 && vis.every(k => s.selectedKws.includes(k));
        this.setState({ selectedKws: allOn ? [] : vis });
      },
      clearSelection: () => this.setState({ selectedKws: [], sendOpen: false, sendSub: null }),
      toggleSend: () => this.setState(st => ({ sendOpen: !st.sendOpen, exportOpen: false, sendSub: st.sendOpen ? null : st.sendSub })),
      toggleExport: () => this.setState(st => ({ exportOpen: !st.exportOpen, sendOpen: false })),
      sendSubPt: () => this.setState(st => ({ sendSub: st.sendSub === 'pt' ? null : 'pt' })),
      sendSubList: () => this.setState(st => ({ sendSub: st.sendSub === 'list' ? null : 'list' })),
      newListInput: e => this.setState({ newListName: e.target.value }),
      newListKey: e => { if (e.key === 'Enter') this.createListWith(this.state.newListName, this.selectedRows()); },
      createList: () => this.createListWith(this.state.newListName, this.selectedRows()),
      exportCsv: () => this.exportRows(s.selectedKws.length ? this.selectedRows() : this.matchRows(), 'csv'),
      exportXls: () => this.exportRows(s.selectedKws.length ? this.selectedRows() : this.matchRows(), 'xls'),
      credGsc: e => this.setState({ creds: Object.assign({}, s.creds, { gsc: e.target.value }) }),
      credGa4: e => this.setState({ creds: Object.assign({}, s.creds, { ga4: e.target.value }) }),
      saveCreds: () => this.saveCreds(),
      prefEmail: () => this.togglePref('email_alerts'),
      prefDigest: () => this.togglePref('weekly_digest'),
      syncAudit: () => this.startSync('audit'),
      syncAi: () => this.startSync('ai'),
      copyKws: () => this.copySelectedKws(),
      copySummary: () => this.copySummary(),
      ackAll: () => this.ackAllAlerts(),
      exportTopPages: () => { const d = s.cache[this.key('overview')]; if (d) this.downloadCsv(project.domain + '-top-pages.csv', [['page', 'url'], ['clicks', 'clicks'], ['impressions', 'impressions'], ['ctr', 'ctr']], d.topPages); },
      exportKeywords: () => { const d = s.cache[this.key('keywords')]; if (d) this.downloadCsv(project.domain + '-keywords.csv', [['keyword', 'kw'], ['intent', 'intent'], ['position', 'pos'], ['volume', 'volume'], ['kd', 'kd'], ['cpc', 'cpc'], ['clicks', 'clicks'], ['url', 'url']], d.keywords); },
      exportBacklinks: () => { const d = s.cache[this.key('backlinks')]; if (d) this.downloadCsv(project.domain + '-backlinks.csv', [['domain', 'domain'], ['anchor', 'anchor'], ['type', 'type'], ['status', 'status'], ['rank', 'rank'], ['first_seen', 'firstSeen'], ['target', 'target']], d.links); },
      exportReferrers: () => { const d = s.cache[this.key('offsite')]; if (d) this.downloadCsv(project.domain + '-referring-domains.csv', [['domain', 'domain'], ['domain_rank', 'rank'], ['sessions', 'sessions'], ['engaged_sessions', 'engagedSessions'], ['engagement_rate', 'engagedRate'], ['key_events', 'keyEvents'], ['revenue', 'revenue'], ['tracked_as_backlink', 'tracked']], d.referrers); },
      exportSocial: () => { const d = s.cache[this.key('offsite')]; if (d) this.downloadCsv(project.domain + '-off-site-social.csv', [['platform', 'platform'], ['source', 'source'], ['channel', 'channel'], ['impressions', 'impressions'], ['sessions', 'sessions'], ['engagement_rate', 'engagedRate'], ['key_events', 'keyEvents'], ['revenue', 'revenue']], d.social); },
      exportPages: () => { const d = s.cache[this.key('pages')]; if (d) this.downloadCsv(project.domain + '-crawled-pages.csv', [['url', 'url'], ['score', 'score'], ['status', 'statusCode'], ['errors', 'errors'], ['warnings', 'warnings'], ['notices', 'notices'], ['depth', 'depth'], ['in_links', 'inLinks'], ['load_ms', 'loadTimeMs']], d.crawledPages); },
      auGoIssues: () => { this.setState({ auSub: 'issues', auSev: 'all', auCat: 'all' }); this.pushNav({ auSub: 'issues' }); },
      auSearch: e => this.setState({ auSearch: e.target.value }),
      auPgSearch: e => this.setState({ auPgSearch: e.target.value }),
      auViewTable: () => this.setState({ auView: 'table' }),
      auViewTree: () => this.setState({ auView: 'tree' }),
      auCmpA: e => this.setState({ auCmpA: parseInt(e.target.value, 10) }),
      auCmpB: e => this.setState({ auCmpB: parseInt(e.target.value, 10) }),
      crawlMax: e => this.editCrawl({ maxPages: parseInt(e.target.value, 10) }),
      crawlFreq: e => this.editCrawl({ frequency: e.target.value }),
      crawlExcl: e => this.editCrawl({ excludedPaths: e.target.value }),
      crawlJs: () => this.editCrawl(null, 'jsRendering'),
      crawlRobots: () => this.editCrawl(null, 'respectRobots'),
      saveCrawl: () => this.saveCrawl(),
      auCloseDrawer: () => this.setState({ auPage: null }),
      /* ----- extended settings handlers ----- */
      setSub: sub => () => this.setSettingsSub(sub),
      wsName: e => this.editWs({ name: e.target.value }),
      wsOwner: e => this.editWs({ owner_email: e.target.value }),
      wsTz: e => this.editWs({ timezone: e.target.value }),
      wsWeek: e => this.editWs({ week_start: e.target.value }),
      saveWs: () => this.saveWs(),
      transferOwner: () => this.notify('Ownership transfer requires email confirmation'),
      deleteWorkspace: () => this.notify('Type the workspace name to confirm deletion'),
      inviteEmail: e => this.setState({ inviteEmail: e.target.value }),
      inviteUsername: e => this.setState({ inviteUsername: e.target.value }),
      invitePassword: e => this.setState({ invitePassword: e.target.value }),
      inviteRole: e => this.setState({ inviteRole: e.target.value }),
      createUser: () => this.createUser(),
      syncCfgSet: mod => e => this.editSyncCfg(mod, e.target.value),
      capSet: e => this.setBudgetCap(e.target.value),
      enforceToggle: () => this.toggleEnforce(),
      notifRecipients: e => this.editNotif({ recipients: e.target.value }),
      notifSlack: e => this.editNotif({ slack_webhook: e.target.value }),
      notifDigestDay: e => this.editNotif({ digest_day: e.target.value }),
      notifQuietStart: e => this.editNotif({ quiet_start: e.target.value }),
      notifQuietEnd: e => this.editNotif({ quiet_end: e.target.value }),
      notifEmail: () => this.toggleNotif('email_enabled'),
      notifWeekly: () => this.toggleNotif('weekly_digest'),
      notifSlackOn: () => this.toggleNotif('slack_enabled'),
      saveNotif: () => this.saveNotif(),
      aiProvider: e => this.editAi({ provider: e.target.value }),
      aiModel: e => this.editAi({ model: e.target.value }),
      aiTone: e => this.editAi({ tone: e.target.value }),
      aiCadence: e => this.editAi({ cadence: e.target.value }),
      aiCap: e => this.editAi({ monthly_cap: Math.max(0, parseInt(e.target.value, 10) || 0) }),
      aiVoice: e => this.editAi({ brand_voice: e.target.value }),
      saveAi: () => this.saveAi(),
      dataFormat: e => this.editData({ export_format: e.target.value }),
      dataRetention: e => this.editData({ retention: e.target.value }),
      dataTz: e => this.editData({ report_timezone: e.target.value }),
      dataNum: e => this.editData({ number_format: e.target.value }),
      saveData: () => this.saveData(),
      downloadAll: () => this.notify('Preparing full data export — you\u2019ll get an email link'),
      gdprDelete: () => this.notify('Data-deletion request queued (30-day grace period)'),
      twofaToggle: () => this.toggle2fa(),
      ssoToggle: () => this.toggleSso(),
      tokenName: e => this.setState({ newTokenName: e.target.value }),
      createToken: () => this.createToken(),
      blGoAnchors: () => { this.setState({ blTab: 'anchors' }); this.pushNav({ blTab: 'anchors' }); },
      blGoRefDomains: () => { this.setState({ blTab: 'refdomains' }); this.pushNav({ blTab: 'refdomains' }); },
      blToggleGap: () => this.setState(st => ({ gapOnly: !st.gapOnly })),
      setInviteModeEmail: () => this.setInviteMode('email'),
      setInviteModeDirect: () => this.setInviteMode('direct'),
      sendInvite: () => this.sendInvite(),
      acceptUsernameInput: e => this.setState({ acceptUsername: e.target.value }),
      acceptPasswordInput: e => this.setState({ acceptPassword: e.target.value }),
      submitAcceptInvite: () => this.submitAcceptInvite(),
      cpwOldFn: e => this.setState({ cpwOld: e.target.value }),
      cpwNewFn: e => this.setState({ cpwNew: e.target.value }),
      cpwNew2Fn: e => this.setState({ cpwNew2: e.target.value }),
      cpwSave: () => this.changePassword()
    };

    const uCfg = (window.FuseAPI && window.FuseAPI.config && window.FuseAPI.config.user) || { username: 'founder', initials: 'FO', role: 'Internal' };
    const canManageSettings = uCfg.role !== 'Analyst';
    const vals = {
      cpwOld: s.cpwOld, cpwNew: s.cpwNew, cpwNew2: s.cpwNew2, cpwErr: s.cpwErr, cpwMsg: s.cpwMsg, cpwBusy: s.cpwBusy,
      acceptInvite: s.acceptInviteToken ? {
        token: s.acceptInviteToken,
        email: s.acceptEmail || 'Loading...',
        role: s.acceptRole || '',
        invitedBy: s.acceptInvitedBy || 'Owner',
        username: s.acceptUsername || '',
        password: s.acceptPassword || '',
        error: s.acceptError || null,
        success: s.acceptSuccess || null
      } : null,
      userInitials: uCfg.initials, userName: uCfg.username, userRole: uCfg.role, canManageSettings,
      brandName: project.name || 'FuseHealth',
      projectDomain: project.domain || '',
      h,
      navStyle: { overview: mk('overview'), seo: mk('seo'), keywords: sub('keywords'), positioning: sub('positioning'), backlinks: sub('backlinks'), offsite: sub('offsite'), pages: sub('pages'), ai: sub('ai'), ads: mk('ads'), campaigns: sub('campaigns'), terms: sub('terms'), attribution: sub('attribution'), alerts: mk('alerts'), settings: mk('settings') },
      dotStyle: { overview: dot('overview'), seo: dot('seo'), ads: dot('ads'), campaigns: sdot('campaigns'), terms: sdot('terms'), attribution: sdot('attribution'), alerts: dot('alerts'), settings: dot('settings'), keywords: sdot('keywords'), positioning: sdot('positioning'), backlinks: sdot('backlinks'), offsite: sdot('offsite'), pages: sdot('pages'), ai: sdot('ai') },
      seoOpen: s.seoOpen, adsOpen: s.adsOpen,
      title: titles[tab][0], subtitle: titles[tab][1] + ' · ' + project.domain,
      projects: s.projects.length ? s.projects : [{ id: s.projectId, domain: project.domain }],
      projectId: s.projectId, projectDomain: project.domain,
      addSiteOpen: s.addSiteOpen, addSiteDomain: s.addSiteDomain, addSiteName: s.addSiteName, addSiteError: s.addSiteError,
      rangeStyle: { d7: s.range === '7d' ? rActive : rBase, d30: s.range === '30d' ? rActive : rBase, d90: s.range === '90d' ? rActive : rBase },
      hasPageRefresh: !!pageScope,
      refreshPageLabel: isPageSyncing ? 'Syncing…' : (tabToLabel[tab] || 'Fetch page'),
      refreshPageBtnStyle: { display: 'inline-flex', alignItems: 'center', gap: '8px', borderRadius: '8px', background: isPageSyncing ? '#6ee7b7' : '#10b981', color: 'white', fontSize: '14px', fontWeight: 500, padding: '8px 16px', boxShadow: '0 1px 2px rgba(0,0,0,0.05)', cursor: isPageSyncing ? 'default' : 'pointer' },
      refreshPageIconStyle: isPageSyncing ? { animation: 'fuseSpin 1s linear infinite' } : {},
      refreshLabel: isAllSyncing ? 'Syncing all…' : 'Refresh all',
      refreshBtnStyle: { display: 'inline-flex', alignItems: 'center', gap: '8px', borderRadius: '8px', background: isAllSyncing ? '#818cf8' : '#4f46e5', color: 'white', fontSize: '14px', fontWeight: 500, padding: '8px 16px', boxShadow: '0 1px 2px rgba(0,0,0,0.05)', cursor: isAllSyncing ? 'default' : 'pointer' },
      refreshIconStyle: isAllSyncing ? { animation: 'fuseSpin 1s linear infinite' } : {},
      freshness: s.freshness,
      syncing, syncScopeLabel: activeScope === 'all' ? 'all modules' : (tabToLabel[tab] || activeScope || '').replace('Fetch ', ''), syncStep: s.sync.step, syncPct: Math.round(s.sync.progress * 100),
      syncPctText: Math.round(s.sync.progress * 100) + '%', syncCostText: this.money(s.sync.cost),
      hasError: !!s.error && !s.loading, errorText: s.error || '',
      loading: s.loading && !s.error,
      hasUnacked: unacked > 0, unackedCount: unacked,
      explorerQ: s.explorerQ, explorerLoc: s.explorerLoc,
      researchLabel: s.researching ? 'Searching…' : 'Search',
      hasResearch: false, resRows: [], resMeta: '', resDrawerOpen: false, rd: {}, rf: { volOptions: [], kdOptions: [], intentOptions: [] }, rg: { groups: [] },
      resAlgoEp: '', resAlgoDesc: '', resAlgoCost: '',
      credsSaveLabel: s.credsSaved ? 'Saved ✓' : 'Save Credentials',
      showOverview: false, showSeo: false, showKeywords: false, showPositioning: false,
      showBacklinks: false, showOffsite: false, showPages: false, showAi: false, showAds: false, showCampaigns: false, showTerms: false, showAttribution: false, showAlerts: false, showSettings: false,
      ov: {}, seo: {}, kw: {}, pt: {}, bl: {}, off: {}, au: {}, aiv: {}, ads: {}, cmp: {}, trm: {}, att: {}, adsSync: {}, al: {}, st: {},
      sortCmp: { spend: this.mkSortHandler('cmpSort', 'spend'), clicks: this.mkSortHandler('cmpSort', 'clicks'), ctr: this.mkSortHandler('cmpSort', 'ctr'), cpc: this.mkSortHandler('cmpSort', 'cpc'), conversions: this.mkSortHandler('cmpSort', 'conversions'), cpa: this.mkSortHandler('cmpSort', 'cpa'), roas: this.mkSortHandler('cmpSort', 'roas') },
      cmpArrow: { spend: this.arrow(s.cmpSort, 'spend'), clicks: this.arrow(s.cmpSort, 'clicks'), ctr: this.arrow(s.cmpSort, 'ctr'), cpc: this.arrow(s.cmpSort, 'cpc'), conversions: this.arrow(s.cmpSort, 'conversions'), cpa: this.arrow(s.cmpSort, 'cpa'), roas: this.arrow(s.cmpSort, 'roas') },
      sortTrm: { impressions: this.mkSortHandler('trmSort', 'impressions'), clicks: this.mkSortHandler('trmSort', 'clicks'), cost: this.mkSortHandler('trmSort', 'cost'), conversions: this.mkSortHandler('trmSort', 'conversions'), cpa: this.mkSortHandler('trmSort', 'cpa') },
      trmArrow: { impressions: this.arrow(s.trmSort, 'impressions'), clicks: this.arrow(s.trmSort, 'clicks'), cost: this.arrow(s.trmSort, 'cost'), conversions: this.arrow(s.trmSort, 'conversions'), cpa: this.arrow(s.trmSort, 'cpa') },
      sortKw: { pos: this.mkSortHandler('kwSort', 'pos'), volume: this.mkSortHandler('kwSort', 'volume'), kd: this.mkSortHandler('kwSort', 'kd'), clicks: this.mkSortHandler('kwSort', 'clicks') },
      kwArrow: { pos: this.arrow(s.kwSort, 'pos'), volume: this.arrow(s.kwSort, 'volume'), kd: this.arrow(s.kwSort, 'kd'), clicks: this.arrow(s.kwSort, 'clicks') },
      sortBl: { rank: this.mkSortHandler('blSort', 'rank'), firstSeen: this.mkSortHandler('blSort', 'firstSeen') },
      blArrow: { rank: this.arrow(s.blSort, 'rank'), firstSeen: this.arrow(s.blSort, 'firstSeen') },
      sortPg: { clicks: this.mkSortHandler('pgSort', 'clicks'), speed: this.mkSortHandler('pgSort', 'speed') },
      pgArrow: { clicks: this.arrow(s.pgSort, 'clicks'), speed: this.arrow(s.pgSort, 'speed') },
      pd: { show: false },
      auSort: { score: this.mkSortHandler('auPgSort', 'score'), issues: this.mkSortHandler('auPgSort', 'issues'), depth: this.mkSortHandler('auPgSort', 'depth'), inLinks: this.mkSortHandler('auPgSort', 'inLinks'), loadTimeMs: this.mkSortHandler('auPgSort', 'loadTimeMs') },
      auArrow: { score: this.arrow(s.auPgSort, 'score'), issues: this.arrow(s.auPgSort, 'issues'), depth: this.arrow(s.auPgSort, 'depth'), inLinks: this.arrow(s.auPgSort, 'inLinks'), loadTimeMs: this.arrow(s.auPgSort, 'loadTimeMs') },
      ptView: s.ptView || 'list', ptSearch: s.ptSearch || '', ptFilter: s.ptFilter || 'all', ptWizOpen: !!s.ptWizOpen, ptWizStep: s.ptWizStep || 1, ptWizDomain: s.ptWizDomain || '', ptWizName: s.ptWizName || '', ptWizEngine: s.ptWizEngine || 'Google', ptWizLang: s.ptWizLang || 'English', ptWizLoc: s.ptWizLoc || 'United States', ptWizDevice: s.ptWizDevice || 'Desktop', ptWizKwMode: s.ptWizKwMode || 'paste', ptWizKwText: s.ptWizKwText || '', ptWizListId: s.ptWizListId || null, ptWizComps: s.ptWizComps || [], ptWizCompInput: s.ptWizCompInput || '', ptWizBusy: !!s.ptWizBusy,
      toast: s.toast
    };

    /* keyword tool: back/forward + lists (available regardless of search state) */
    {
      const backOn = !!(this._hist && this._histIdx > 0);
      const fwdOn = !!(this._hist && this._histIdx < this._hist.length - 1);
      vals.backCursor = backOn ? 'pointer' : 'default';
      vals.backColor = backOn ? '#475569' : '#cbd5e1';
      vals.fwdCursor = fwdOn ? 'pointer' : 'default';
      vals.fwdColor = fwdOn ? '#475569' : '#cbd5e1';
      vals.listsCount = s.kwLists.length;
      vals.showLists = s.showLists;
      vals.noLists = s.kwLists.length === 0;
      vals.allLists = s.kwLists.map(l => ({
        name: l.name, count: l.keywords.length, empty: l.keywords.length === 0,
        onDelete: () => this.deleteList(l.id),
        onSendPt: () => this.sendListToTracking(l.id),
        keywords: l.keywords.map(kw => ({ kw, onRemove: () => this.removeKwFromList(l.id, kw) }))
      }));
    }

    /* research results (visible on keywords tab regardless of loading) */
    if (s.research && s.research.rows) {
      vals.hasResearch = true;
      const visRows = this.matchRows();
      const selSet = new Set(s.selectedKws);
      const selCount = visRows.filter(r => selSet.has(r.kw)).length;

      // match-type tabs
      const tabDefs = [['all', 'All'], ['broad', 'Broad Match'], ['phrase', 'Phrase Match'], ['exact', 'Exact Match'], ['questions', 'Questions'], ['related', 'Related']];
      const tabBase = { padding: '6px 11px', fontSize: '13px', borderRadius: '7px', cursor: 'pointer', border: '1px solid transparent', color: '#64748b', fontWeight: 400 };
      const tabOn = { padding: '6px 11px', fontSize: '13px', borderRadius: '7px', cursor: 'pointer', border: '1px solid #c7d2fe', background: '#eef2ff', color: '#4338ca', fontWeight: 600 };
      vals.matchTabs = tabDefs.map(d => ({ label: d[1], onClick: () => vals.h.setMatch(d[0]), style: s.matchType === d[0] ? tabOn : tabBase }));

      // DataForSEO Labs expansion algorithm per match tab
      const ALGO = {
        all: { ep: 'keyword_ideas + keyword_suggestions', desc: 'Deduped union of all expansion algorithms off your seed' },
        broad: { ep: 'dataforseo_labs/google/keyword_ideas', desc: 'Category-relevance search \u2014 widest net, includes terms that don\u2019t contain your seed' },
        phrase: { ep: 'dataforseo_labs/google/keyword_suggestions', desc: 'Full-text long-tail search \u2014 every result contains your seed phrase' },
        exact: { ep: 'keywords_data/google_ads/search_volume', desc: 'Metrics for the literal seed phrase only' },
        questions: { ep: 'keyword_suggestions + filter', desc: 'Long-tail suggestions filtered to question prefixes (how / what / is / can\u2026)' },
        related: { ep: 'dataforseo_labs/google/related_keywords', desc: 'Semantic neighbors from Google\u2019s \u201csearches related to\u201d graph' }
      };
      const algo = ALGO[s.matchType] || ALGO.broad;
      vals.resAlgoEp = algo.ep;
      vals.resAlgoDesc = algo.desc;
      vals.resAlgoCost = 'pull est. $' + (0.012 + s.research.rows.length * 0.00012).toFixed(3) + ' \u00b7 filters run on the cached set ($0)';

      // filter chips
      const chip = on => ({ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '6px 11px', fontSize: '12.5px', border: '1px solid ' + (on ? '#c7d2fe' : '#e2e8f0'), borderRadius: '7px', color: on ? '#4338ca' : '#64748b', cursor: 'pointer', background: 'white' });
      const opt = on => ({ padding: '8px 10px', borderRadius: '6px', fontSize: '13px', cursor: 'pointer', color: on ? '#4338ca' : '#334155', fontWeight: on ? 600 : 400, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' });
      const volDefs = [['Any', 0], ['101+', 101], ['1,001+', 1001], ['10,001+', 10001]];
      const kdDefs = [['Any', 0, 100, '#cbd5e1'], ['Very easy\u2013Easy (0\u201329)', 0, 29, '#22c55e'], ['Possible (30\u201349)', 30, 49, '#f59e0b'], ['Difficult (50\u201369)', 50, 69, '#f97316'], ['Hard+ (70\u2013100)', 70, 100, '#ef4444']];
      const filtersOn = s.resVolMin > 0 || s.resKdMin > 0 || s.resKdMax < 100 || s.resIntents.length > 0 || !!s.resIncl.trim() || !!s.resExcl.trim() || !!s.resGroup;
      vals.rf = {
        volOpen: s.resOpenFilter === 'vol', kdOpen: s.resOpenFilter === 'kd', intentOpen: s.resOpenFilter === 'intent', inclOpen: s.resOpenFilter === 'incl', exclOpen: s.resOpenFilter === 'excl',
        volChip: chip(s.resVolMin > 0), kdChip: chip(s.resKdMin > 0 || s.resKdMax < 100), intentChip: chip(s.resIntents.length > 0), inclChip: chip(!!s.resIncl.trim()), exclChip: chip(!!s.resExcl.trim()),
        incl: s.resIncl, excl: s.resExcl, anyOn: filtersOn,
        volOptions: volDefs.map(d => ({ label: d[0], check: s.resVolMin === d[1] ? '\u2713' : '', style: opt(s.resVolMin === d[1]), onPick: () => this.setState({ resVolMin: d[1], resOpenFilter: null }) })),
        kdOptions: kdDefs.map(d => ({ label: d[0], check: s.resKdMin === d[1] && s.resKdMax === d[2] ? '\u2713' : '', dotStyle: { width: '8px', height: '8px', borderRadius: '50%', background: d[3], flexShrink: 0 }, style: opt(s.resKdMin === d[1] && s.resKdMax === d[2]), onPick: () => this.setState({ resKdMin: d[1], resKdMax: d[2], resOpenFilter: null }) })),
        intentOptions: ['informational', 'navigational', 'commercial', 'transactional'].map(k => { const iv0 = this.intentView(k); const on = s.resIntents.includes(k); return { label: iv0.label, check: on ? '\u2713' : '', badgeStyle: iv0.style, style: opt(on), onPick: () => this.setState(st => ({ resIntents: st.resIntents.includes(k) ? st.resIntents.filter(x => x !== k) : st.resIntents.concat([k]) })) }; })
      };

      // grouping sidebar
      const segBtn = on => ({ flex: 1, textAlign: 'center', padding: '6px', fontSize: '12px', fontWeight: 500, borderRadius: '6px', cursor: 'pointer', background: on ? '#eef2ff' : 'transparent', color: on ? '#4338ca' : '#64748b' });
      const grpRow = on => ({ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '9px 14px', fontSize: '13px', cursor: 'pointer', borderBottom: '1px solid #f8fafc', background: on ? '#eef2ff' : 'white', color: on ? '#4338ca' : '#334155' });
      vals.rg = {
        numStyle: segBtn(s.resGroupMode === 'number'), volStyle: segBtn(s.resGroupMode === 'volume'),
        allStyle: grpRow(!s.resGroup), total: this.fmt(this.matchRows(true).length),
        groups: this.resGroups().map(g => ({ word: g.word, metric: s.resGroupMode === 'volume' ? this.fmt(g.volume) : this.fmt(g.count), style: grpRow(s.resGroup === g.word), onSelect: () => this.setState(st => ({ resGroup: st.resGroup === g.word ? null : g.word, selectedKws: [] })) }))
      };

      // keyword overview drawer
      const drRow = s.resDrawer ? s.research.rows.find(r => r.kw === s.resDrawer) : null;
      vals.resDrawerOpen = !!drRow;
      if (drRow) {
        const div = this.intentView(drRow.intent);
        const kdc = this.kdColor(drRow.kd);
        vals.rd = {
          kw: drRow.kw, loc: s.research.location,
          serpHref: 'https://www.google.com/search?q=' + encodeURIComponent(drRow.kw),
          volFmt: this.fmt(drRow.volume),
          kd: drRow.kd, kdLabel: drRow.kd >= 85 ? 'Very hard' : drRow.kd >= 70 ? 'Hard' : drRow.kd >= 50 ? 'Difficult' : drRow.kd >= 30 ? 'Possible' : drRow.kd >= 15 ? 'Easy' : 'Very easy',
          kdLabelStyle: { fontSize: '12px', fontWeight: 500, color: kdc, marginTop: '2px' },
          cpcFmt: this.money(drRow.cpc),
          intentLabel: div.label, intentStyle: div.style,
          spark: this.spark(drRow.monthly, 380, 64),
          feats: (drRow.serpFeatures || []).map(f => ({ label: f.replace(/_/g, ' ') })),
          trackLabel: drRow.tracked ? 'Already tracked \u2014 re-sync metrics' : 'Track in Position Tracking',
          onTrack: () => { this.sendKwsToTracking(s.projectId, [drRow]); this.setState({ resDrawer: null }); }
        };
      }

      vals.resMeta = visRows.length + ' keyword ideas · ' + s.research.location + ' · est. cost ' + this.money(s.research.cost);
      vals.anySelected = selCount > 0;
      vals.noneSelected = selCount === 0;
      vals.selectedCount = selCount;
      vals.noRows = visRows.length === 0;
      vals.toolbarBg = selCount > 0 ? '#f5f7ff' : '#f8fafc';
      vals.exportScopeLabel = selCount > 0 ? '(' + selCount + ')' : '(all ' + visRows.length + ')';

      const allOn = visRows.length > 0 && visRows.every(r => selSet.has(r.kw));
      vals.allChecked = allOn;
      vals.allCheckStyle = { width: '15px', height: '15px', borderRadius: '4px', border: '1.5px solid ' + (allOn ? '#4f46e5' : '#cbd5e1'), background: allOn ? '#4f46e5' : 'white', display: 'flex', alignItems: 'center', justifyContent: 'center' };

      // send menu
      vals.sendOpen = s.sendOpen;
      vals.exportOpen = s.exportOpen;
      vals.sendSubPt = s.sendSub === 'pt';
      vals.sendSubList = s.sendSub === 'list';
      const subItem = on => ({ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '9px 8px', borderRadius: '7px', cursor: 'pointer', background: on ? '#f8fafc' : 'transparent' });
      vals.ptItemStyle = subItem(vals.sendSubPt);
      vals.listItemStyle = subItem(vals.sendSubList);
      const selRows = () => this.selectedRows();
      vals.sendProjects = vals.projects.map(p => ({ domain: p.domain, onSend: () => this.sendKwsToTracking(p.id, selRows()) }));
      vals.sendLists = s.kwLists.map(l => ({ name: l.name, count: l.keywords.length, onAdd: () => this.addKwsToList(l.id, selRows()) }));
      vals.noLists = s.kwLists.length === 0;
      vals.newListName = s.newListName;

      vals.resRows = visRows.map(r => {
        const iv = this.intentView(r.intent);
        const on = selSet.has(r.kw);
        return {
          kw: r.kw, volFmt: this.fmt(r.volume), kd: r.kd, tracked: r.tracked,
          spark: this.spark(r.monthly, 46, 16),
          sparkColor: r.monthly && r.monthly[11] >= r.monthly[0] ? '#22c55e' : '#ef4444',
          sf: (r.serpFeatures || []).length || '\u2014',
          onOpen: () => this.setState({ resDrawer: r.kw }),
          kdStyle: { fontSize: '12px', fontWeight: 600, color: this.kdColor(r.kd) },
          cpcFmt: this.money(r.cpc),
          intentLabel: iv.label, intentStyle: iv.style,
          checked: on,
          rowBg: on ? '#f5f7ff' : 'white',
          checkStyle: { width: '15px', height: '15px', borderRadius: '4px', border: '1.5px solid ' + (on ? '#4f46e5' : '#cbd5e1'), background: on ? '#4f46e5' : 'white', display: 'flex', alignItems: 'center', justifyContent: 'center' },
          onToggle: () => vals.h.toggleRow(r.kw)
        };
      });
    }

    if (s.loading || s.error || !data) return vals;

        /* ============ OVERVIEW ============ */
    if (tab === 'overview') {
      vals.showOverview = true;
      const pillarDisp = (p) => {
        if (p.state === 'setup') return 'Set up';
        if (p.value == null) return '—';
        if (p.valueKind === 'pos') return '#' + p.value;
        if (p.valueKind === 'roas') return p.value + '×';
        if (p.valueKind === 'pct') return p.value + '%';
        if (p.valueKind === 'score') return String(p.value);
        return this.fmt(p.value);
      };
      const sevColor = { high: '#dc2626', medium: '#d97706', info: '#94a3b8' };
      const modColor = { SEO: '#4f46e5', Positions: '#0891b2', Backlinks: '#7c3aed', 'Site Audit': '#dc2626', Ads: '#059669', System: '#64748b', General: '#64748b' };
      const toneDot = { ok: '#10b981', warn: '#f59e0b', bad: '#ef4444', setup: '#a855f7' };
      const toneStat = { ok: '#0f172a', warn: '#b45309', bad: '#b91c1c', setup: '#7c3aed' };
      vals.ov = {
        pillars: (data.pillars || []).map(p => {
          const setup = p.state === 'setup';
          const good = (p.delta || 0) >= 0;
          return {
            label: p.label, value: pillarDisp(p), sub: p.sub || '', hasSub: !!p.sub,
            hasDelta: p.delta != null,
            deltaFmt: p.delta == null ? '' : (p.delta >= 0 ? '▲ ' : '▼ ') + Math.abs(p.delta) + (p.deltaUnit === '%' ? '%' : ''),
            chipStyle: { fontSize: '11px', fontWeight: 600, padding: '2px 6px', borderRadius: '4px', color: good ? '#059669' : '#e11d48', background: good ? '#ecfdf5' : '#fff1f2' },
            onClick: () => this.go(p.target),
            cardStyle: { borderRadius: '12px', background: 'white', border: '1px solid #e2e8f0', padding: '16px 18px', boxShadow: '0 1px 2px rgba(0,0,0,0.05)', cursor: 'pointer', transition: 'all .16s' },
            valueStyle: setup ? { fontSize: '16px', fontWeight: 600, color: '#6366f1' } : { fontSize: '24px', fontWeight: 600, color: '#0f172a', lineHeight: 1 },
            arrowStyle: { color: '#cbd5e1', fontSize: '14px', lineHeight: 1 }
          };
        }),
        priority: (data.priority || []).map((a, i) => ({
          title: a.title, detail: a.detail, tsFmt: a.ts, moduleLabel: a.module.label,
          moduleStyle: { fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em', color: modColor[a.module.label] || '#64748b', background: (modColor[a.module.label] || '#64748b') + '14', padding: '2px 7px', borderRadius: '4px' },
          sevDot: { width: '8px', height: '8px', borderRadius: '9999px', background: sevColor[a.severity] || '#94a3b8', marginTop: '6px', flexShrink: 0 },
          rowStyle: { display: 'flex', gap: '12px', alignItems: 'flex-start', padding: '14px 20px', cursor: 'pointer', borderTop: i === 0 ? 'none' : '1px solid #f1f5f9' },
          onClick: () => this.go(a.module.target)
        })),
        priorityEmpty: (data.priority || []).length === 0,
        modules: (data.modules || []).map(m => ({
          label: m.label, stat: m.stat, sub: m.sub,
          dotStyle: { width: '8px', height: '8px', borderRadius: '9999px', background: toneDot[m.tone] || '#10b981', flexShrink: 0 },
          statStyle: { fontSize: '18px', fontWeight: 600, color: toneStat[m.tone] || '#0f172a', marginTop: '8px', lineHeight: 1.1 },
          cardStyle: { borderRadius: '12px', background: 'white', border: '1px solid #e2e8f0', padding: '14px 16px', boxShadow: '0 1px 2px rgba(0,0,0,0.05)', cursor: 'pointer', transition: 'all .16s' },
          onClick: () => this.go(m.target)
        })),
        clickPts: this.linePts(data.trend, 'clicks', 600, 220),
        imprPts: this.linePts(data.trend, 'impressions', 600, 220),
        maxClicks: this.fmt(Math.max.apply(null, data.trend.map(d => d.clicks))),
        dateFrom: data.trend[0] ? data.trend[0].date : '', dateTo: data.trend.length ? data.trend[data.trend.length - 1].date : '',
        rangeLabel: s.range === '7d' ? 'last 7 days' : s.range === '90d' ? 'last 90 days' : 'last 30 days',
        summary: [
          { title: 'Wins', items: data.summary.wins, kind: 'win' },
          { title: 'Critical', items: data.summary.critical, kind: 'critical' },
          { title: 'Watch', items: data.summary.watch, kind: 'watch' }
        ].filter(x => x.items && x.items.length).map(x => {
          const m = x.kind === 'win' ? ['#d1fae5', 'rgba(236,253,245,0.5)', '#047857', '#34d399'] : x.kind === 'critical' ? ['#fee2e2', 'rgba(254,242,242,0.5)', '#b91c1c', '#f87171'] : ['#e2e8f0', 'rgba(248,250,252,0.6)', '#64748b', '#94a3b8'];
          return {
            title: x.title, items: x.items.map(htmlString => ({ obj: { __html: htmlString } })),
            boxStyle: { borderRadius: '8px', border: '1px solid ' + m[0], background: m[1], padding: '12px' },
            titleStyle: { fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', color: m[2], margin: '0 0 4px' },
            dotStyle: { marginTop: '6px', width: '4px', height: '4px', borderRadius: '9999px', background: m[3], flexShrink: 0 }
          };
        }),
        topPages: data.topPages.map(r => ({ url: r.url, clicksFmt: this.fmt(r.clicks), imprFmt: this.fmt(r.impressions), ctrFmt: r.ctr + '%' }))
      };
    }


        /* ============ SEO ============ */
    if (tab === 'seo') {
      vals.showSeo = true;
      vals.seo = {
        lowCtrCount: data.kpis.low_ctr, anomalyCount: data.kpis.anomalies,
        criticalCount: data.kpis.critical, quickWins: data.quickWinKws,
        lowCtrRows: data.lowCtrPages.map(r => ({ url: r.url, imprFmt: this.fmt(r.impressions), clicks: r.clicks, ctrFmt: r.ctr + '%', avgPos: r.avg_pos })),
        countries: data.countries.map(c => ({ country: c.country, clicksFmt: this.fmt(c.clicks), ctrFmt: c.ctr + '%' })),
        anomalies: data.anomalies.map(a => ({
          metric: a.metric, severity: a.severity, date: a.date,
          deviation: a.deviation || '—',
          sevStyle: this.sevChip(a.severity),
          devStyle: { color: String(a.deviation).indexOf('-') === 0 || String(a.deviation).indexOf('−') === 0 ? '#dc2626' : '#059669', fontWeight: 500 }
        }))
      };
    }


        /* ============ KEYWORDS ============ */
    if (tab === 'keywords') {
      vals.showKeywords = true;
      const segDefs = [
        { id: null, label: 'All', hint: null },
        { id: 'quick_wins', label: '⚡ Quick Wins', hint: 'These keywords rank #4–10 AND already get real clicks. A small push can move them into the top 3 — where CTR doubles.', action: 'Improve meta titles, add internal links, expand content depth.' },
        { id: 'striking', label: '🎯 Striking Distance', hint: 'Ranking #11–20 — page two. These are one content refresh away from page one.', action: 'Refresh content, add internal links from your top pages.' },
        { id: 'declining', label: '📉 Declining', hint: 'Dropped ≥2 positions since the last weekly sync.', action: 'Check SERP changes and competitor updates; consider a content refresh.' },
        { id: 'low_ctr', label: '👀 High Imp, Low CTR', hint: 'Seen often (≥100 impressions) but clicked under 2% of the time.', action: 'Rewrite title tags & meta descriptions.' }
      ];
      const counts = {
        null: data.keywords.length,
        quick_wins: data.segments.quick_wins.length, striking: data.segments.striking.length,
        declining: data.segments.declining.length, low_ctr: data.segments.low_ctr.length
      };
      const active = segDefs.find(d => d.id === s.kwSeg) || segDefs[0];
      const idSet = s.kwSeg ? new Set(data.segments[s.kwSeg]) : null;
      let rows = data.keywords.filter(k => !idSet || idSet.has(k.id));
      rows = this.sortRows(rows, s.kwSort);
      const tabBase = { padding: '14px 4px', borderBottom: '2px solid transparent', color: '#64748b', fontSize: '14px', cursor: 'pointer' };
      const tabActive = Object.assign({}, tabBase, { borderBottom: '2px solid #4f46e5', color: '#4f46e5', fontWeight: 500 });
      const intentTotal = Math.max(1, data.kpis.total);
      const intentDefs = [
        ['Informational', 'informational', '#3b82f6', '#dbeafe', '#2563eb', 'I'],
        ['Commercial', 'commercial', '#10b981', '#d1fae5', '#059669', 'C'],
        ['Transactional', 'transactional', '#f97316', '#ffedd5', '#ea580c', 'T'],
        ['Navigational', 'navigational', '#a855f7', '#f3e8ff', '#9333ea', 'N']
      ];
      const kdDefs = [
        ['Easy (0–29)', 'easy', '#10b981', '#d1fae5', '#059669', 'E', '#047857'],
        ['Medium (30–59)', 'medium', '#f59e0b', '#fef3c7', '#d97706', 'M', '#b45309'],
        ['Hard (60+)', 'hard', '#ef4444', '#fee2e2', '#dc2626', 'H', '#b91c1c']
      ];
      const kwSetup = !data || !data.kpis || data.kpis.state === 'setup' || (data.kpis.total === 0 && (!data.keywords || !data.keywords.length));
      if (kwSetup) {
        vals.kw = { setup: true, total: 0, avgPos: 0, totalVolume: 0, totalClicks: 0, intentRows: [], kdRows: [], tabs: [], rows: [] };
        return vals;
      }
      vals.kw = {
        total: data.kpis.total, avgPos: data.kpis.avg_pos,
        totalVolume: this.fmt(data.kpis.total_volume), totalClicks: this.fmt(data.kpis.total_clicks),
        intentRows: intentDefs.map(d => ({
          label: d[0], count: data.intents[d[1]],
          iconChar: d[5],
          iconStyle: { width: '20px', height: '20px', borderRadius: '4px', background: d[3], color: d[4], display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px', fontWeight: 700, flexShrink: 0 },
          barStyle: { height: '100%', width: Math.round((data.intents[d[1]] / intentTotal) * 100) + '%', background: d[2] }
        })),
        kdRows: kdDefs.map(d => ({
          label: d[0], count: data.difficulty[d[1]],
          iconChar: d[5],
          iconStyle: { width: '20px', height: '20px', borderRadius: '4px', background: d[3], color: d[4], display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px', fontWeight: 700, flexShrink: 0 },
          barStyle: { height: '100%', width: Math.round((data.difficulty[d[1]] / intentTotal) * 100) + '%', background: d[2] },
          countStyle: { fontSize: '14px', fontWeight: 600, color: d[6], width: '32px', textAlign: 'right' }
        })),
        tabs: segDefs.map(d => ({
          label: d.label + ' (' + counts[d.id] + ')',
          style: d.id === s.kwSeg ? tabActive : tabBase,
          click: () => { this.setState({ kwSeg: d.id }); this.pushNav({ kwSeg: d.id }); }
        })),
        hasHint: !!active.hint, hintText: active.hint || '', hintAction: active.action || '',
        tableTitle: s.kwSeg ? active.label.replace(/^[^ ]+ /, '') + ' Keywords' : 'All Keywords',
        rows: rows.map(k => {
          const iv = this.intentView(k.intent);
          let deltaFmt = '—', deltaColor = '#cbd5e1';
          if (k.prevPos == null) { deltaFmt = 'new'; deltaColor = '#2563eb'; }
          else {
            const d = k.prevPos - k.pos;
            if (d > 0) { deltaFmt = '▲ ' + d; deltaColor = '#059669'; }
            else if (d < 0) { deltaFmt = '▼ ' + Math.abs(d); deltaColor = '#dc2626'; }
          }
          return {
            kw: k.kw, url: k.url || 'not ranking yet', isManual: k.source === 'manual',
            intentLabel: iv.label, intentStyle: iv.style,
            posText: k.pos == null ? '—' : k.pos, posStyle: this.posBadge(k.pos),
            deltaFmt, deltaStyle: { fontSize: '12px', fontWeight: 600, color: deltaColor },
            volFmt: this.fmt(k.volume),
            spark: this.spark(k.monthly, 46, 16),
            sparkColor: k.monthly && k.monthly[11] >= k.monthly[0] ? '#22c55e' : '#ef4444',
            kd: k.kd,
            kdBarStyle: { height: '100%', width: Math.min(100, k.kd) + '%', background: this.kdColor(k.kd) },
            clicksFmt: this.fmt(k.clicks)
          };
        })
      };
    }


        /* ============ POSITIONING ============ */
    if (tab === 'positioning') {
      vals.showPositioning = true;
      vals.ptIsList = s.ptView !== 'workspace';
      vals.ptIsWorkspace = s.ptView === 'workspace';
      vals.ptWizOpen = s.ptWizOpen;
      vals.ptEditOpen = s.ptEditOpen;
      vals.ptEditBusy = s.ptEditBusy;
      vals.ptEditKws = s.ptEditKws || '';
      vals.ptEditKwsFn = e => this.setState({ ptEditKws: e.target.value });
      vals.ptEditDomain = s.ptEditDomain || '';
      vals.ptEditName = s.ptEditName || '';
      vals.ptEditNameFn = e => this.setState({ ptEditName: e.target.value });
      vals.ptEditEngine = s.ptEditEngine || 'Google';
      vals.ptEditEngineFn = e => this.setState({ ptEditEngine: e.target.value });
      vals.ptEditDevice = s.ptEditDevice || 'Desktop';
      vals.ptEditDeviceFn = e => this.setState({ ptEditDevice: e.target.value });
      vals.ptEditLang = s.ptEditLang || 'English';
      vals.ptEditLangFn = e => this.setState({ ptEditLang: e.target.value });
      vals.ptEditLoc = s.ptEditLoc || 'United States';
      vals.ptEditLocFn = e => this.setState({ ptEditLoc: e.target.value });
      vals.ptEditClose = () => this.setState({ ptEditOpen: false, ptEditBusy: false });
      vals.ptEditSave = () => {
        if (s.ptEditBusy) return;
        this.setState({ ptEditBusy: true });
        const kwLines = (s.ptEditKws || '').split(/\r?\n/).map(l => l.trim()).filter(Boolean);
        const kwsToSend = kwLines.map(kw => ({ kw: kw, volume: 0, kd: null, cpc: null, intent: 'Informational' }));
        const comps = s.ptWizComps || [];
        
        Promise.all([
          window.FuseAPI.put('/api/projects/' + s.projectId + '/settings', { project: { competitors: comps, name: s.ptEditName, location: s.ptEditLoc } }).catch(() => {}),
          window.FuseAPI.put('/api/projects/' + s.projectId + '/keywords', { keywords: kwsToSend }).catch(() => {})
        ]).then(() => {
          this.setState({ ptEditBusy: false, ptEditOpen: false });
          this.startSync('positions');
          if (this.notify) this.notify('Project updated. Refreshing positions...');
        });
      };

      /* ---- global handlers exposed for template holes ---- */
      vals.ptNewProject = () => this.setState({ ptWizOpen: true, ptWizStep: 1, ptWizDomain: '', ptWizName: '', ptWizEngine: 'Google', ptWizLang: 'English', ptWizLoc: 'United States', ptWizDevice: 'Desktop', ptWizKwMode: 'paste', ptWizKwText: '', ptWizListId: (s.kwLists && s.kwLists[0] && s.kwLists[0].id) || null, ptWizComps: [], ptWizCompInput: '' });
      vals.ptCreateAndSend = () => {
        const rows = this.selectedRows();
        this._pendingSendRows = rows;
        const kwLines = rows.map(r => r.kw).join('\n');
        this.setState({
          ptWizOpen: true, ptWizStep: 1, ptWizDomain: '', ptWizName: '', ptWizEngine: 'Google', ptWizLang: 'English', ptWizLoc: 'United States', ptWizDevice: 'Desktop', ptWizKwMode: 'paste', ptWizKwText: kwLines, ptWizComps: [], ptWizCompInput: '', sendOpen: false, sendSub: null
        });
      };
      vals.ptSearchFn = (e) => this.setState({ ptSearch: e.target.value });
      vals.ptBackToList = () => this.setState({ ptView: 'list' });
      vals.ptWizClose = () => this.setState({ ptWizOpen: false });
      vals.ptWizPrev = () => this.setState(st => ({ ptWizStep: Math.max(1, st.ptWizStep - 1) }));
      vals.ptWizFieldDomain = (e) => this.setState({ ptWizDomain: e.target.value });
      vals.ptWizFieldName = (e) => this.setState({ ptWizName: e.target.value });
      vals.ptWizFieldEngine = (e) => this.setState({ ptWizEngine: e.target.value });
      vals.ptWizFieldLang = (e) => this.setState({ ptWizLang: e.target.value });
      vals.ptWizFieldLoc = (e) => this.setState({ ptWizLoc: e.target.value });
      vals.ptWizFieldDevice = (e) => this.setState({ ptWizDevice: e.target.value });
      vals.ptWizFieldKwText = (e) => this.setState({ ptWizKwText: e.target.value });
      vals.ptWizModePaste = () => this.setState({ ptWizKwMode: 'paste' });
      vals.ptWizModeList = () => this.setState({ ptWizKwMode: 'list' });
      vals.ptWizCompInputFn = (e) => this.setState({ ptWizCompInput: e.target.value });
      vals.ptWizCompAddFn = () => {
        const v = (this.state.ptWizCompInput || '').trim().toLowerCase().replace(/^https?:\/\//, '').replace(/\/$/, '');
        if (!v) return;
        this.setState(st => (st.ptWizComps.includes(v) || st.ptWizComps.length >= 5) ? { ptWizCompInput: '' } : { ptWizComps: st.ptWizComps.concat([v]), ptWizCompInput: '' });
      };
      vals.ptWizCompKeyFn = (e) => { if (e.key === 'Enter') vals.ptWizCompAddFn(); };


      vals.ptWizFinish = () => {
        const domainStr = (this.state.ptWizDomain || '').trim();
        const domain = domainStr.toLowerCase().replace(/^https?:\/\//, '').replace(/\/$/, '');
        if (!domain) { this.setState({ ptWizStep: 1 }); return; }
        
        if (this.state.projects.some(p => p.domain === domain)) {
          this.setState({ ptWizBusy: false, ptWizOpen: false });
          if (this.notify) this.notify('That site is already added to Position Tracking');
          return;
        }

        this.setState({ ptWizBusy: true });
        window.FuseAPI.post('/api/projects', { domain: domainStr, name: (this.state.ptWizName || '').trim() || undefined, location: this.state.ptWizLoc })
          .then(p => {
            if (!this._alive) return;
            this.setState({ ptWizBusy: false, ptWizOpen: false, ptView: 'workspace', ptTab: 'landscape', projectId: p.id });
            
            // Save competitors
            if (this.state.ptWizComps && this.state.ptWizComps.length > 0) {
              window.FuseAPI.put('/api/projects/' + p.id + '/settings', { action: 'targets', competitors: this.state.ptWizComps }).catch(() => {});
            }

            let kwsToSend = [];
            if (this._pendingSendRows && this._pendingSendRows.length) {
              kwsToSend = this._pendingSendRows;
              this._pendingSendRows = null;
            } else if (this.state.ptWizKwText && this.state.ptWizKwText.trim()) {
              const lines = this.state.ptWizKwText.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
              kwsToSend = lines.map(kw => ({ kw: kw, volume: 0, kd: null, cpc: null, intent: 'Informational' }));
            }
            if (kwsToSend.length > 0) {
              this.sendKwsToTracking(p.id, kwsToSend);
            } else {
              window.FuseAPI.get('/api/projects').then(ps => { if (this._alive) this.setState({ projects: ps }); }).catch(() => {});
              this.fetchTab('positioning', p.id, this.state.range, true);
              if (this.notify) this.notify('SEO project created for ' + p.domain);
            }
          })
          .catch(err => { if (this._alive) { this.setState({ ptWizBusy: false }); if (this.notify) this.notify(err.detail || 'Could not create project'); } });
      };
      vals.ptWizNext = () => { if (this.state.ptWizStep >= 4) { vals.ptWizFinish(); } else { this.setState(st => ({ ptWizStep: Math.min(4, st.ptWizStep + 1) })); } };

      /* ---- projects list ---- */
      const searchVal = (s.ptSearch || '').trim().toLowerCase();
      vals.ptSearchVal = s.ptSearch || '';
      const mkFilter = (val, label) => { const active = (s.ptFilter || 'all') === val; return { label, onClick: () => this.setState({ ptFilter: val }), style: { padding: '8px 14px', cursor: 'pointer', fontSize: '13px', background: active ? '#eef2ff' : 'white', color: active ? '#4338ca' : '#64748b', fontWeight: active ? 600 : 400, borderLeft: val === 'all' ? 'none' : '1px solid #e2e8f0' } }; };
      vals.ptFilters = [mkFilter('all', 'All projects')];
      const projList = (s.projects || []).filter(p => !searchVal || (p.domain + ' ' + (p.name || '')).toLowerCase().includes(searchVal));
      const listCols = 'minmax(200px,2fr) 150px 90px 80px 80px 120px';
      vals.ptListGridCols = listCols;
      vals.ptProjects = projList.map(p => {
        const isCur = p.id === s.projectId;
        const tracked = p.tracked_keywords_count || 0;
        const avgPos = p.avg_position || 0;
        const vis = avgPos > 0 ? Math.min(100, Math.max(5, Math.round((100 - avgPos) / 1.2))) : (tracked > 0 ? 50 : 0);
        const improved = p.improved_count || 0;
        const declined = p.declined_count || 0;
        const visColor = vis >= 45 ? '#059669' : vis >= 25 ? '#0891b2' : '#d97706';
        return {
          id: p.id, name: p.name || p.domain, domain: p.domain, location: p.location || 'United States', device: 'Desktop',
          tracked: this.fmt(tracked), improved, declined,
          visLabel: vis + '%', visColor,
          visBarStyle: { width: vis + '%', height: '100%', background: visColor, borderRadius: '4px' },
          updated: p.last_updated || 'No sync yet',
          isCurrent: isCur,
          rowStyle: { display: 'grid', gridTemplateColumns: listCols, alignItems: 'center', padding: '14px 20px', borderTop: '1px solid #f1f5f9', cursor: 'pointer', background: isCur ? '#fafaff' : 'white' },
          onOpen: () => {
            this.setState({ ptView: 'workspace', projectId: p.id });
            this.fetchTab('positioning', p.id, this.state.range, true);
          }
        };
      });
      vals.ptNoProjects = vals.ptProjects.length === 0;

      /* ---- wizard ---- */
      const lists = s.kwLists || [];
      const wizComps = s.ptWizComps || [];
      const wizSteps = ['Site', 'Tracking area', 'Keywords', 'Competitors'];
      const segStyleFn = (on) => ({ flex: 1, textAlign: 'center', padding: '8px', fontSize: '13px', fontWeight: 500, borderRadius: '6px', cursor: 'pointer', background: on ? '#ffffff' : 'transparent', color: on ? '#4338ca' : '#64748b', boxShadow: on ? '0 1px 2px rgba(0,0,0,0.06)' : 'none' });
      vals.ptWiz = {
        stepItems: wizSteps.map((nm, i2) => { const n = i2 + 1; const st2 = n < s.ptWizStep ? 'done' : n === s.ptWizStep ? 'active' : 'todo'; return { label: nm, n, circleStyle: { width: '26px', height: '26px', borderRadius: '9999px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px', fontWeight: 600, background: st2 === 'todo' ? '#f1f5f9' : '#4f46e5', color: st2 === 'todo' ? '#94a3b8' : 'white', flexShrink: 0 }, labelStyle: { fontSize: '13px', fontWeight: st2 === 'active' ? 600 : 400, color: st2 === 'todo' ? '#94a3b8' : '#334155', whiteSpace: 'nowrap' } }; }),
        isStep1: s.ptWizStep === 1, isStep2: s.ptWizStep === 2, isStep3: s.ptWizStep === 3, isStep4: s.ptWizStep === 4,
        domain: s.ptWizDomain, name: s.ptWizName,
        engine: s.ptWizEngine, language: s.ptWizLang, location: s.ptWizLoc, device: s.ptWizDevice,
        engineOpts: ['Google', 'Bing'], langOpts: ['English', 'Spanish', 'French'], 
        locOpts: s.allUsCities ? (s.ptWizLoc ? s.allUsCities.filter(c => c.toLowerCase().includes(s.ptWizLoc.toLowerCase())).slice(0, 100) : ['United States', 'Canada', 'United Kingdom', 'Australia'].concat(s.allUsCities.slice(0, 96))) : [
          'United States', 'Canada', 'United Kingdom', 'Australia',
          'United States - Alabama', 'United States - Alaska', 'United States - Arizona', 'United States - Arkansas', 'United States - California', 'United States - Colorado', 'United States - Connecticut', 'United States - Delaware', 'United States - Florida', 'United States - Georgia', 'United States - Hawaii', 'United States - Idaho', 'United States - Illinois', 'United States - Indiana', 'United States - Iowa', 'United States - Kansas', 'United States - Kentucky', 'United States - Louisiana', 'United States - Maine', 'United States - Maryland', 'United States - Massachusetts', 'United States - Michigan', 'United States - Minnesota', 'United States - Mississippi', 'United States - Missouri', 'United States - Montana', 'United States - Nebraska', 'United States - Nevada', 'United States - New Hampshire', 'United States - New Jersey', 'United States - New Mexico', 'United States - New York', 'United States - North Carolina', 'United States - North Dakota', 'United States - Ohio', 'United States - Oklahoma', 'United States - Oregon', 'United States - Pennsylvania', 'United States - Rhode Island', 'United States - South Carolina', 'United States - South Dakota', 'United States - Tennessee', 'United States - Texas', 'United States - Utah', 'United States - Vermont', 'United States - Virginia', 'United States - Washington', 'United States - West Virginia', 'United States - Wisconsin', 'United States - Wyoming'
        ],
        deviceOpts: ['Desktop', 'Mobile'],
        kwMode: s.ptWizKwMode, kwPaste: s.ptWizKwMode === 'paste', kwList: s.ptWizKwMode === 'list',
        kwText: s.ptWizKwText, kwCount: (s.ptWizKwText || '').split(',').map(x => x.trim()).filter(Boolean).length,
        pasteTabStyle: segStyleFn(s.ptWizKwMode === 'paste'), listTabStyle: segStyleFn(s.ptWizKwMode === 'list'),
        lists: lists.map(l => { const active = s.ptWizListId === l.id; return { name: l.name, count: (l.keywords ? l.keywords.length : 0) + ' keywords', rowStyle: { display: 'flex', alignItems: 'center', gap: '10px', padding: '12px 14px', borderRadius: '8px', cursor: 'pointer', border: '1px solid ' + (active ? '#c7d2fe' : '#e2e8f0'), background: active ? '#eef2ff' : 'white' }, dotStyle: active ? { width: '16px', height: '16px', borderRadius: '9999px', border: '5px solid #4f46e5', boxSizing: 'border-box', flexShrink: 0 } : { width: '16px', height: '16px', borderRadius: '9999px', border: '1px solid #cbd5e1', boxSizing: 'border-box', flexShrink: 0 }, onPick: () => this.setState({ ptWizListId: l.id }) }; }),
        comps: wizComps.map(d => ({ domain: d, onRemove: () => this.setState(st => ({ ptWizComps: st.ptWizComps.filter(x => x !== d) })) })),
        compInput: s.ptWizCompInput, compNote: wizComps.length + ' of 5 competitors',
        canBack: s.ptWizStep > 1, noBack: s.ptWizStep <= 1,
        nextLabel: s.ptWizStep === 4 ? (s.ptWizBusy ? 'Creating…' : 'Create project') : 'Continue'
      };

      if (vals.ptIsWorkspace) {
        const proj = (s.projects || []).find(p => p.id === s.projectId) || {};
        const activeTab = s.ptWsTab || s.ptTab || 'landscape';
        const wsTabDef = [['landscape', 'Landscape', false], ['overview', 'Overview', false], ['pages', 'Pages', false]];
        vals.ptWs = {
          name: proj.name || proj.domain || 'Project',
          domain: proj.domain || '',
          device: 'Desktop',
          location: proj.location || 'United States',
          onEdit: () => {
            this.setState({ 
              ptEditOpen: true, ptEditBusy: false, ptEditKws: '', ptWizComps: [], ptWizCompInput: '',
              ptEditDomain: proj.domain || '',
              ptEditName: proj.name || '',
              ptEditEngine: 'Google',
              ptEditDevice: 'Desktop',
              ptEditLang: 'English',
              ptEditLoc: proj.location || 'United States'
            });
            window.FuseAPI.get('/api/projects/' + proj.id + '/settings').then(res => {
              if (this.state.ptEditOpen && res && res.project) {
                this.setState({
                  ptEditKws: (res.project.tracked_keywords || []).join('\n'),
                  ptWizComps: (res.project.competitors || [])
                });
              }
            }).catch(() => {});
          },
          onDelete: () => {
            if (confirm('Are you sure you want to delete this project?')) {
              window.FuseAPI.delete('/api/projects/' + proj.id).then(() => {
                this.setState({ ptView: 'list', projectId: null });
                window.FuseAPI.get('/api/projects').then(ps => this.setState({ projects: ps })).catch(() => {});
              }).catch(err => { if (this.notify) this.notify(err.detail || 'Could not delete project'); });
            }
          },
          onRefresh: () => this.startSync('positions'),
          snapshotRange: 'Last 30 days',
          tabs: wsTabDef.map(([k, label, soon]) => {
            const active = activeTab === k;
            return {
              label: label + (soon ? ' · soon' : ''),
              onClick: soon ? (() => {}) : (() => this.setState({ ptWsTab: k, ptTab: k })),
              style: { padding: '10px 18px', fontSize: '14px', cursor: soon ? 'not-allowed' : 'pointer', fontWeight: active ? 600 : 500, color: active ? '#4f46e5' : (soon ? '#cbd5e1' : '#64748b'), borderBottom: active ? '2px solid #4f46e5' : '2px solid transparent', marginBottom: '-1px' }
            };
          }),
          showLandscape: activeTab === 'landscape',
          showRankings: activeTab === 'rankings',
          showCompetitors: activeTab === 'competitors',
          rankingsTab: s.ptRankingsSubTab || 'all',
          onTabAll: () => this.setState({ ptRankingsSubTab: 'all' }),
          onTabTop10: () => this.setState({ ptRankingsSubTab: 'top10' }),
          onTabImproved: () => this.setState({ ptRankingsSubTab: 'improved' }),
          onTabDeclined: () => this.setState({ ptRankingsSubTab: 'declined' })
        };
        vals.ptTabOverview = activeTab === 'overview';
        vals.ptTabPages = activeTab === 'pages';
        vals.ptTabLandscape = !vals.ptTabOverview && !vals.ptTabPages;
      }

      const ptSetup = !data || !data.kpis || data.kpis.state === 'setup' || (data.kpis.tracked === 0 && (!data.movers || !data.movers.length) && (!data.competitors || !data.competitors.rows || !data.competitors.rows.length) && (!data.rankings || !data.rankings.length));
      if (ptSetup) {
        vals.pt = { setup: true, tracked: 0, avgPos: 0, traffic: 0, impressions: 0, distSegs: [], distLegend: [], improved: 0, declined: 0, added: 0, lost: 0, movers: [], compDomains: [], compGridCols: '', compRows: [], rankings: [], filteredRankings: [] };
        return vals;
      }
      const dist = data.distribution;
      const total = Math.max(1, dist.top3 + dist.p4_10 + dist.p11_20 + dist.p21_100);
      const distDefs = [
        ['Top 3', dist.top3, '#10b981'], ['4–10', dist.p4_10, '#3b82f6'],
        ['11–20', dist.p11_20, '#f59e0b'], ['21–100', dist.p21_100, '#cbd5e1']
      ];
      vals.pt = {
        tracked: data.kpis.tracked, avgPos: data.kpis.avg_pos,
        traffic: this.fmt(data.kpis.est_traffic), impressions: this.fmt(data.kpis.impressions),
        distSegs: distDefs.map(d => ({
          count: d[1] > 0 ? d[1] : '',
          style: { background: d[2], width: Math.max(4, Math.round((d[1] / total) * 100)) + '%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontSize: '12px', fontWeight: 700 }
        })),
        distLegend: distDefs.map(d => ({
          label: d[0], count: d[1],
          swatch: { width: '12px', height: '12px', borderRadius: '2px', background: d[2] }
        })),
        improved: data.movement.improved, declined: data.movement.declined,
        added: data.movement.added, lost: data.movement.lost,
        movers: data.movers.map(k => {
          const d = k.prevPos - k.pos;
          return {
            kw: k.kw, was: '#' + k.prevPos, now: k.pos, posStyle: this.posBadge(k.pos),
            change: (d > 0 ? '▲ +' : '▼ −') + Math.abs(d),
            chipStyle: { padding: '3px 8px', borderRadius: '4px', fontSize: '12px', fontWeight: 600, background: d > 0 ? '#d1fae5' : '#fee2e2', color: d > 0 ? '#047857' : '#b91c1c' },
            volFmt: this.fmt(k.volume)
          };
        }),
        compDomains: data.competitors.domains,
        compGridCols: 'minmax(180px, 1.4fr) repeat(' + (1 + data.competitors.domains.length) + ', 1fr)',
        compRows: data.competitors.rows.map(row => ({
          kw: row.kw,
          cells: [{ text: row.you, style: this.posBadge(row.you) }].concat(
            row.comps.map(c => c == null
              ? { text: '—', style: { color: '#cbd5e1' } }
              : { text: c, style: this.posBadge(c) })
          )
        })),
        rankings: (data.rankings || data.keywords || []).map(k => {
          const d = k.prevPos != null && k.pos != null ? k.prevPos - k.pos : null;
          const iLower = (k.intent || '').toLowerCase();
          return {
            kw: k.kw,
            pos: k.pos != null ? k.pos : '—',
            posBadgeStyle: this.posBadge(k.pos),
            deltaText: d != null ? (d > 0 ? '▲ +' + d : (d < 0 ? '▼ −' + Math.abs(d) : '—')) : (k.pos != null ? 'NEW' : '—'),
            deltaStyle: { fontSize: '12px', fontWeight: 600, color: d != null ? (d > 0 ? '#059669' : (d < 0 ? '#dc2626' : '#94a3b8')) : '#3b82f6' },
            volume: this.fmt(k.volume),
            clicks: k.clicks != null ? k.clicks : 0,
            kd: k.kd != null ? Math.round(k.kd) : '—',
            kdWidth: k.kd != null ? Math.min(100, Math.max(5, Math.round(k.kd))) + '%' : '0%',
            kdColor: k.kd != null ? (k.kd < 30 ? '#10b981' : (k.kd < 60 ? '#f59e0b' : '#ef4444')) : '#e2e8f0',
            cpc: k.cpc != null ? '$' + Number(k.cpc).toFixed(2) : '—',
            intent: k.intent || '—',
            intentStyle: { padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', background: iLower.includes('comm') ? '#d1fae5' : (iLower.includes('info') ? '#dbeafe' : (iLower.includes('trans') ? '#ffedd5' : '#f1f5f9')), color: iLower.includes('comm') ? '#047857' : (iLower.includes('info') ? '#1d4ed8' : (iLower.includes('trans') ? '#c2410c' : '#475569')) },
            urlShort: (k.url || '').replace(/^https?:\/\/[^\/]+/, '') || (k.url || '—'),
            url: k.url || ''
          };
        }),
        filteredRankings: (data.rankings || data.keywords || []).filter(k => {
          const st = s.ptRankingsSubTab || 'all';
          if (st === 'top10') return k.pos != null && k.pos <= 10;
          if (st === 'improved') return k.prevPos != null && k.pos != null && (k.prevPos - k.pos) >= 2;
          if (st === 'declined') return k.prevPos != null && k.pos != null && (k.prevPos - k.pos) <= -2;
          return true;
        }).map(k => {
          const d = k.prevPos != null && k.pos != null ? k.prevPos - k.pos : null;
          const iLower = (k.intent || '').toLowerCase();
          return {
            kw: k.kw,
            pos: k.pos != null ? k.pos : '—',
            posBadgeStyle: this.posBadge(k.pos),
            deltaText: d != null ? (d > 0 ? '▲ +' + d : (d < 0 ? '▼ −' + Math.abs(d) : '—')) : (k.pos != null ? 'NEW' : '—'),
            deltaStyle: { fontSize: '12px', fontWeight: 600, color: d != null ? (d > 0 ? '#059669' : (d < 0 ? '#dc2626' : '#94a3b8')) : '#3b82f6' },
            volume: this.fmt(k.volume),
            clicks: k.clicks != null ? k.clicks : 0,
            kd: k.kd != null ? Math.round(k.kd) : '—',
            kdWidth: k.kd != null ? Math.min(100, Math.max(5, Math.round(k.kd))) + '%' : '0%',
            kdColor: k.kd != null ? (k.kd < 30 ? '#10b981' : (k.kd < 60 ? '#f59e0b' : '#ef4444')) : '#e2e8f0',
            cpc: k.cpc != null ? '$' + Number(k.cpc).toFixed(2) : '—',
            intent: k.intent || '—',
            intentStyle: { padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', background: iLower.includes('comm') ? '#d1fae5' : (iLower.includes('info') ? '#dbeafe' : (iLower.includes('trans') ? '#ffedd5' : '#f1f5f9')), color: iLower.includes('comm') ? '#047857' : (iLower.includes('info') ? '#1d4ed8' : (iLower.includes('trans') ? '#c2410c' : '#475569')) },
            urlShort: (k.url || '').replace(/^https?:\/\/[^\/]+/, '') || (k.url || '—'),
            url: k.url || ''
          };
        })
      };

      if (vals.ptIsWorkspace && vals.pt) {
        const scMap = [
          { k: 'top3', name: 'Top 3', color: '#10b981', val: dist.top3, delta: '+2' },
          { k: 'p4_10', name: '4–10', color: '#3b82f6', val: dist.p4_10, delta: '+5' },
          { k: 'p11_20', name: '11–20', color: '#f59e0b', val: dist.p11_20, delta: '-1' },
          { k: 'p21_100', name: '21–100', color: '#cbd5e1', val: dist.p21_100, delta: '0' }
        ];
        const hiddenOv = s.ptOvHidden || [];
        vals.ptOv = {
          prevDate: 'Jun 20', curDate: 'Jul 20',
          scoreCards: scMap.map(item => {
            const off = hiddenOv.includes(item.k);
            return {
              name: item.name, valLabel: item.val, deltaLabel: item.delta,
              swatch: { width: '8px', height: '8px', borderRadius: '2px', background: item.color, display: 'inline-block' },
              cardValStyle: { fontSize: '24px', fontWeight: 700, color: off ? '#cbd5e1' : '#0f172a' },
              deltaStyle: { fontSize: '12px', fontWeight: 600, color: item.delta.startsWith('+') ? '#059669' : (item.delta.startsWith('-') ? '#dc2626' : '#94a3b8') },
              legendStyle: { display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: off ? '#94a3b8' : '#334155', cursor: 'pointer', userSelect: 'none' },
              checkStyle: { width: '14px', height: '14px', borderRadius: '3px', border: '1px solid ' + (off ? '#cbd5e1' : item.color), background: off ? 'white' : item.color, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontSize: '10px', fontWeight: 700 },
              check: off ? '' : '✓',
              onToggle: () => {
                const nh = off ? hiddenOv.filter(x => x !== item.k) : hiddenOv.concat([item.k]);
                this.setState({ ptOvHidden: nh });
              }
            };
          }),
          chart: (() => {
            const pts = { top3: [12, 14, 13, 15, 14, 18], p4_10: [25, 24, 28, 30, 32, 35], p11_20: [40, 42, 38, 41, 39, 42], p21_100: [60, 58, 62, 60, 65, 68] };
            const series = scMap.filter(item => !hiddenOv.includes(item.k)).map(item => {
              const arr = pts[item.k] || [10, 10, 10, 10, 10, item.val || 10];
              const maxVal = Math.max(10, ...arr);
              const pStr = arr.map((v, idx) => {
                const x = 50 + idx * 130;
                const y = 180 - (v / maxVal) * 150;
                return x + ',' + y;
              }).join(' ');
              const lastX = 50 + 5 * 130;
              const lastY = 180 - (arr[5] / maxVal) * 150;
              return { color: item.color, points: pStr, dotX: lastX, dotY: lastY };
            });
            return {
              viewBox: '0 0 720 210', lineX1: 50, lineX2: 700, labelX: 42, xLabelY: 200,
              grid: [{ y: 30, label: '80' }, { y: 68, label: '60' }, { y: 105, label: '40' }, { y: 143, label: '20' }, { y: 180, label: '0' }],
              xTicks: ['Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'].map((m, idx) => ({ label: m, x: 50 + idx * 130 })),
              series: series
            };
          })(),
          domains: vals.pt.compDomains.map((d, idx) => ({ name: d, style: { textAlign: 'center', color: idx === 0 ? '#4338ca' : '#64748b' } })),
          gridCols: 'minmax(180px, 1.4fr) 80px 70px repeat(' + (1 + vals.pt.compDomains.length) + ', 1fr)',
          rows: vals.pt.compRows.map(row => {
            const rInfo = (vals.pt.rankings || []).find(r => r.kw === row.kw) || {};
            return {
              kw: row.kw, volFmt: rInfo.volume || '0', kd: rInfo.kd || '—',
              kdStyle: { display: 'flex', alignItems: 'center', gap: '5px', fontSize: '13px', color: '#475569' },
              kdDotStyle: { width: '8px', height: '8px', borderRadius: '50%', background: rInfo.kdColor || '#cbd5e1' },
              onSerp: () => this.setState({ ptSerpKw: row.kw }),
              cells: row.cells.map(c => {
                const pos = c.text;
                return {
                  pos: pos, diff: '', cellStyle: { textAlign: 'center', padding: '6px', borderRadius: '6px', cursor: 'pointer', transition: 'background 0.15s' },
                  posStyle: c.style, diffStyle: { fontSize: '11px', color: '#94a3b8', marginLeft: '4px' },
                  onCell: () => this.setState({ ptOvUrlPop: { open: true, url: rInfo.url || 'https://' + vals.ptWs.domain + '/' + row.kw.replace(/\s+/g, '-'), kw: row.kw } })
                };
              })
            };
          }),
          urlPopOpen: !!(s.ptOvUrlPop && s.ptOvUrlPop.open),
          urlPop: s.ptOvUrlPop && s.ptOvUrlPop.open ? {
            url: s.ptOvUrlPop.url, href: s.ptOvUrlPop.url,
            style: { position: 'fixed', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', zIndex: 90, background: 'white', borderRadius: '12px', padding: '20px', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04)', border: '1px solid #e2e8f0', width: '360px', maxWidth: '90vw' },
            onClose: () => this.setState({ ptOvUrlPop: null }),
            onCopy: () => { navigator.clipboard.writeText(s.ptOvUrlPop.url).catch(() => {}); if (this.notify) this.notify('URL copied to clipboard'); this.setState({ ptOvUrlPop: null }); }
          } : {}
        };

        const openPages = s.ptOpenPages || [];
        const pagesMap = {};
        (vals.pt.rankings || []).forEach(r => {
          const u = r.url || ('https://' + vals.ptWs.domain + '/' + r.kw.replace(/\s+/g, '-'));
          if (!pagesMap[u]) pagesMap[u] = { url: u, kws: [] };
          pagesMap[u].kws.push(r);
        });
        const pageList = Object.values(pagesMap);
        vals.ptPages = {
          gridCols: 'minmax(240px, 2fr) 100px 120px 100px 100px 100px',
          rows: pageList.map((p, idx) => {
            const isOpen = openPages.includes(p.url);
            const avg = Math.round(p.kws.reduce((acc, k) => acc + (typeof k.pos === 'number' ? k.pos : 20), 0) / p.kws.length);
            const totVol = p.kws.reduce((acc, k) => acc + (parseInt((k.volume || '0').replace(/,/g, ''), 10) || 0), 0);
            return {
              url: p.url.replace(/^https?:\/\/[^\/]+/, '') || '/', href: p.url, isNew: idx === 0,
              kwCount: p.kws.length, kwDiff: '+1', kwDiffStyle: { fontSize: '11px', color: '#059669', marginLeft: '4px' },
              intentSegs: [{ style: { background: '#3b82f6', flex: 2 } }, { style: { background: '#10b981', flex: 1 } }],
              etVal: this.fmt(Math.round(totVol * 0.15)), etDiff: '+12%', etDiffStyle: { fontSize: '11px', color: '#059669', marginLeft: '4px' },
              avgPos: avg, posArrow: '▲', posArrowStyle: { fontSize: '11px', color: '#059669', marginLeft: '4px' },
              totVol: this.fmt(totVol), open: isOpen,
              chevStyle: { display: 'inline-block', width: '16px', fontWeight: 700, color: '#94a3b8', transform: isOpen ? 'rotate(90deg)' : 'none', transition: 'transform 0.15s' },
              onToggle: () => {
                const next = isOpen ? openPages.filter(u => u !== p.url) : openPages.concat([p.url]);
                this.setState({ ptOpenPages: next });
              },
              onLinkClick: (e) => e.stopPropagation(),
              kws: p.kws.map(k => ({
                kw: k.kw, intentLabel: k.intent || 'Info', intentStyle: k.intentStyle || { padding: '2px 6px', borderRadius: '4px', fontSize: '11px', background: '#eef2ff', color: '#4338ca' },
                etVal: this.fmt(Math.round((parseInt((k.volume || '0').replace(/,/g, ''), 10) || 0) * 0.15)), etDiff: '', etDiffStyle: {},
                pos: k.pos, posStyle: k.posBadgeStyle || this.posBadge(k.pos), posArrowStyle: {}, vol: k.volume
              }))
            };
          })
        };

        vals.ptSerpOpen = !!s.ptSerpKw;
        vals.ptSerpCloseFn = () => this.setState({ ptSerpKw: null });
        if (s.ptSerpKw) {
          const kw = s.ptSerpKw;
          const pool = [vals.ptWs.domain].concat(vals.pt.compDomains || []).concat(['healthline.com', 'yelp.com', 'reddit.com', 'webmd.com', 'wikipedia.org', 'medicalnewstoday.com']);
          const serpTitles = ['Best ' + kw + ' — Top Rated Providers', 'What to know about ' + kw, kw + ': Cost & Options Explained', 'Reviews: ' + kw, kw + ' near you — Compare', 'A Complete Guide to ' + kw, 'Top 10 for ' + kw];
          const serpRows = [];
          for (let i = 0; i < 10; i++) {
            const dom = pool[i % pool.length];
            const isYou = dom === vals.ptWs.domain;
            serpRows.push({ n: i + 1, domain: dom, isYou, url: dom + '/' + kw.replace(/\s+/g, '-'), title: serpTitles[i % serpTitles.length], rowStyle: { display: 'flex', gap: '12px', padding: '12px 0', borderBottom: '1px solid #f1f5f9', background: isYou ? '#fafaff' : 'transparent' }, badgeStyle: { minWidth: '22px', fontSize: '13px', fontWeight: 700, color: isYou ? '#4f46e5' : '#94a3b8' } });
          }
          vals.ptSerp = { kw, href: 'https://www.google.com/search?q=' + encodeURIComponent(kw), rows: serpRows };
        } else {
          vals.ptSerp = { kw: '', href: '', rows: [] };
        }
      }

    }


        /* ============ BACKLINKS ============ */
    if (tab === 'backlinks') {
      vals.showBacklinks = true;
      const sum = data.summary;
      const setup = !data || !sum || sum.state === 'setup' || (sum.backlinks === 0 && (!data.links || !data.links.length));

      if (setup) {
        vals.bl = {
          setup: true,
          tabs: [], isOverview: false, isLinks: false, isRefDom: false, isAnchors: false, isGap: false,
          lastUpdated: '', chartBars: [], chartLabels: [], typeArcs: [], typeLegend: [],
          asBuckets: [], topAnchors: [], topRefDomains: [], allRefDomains: [],
          rows: [], statusFilters: [], followFilters: [], allAnchors: [],
          gapCols: [], gapRows: [], gapOnly: false,
          gapBtnBorder: '#e2e8f0', gapBtnBg: 'white', gapBtnColor: '#64748b'
        };
        return vals;
      }

      const links = data.links;
      const asColorOf = as => as >= 60 ? '#059669' : as >= 40 ? '#0891b2' : as >= 20 ? '#d97706' : '#94a3b8';
      const asBgOf = as => as >= 60 ? '#ecfdf5' : as >= 40 ? '#ecfeff' : as >= 20 ? '#fffbeb' : '#f1f5f9';
      const spamColorOf = sp => sp >= 30 ? '#dc2626' : sp >= 10 ? '#d97706' : '#059669';
      const asChip = as => ({ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', minWidth: '26px', padding: '2px 6px', borderRadius: '5px', fontSize: '12px', fontWeight: 600, color: asColorOf(as), background: asBgOf(as) });
      const shortN = n => n >= 1000 ? (n / 1000).toFixed(n >= 10000 ? 0 : 1) + 'K' : ('' + n);

      const bl = {};
      bl.lastUpdated = sum.lastUpdated;
      // sub-tabs
      const tabDef = [['overview', 'Overview'], ['backlinks', 'Backlinks'], ['refdomains', 'Referring Domains'], ['anchors', 'Anchors'], ['linkgap', 'Link Gap']];
      bl.tabs = tabDef.map(([k, label]) => {
        const active = s.blTab === k;
        return { label, click: () => { this.setState({ blTab: k }); this.pushNav({ blTab: k }); }, style: { padding: '12px 16px', fontSize: '14px', cursor: 'pointer', color: active ? '#4f46e5' : '#64748b', fontWeight: active ? 600 : 400, borderBottom: '2px solid ' + (active ? '#4f46e5' : 'transparent') } };
      });
      bl.isOverview = s.blTab === 'overview';
      bl.isLinks = s.blTab === 'backlinks';
      bl.isRefDom = s.blTab === 'refdomains';
      bl.isAnchors = s.blTab === 'anchors';
      bl.isGap = s.blTab === 'linkgap';

      // KPIs
      bl.as = sum.authorityScore; bl.asColor = asColorOf(sum.authorityScore);
      bl.asDash = (sum.authorityScore / 100 * 188.5).toFixed(1) + ' 188.5'; bl.asDelta = sum.asDelta;
      bl.refDomainsFmt = this.fmt(sum.refDomains); bl.newRdMonth = sum.newRdMonth;
      bl.backlinksFmt = this.fmt(sum.backlinks); bl.backlinksShort = shortN(sum.backlinks);
      bl.dofollowPct = sum.dofollowPct; bl.brokenFmt = this.fmt(sum.broken);
      bl.spamScore = sum.spamScore; bl.spamColor = spamColorOf(sum.spamScore);

      // new/lost chart
      const months = data.months;
      const maxMonth = Math.max(...months.map(m => Math.max(m.nw, m.lost)));
      const barW = 640 / months.length;
      bl.chartBars = months.map((m, i) => ({ x: (i * barW + 2).toFixed(1), w: (barW - 4).toFixed(1), newH: ((m.nw / maxMonth) * 82).toFixed(1), newY: (90 - (m.nw / maxMonth) * 82).toFixed(1), lostH: ((m.lost / maxMonth) * 82).toFixed(1) }));
      bl.chartLabels = months.filter((m, i) => i % 4 === 0).map(m => m.label);

      // types donut
      let acc = 0;
      bl.typeArcs = data.types.map(t => { const arc = { color: t.color, dash: t.pct + ' ' + (100 - t.pct), offset: (100 - acc) % 100 }; acc += t.pct; return arc; });
      bl.typeLegend = data.types.map(t => ({ label: t.label, color: t.color, pct: t.pct }));

      // AS buckets
      const maxBucket = Math.max(...data.asBuckets.map(b => b.count));
      bl.asBuckets = data.asBuckets.map(b => ({ label: b.label, color: b.color, countFmt: this.fmt(b.count), pct: Math.round((b.count / maxBucket) * 100) }));

      // top anchors
      const maxAnchor = Math.max(...data.anchors.map(a => a.backlinks));
      bl.topAnchors = data.anchors.slice(0, 6).map(a => ({ anchor: a.anchor, pct: Math.round((a.backlinks / maxAnchor) * 100) }));

      // referring domains
      const refRow = x => ({ domain: x.domain, flag: x.flag, as: x.rank, asStyle: asChip(x.rank), backlinksFmt: this.fmt(x.backlinks), linksToUs: x.linksToUs, follow: x.follow ? 'Dofollow' : 'Nofollow', followColor: x.follow ? '#059669' : '#94a3b8', firstSeen: x.firstSeen, isNew: x.isNew, category: x.category });
      bl.topRefDomains = data.refDomains.slice(0, 8).map(refRow);
      bl.allRefDomains = data.refDomains.map(refRow);

      // backlinks table (derived from referring domains, deterministic)
      const paths = ['/blog/top-providers', '/reviews/best-services', '/guides/pricing', '/news/industry-2026', '/resources/how-it-works', '/directory/listings'];
      const titles = ['Top Providers in 2026', 'Best Services Reviewed', 'Complete Pricing Guide', 'Industry Trends 2026', 'How It Works, Explained', 'Local Directory Listing'];
      const statusPool = [];
      data.refDomains.forEach((rd, i) => {
        const cnt = 1 + (i % 3);
        for (let j = 0; j < cnt; j++) {
          const rr = this.blHash('blk:' + s.projectId + rd.domain + j);
          const anchorsL = [rd.domain.split('.')[0], (data.project ? '' : '') + 'services', project.domain, 'read the full review', 'here', 'learn more'];
          const dofollow = rr() > (1 - sum.dofollowPct / 100);
          const isNew = rr() > 0.8, isLost = !isNew && rr() > 0.9, isBroken = rr() > 0.94;
          statusPool.push({ domain: rd.domain, flag: rd.flag, pageTitle: titles[Math.floor(rr() * titles.length)], urlFrom: rd.domain + paths[Math.floor(rr() * paths.length)], anchor: anchorsL[Math.floor(rr() * anchorsL.length)], urlTo: project.domain + ['/', '/services', '/pricing', '/about'][Math.floor(rr() * 4)], domainRank: rd.rank, spam: rd.spam, dofollow, firstSeen: rd.firstSeen, isNew, isLost, isBroken });
        }
      });
      let blr = statusPool;
      if (s.blFilter === 'new') blr = blr.filter(x => x.isNew);
      else if (s.blFilter === 'lost') blr = blr.filter(x => x.isLost);
      else if (s.blFilter === 'broken') blr = blr.filter(x => x.isBroken);
      if (s.blFollow === 'dofollow') blr = blr.filter(x => x.dofollow);
      else if (s.blFollow === 'nofollow') blr = blr.filter(x => !x.dofollow);
      bl.rowCount = this.fmt(Math.min(blr.length, 60));
      bl.rows = blr.slice(0, 60).map(x => {
        const badges = [];
        if (x.isNew) badges.push({ label: 'NEW', color: '#059669', bg: '#ecfdf5' });
        if (x.isLost) badges.push({ label: 'LOST', color: '#dc2626', bg: '#fef2f2' });
        if (x.isBroken) badges.push({ label: 'BROKEN', color: '#b45309', bg: '#fffbeb' });
        return { flag: x.flag, pageTitle: x.pageTitle, urlFrom: x.urlFrom, anchor: x.anchor, urlTo: x.urlTo, domainRank: x.domainRank, asStyle: asChip(x.domainRank), spam: x.spam, spamColor: spamColorOf(x.spam), follow: x.dofollow ? 'Dofollow' : 'Nofollow', followColor: x.dofollow ? '#059669' : '#94a3b8', firstSeen: x.firstSeen, badges };
      });
      const mkF = (val, cur, key, label) => { const active = cur === val; return { label, click: () => { this.setState({ [key]: val }); this.pushNav(); }, style: { padding: '8px 14px', cursor: 'pointer', background: active ? '#eef2ff' : 'white', color: active ? '#4338ca' : '#64748b', fontWeight: active ? 600 : 400, borderLeft: '1px solid #e2e8f0' } }; };
      bl.statusFilters = [mkF('all', s.blFilter, 'blFilter', 'All'), mkF('new', s.blFilter, 'blFilter', 'New'), mkF('lost', s.blFilter, 'blFilter', 'Lost'), mkF('broken', s.blFilter, 'blFilter', 'Broken')];
      bl.statusFilters[0].style.borderLeft = 'none';
      bl.followFilters = [mkF('all', s.blFollow, 'blFollow', 'All links'), mkF('dofollow', s.blFollow, 'blFollow', 'Dofollow'), mkF('nofollow', s.blFollow, 'blFollow', 'Nofollow')];
      bl.followFilters[0].style.borderLeft = 'none';

      // anchors
      const typeColors = { Branded: ['#4338ca', '#eef2ff'], URL: ['#0891b2', '#ecfeff'], Keyword: ['#059669', '#ecfdf5'], Generic: ['#64748b', '#f1f5f9'], Empty: ['#94a3b8', '#f8fafc'] };
      bl.allAnchors = data.anchors.map(a => ({ anchor: a.anchor, type: a.type, typeColor: (typeColors[a.type] || typeColors.Generic)[0], typeBg: (typeColors[a.type] || typeColors.Generic)[1], backlinksFmt: this.fmt(a.backlinks), refDomainsFmt: this.fmt(a.refDomains), dofollowPct: a.dofollowPct }));

      // link gap
      const gapCols = [{ name: 'You', color: '#4f46e5' }, ...data.competitors.map(c => ({ name: c, color: '#64748b' }))];
      bl.gapCols = gapCols;
      let gapSource = data.gapDomains;
      if (s.gapOnly) gapSource = gapSource.filter(g => !g.you && g.comp.filter(Boolean).length >= 2);
      bl.gapRows = gapSource.slice().sort((a, b) => b.rank - a.rank).map(g => {
        const compCount = g.comp.filter(Boolean).length;
        const cells = [{ linked: g.you, missing: !g.you, color: '#4f46e5' }, ...g.comp.map(c => ({ linked: c, missing: !c, color: '#22c55e' }))];
        let opp = 'Low', oc = '#64748b', ob = '#f1f5f9';
        if (!g.you && compCount >= 3 && g.rank >= 50) { opp = 'High'; oc = '#059669'; ob = '#ecfdf5'; }
        else if (!g.you && compCount >= 2) { opp = 'Medium'; oc = '#d97706'; ob = '#fffbeb'; }
        else if (g.you) { opp = 'Have it'; oc = '#4f46e5'; ob = '#eef2ff'; }
        return { domain: g.domain, flag: g.flag, as: g.rank, asStyle: asChip(g.rank), cells, opp, oppColor: oc, oppBg: ob };
      });
      bl.gapOnly = s.gapOnly;
      bl.gapBtnBorder = s.gapOnly ? '#c7d2fe' : '#e2e8f0';
      bl.gapBtnBg = s.gapOnly ? '#eef2ff' : 'white';
      bl.gapBtnColor = s.gapOnly ? '#4338ca' : '#64748b';

      vals.bl = bl;
    }


        /* ============ OFF-SITE SEO ============ */
    if (tab === 'offsite') {
      vals.showOffsite = true;
      const t = data.totals, pv = data.prev;
      const pctD = (a, b) => (b ? Math.round(((a - b) / b) * 100) : null);
      const chip = d => {
        if (d == null || !isFinite(d)) return { has: false, label: '', style: {} };
        const good = d >= 0;
        return { has: true, label: (d > 0 ? '+' : '') + d + '%', style: { fontSize: '11px', fontWeight: 600, padding: '2px 6px', borderRadius: '4px', color: good ? '#059669' : '#e11d48', background: good ? '#ecfdf5' : '#fff1f2' } };
      };
      const kpiCard = (label, value, c, note) => ({ label, value, hasChip: c.has, chipLabel: c.label, chipStyle: c.style, note });
      const off = {};
      const syncSetup = !data || !data.syncMeta || data.syncMeta.state === 'setup' || (data.totals && data.totals.sessions === 0 && (!data.referrers || !data.referrers.length));
      if (syncSetup) {
        vals.off = { setup: true };
        return vals;
      }
      off.cadence = data.syncMeta.cadence;
      off.tokens = (data.syncMeta.ga4_tokens_used + ' / ' + this.fmt(data.syncMeta.ga4_tokens_limit) + ' GA4 tokens');
      off.tokensEmpty = false;
      off.rangeLabel = s.range === '7d' ? 'last 7 days' : s.range === '90d' ? 'last 90 days' : 'last 30 days';
      off.kpis = [
        kpiCard('Off-site sessions', this.fmt(t.sessions), chip(pctD(t.sessions, pv.sessions)), 'vs. previous period'),
        kpiCard('Engagement rate', t.engagementRate + '%', chip(null), this.fmt(t.engagedSessions) + ' engaged'),
        kpiCard('Key events', this.fmt(Math.round(t.keyEvents)), chip(pctD(t.keyEvents, pv.keyEvents)), 'attributed conversions'),
        kpiCard('Attributed revenue', this.money(t.revenue), chip(pctD(t.revenue, pv.revenue)), 'GA4 totalRevenue'),
        kpiCard('Referring domains', String(t.referringDomains), chip(null), 'sites sending traffic')
      ];

      /* trend */
      const tr = data.trend, W = 600, H = 220, P = 8;
      const maxV = Math.max.apply(null, tr.map(d => d.sessions).concat([1]));
      const xs = i => (tr.length > 1 ? P + i * ((W - 2 * P) / (tr.length - 1)) : W / 2);
      const yOf = v => H - P - (v / maxV) * (H - 2 * P);
      const pts = k => tr.map((d, i) => xs(i).toFixed(1) + ',' + yOf(d[k]).toFixed(1)).join(' ');
      off.sessPts = pts('sessions');
      off.engPts = pts('engagedSessions');
      off.area = tr.length ? 'M' + xs(0).toFixed(1) + ',' + (H - P) + ' L' + off.sessPts.split(' ').join(' L') + ' L' + xs(tr.length - 1).toFixed(1) + ',' + (H - P) + ' Z' : '';
      off.trendStart = tr.length ? tr[0].date : '';
      off.trendEnd = tr.length ? tr[tr.length - 1].date : '';

      /* channel mix */
      const chMax = Math.max.apply(null, data.channels.map(c => c.sessions).concat([1]));
      const chTotal = data.channels.reduce((a, c) => a + c.sessions, 0) || 1;
      const chColors = { 'Organic Search': '#94a3b8', 'Direct': '#cbd5e1', 'Referral': '#4f46e5', 'Organic Social': '#0a66c2', 'Organic Video': '#dc2626', 'Email': '#a1a1aa' };
      off.channels = data.channels.map(c => {
        const col = chColors[c.channel] || '#94a3b8';
        return {
          channel: c.channel, sessFmt: this.fmt(c.sessions),
          pctLabel: Math.round(c.sessions / chTotal * 100) + '%',
          labelColor: c.offsite ? '#0f172a' : '#64748b', labelWeight: c.offsite ? 600 : 400,
          dotStyle: { width: '8px', height: '8px', borderRadius: '2px', background: col, flexShrink: 0 },
          barStyle: { height: '100%', width: Math.max(2, Math.round(c.sessions / chMax * 100)) + '%', background: col, borderRadius: '9999px', opacity: c.offsite ? 1 : 0.5 }
        };
      });
      const offCh = data.channels.filter(c => c.offsite);
      const offSess = offCh.reduce((a, c) => a + c.sessions, 0);
      off.offShareLabel = Math.round(offSess / chTotal * 100) + '%';
      off.offKeyEvents = this.fmt(Math.round(offCh.reduce((a, c) => a + c.keyEvents, 0)));

      /* LinkedIn spotlight */
      const li = data.social.find(x => x.platform === 'LinkedIn') || { impressions: 0, sessions: 0, keyEvents: 0, revenue: 0 };
      const liConnected = !!(data.connectors && data.connectors.linkedin);
      off.li = {
        impressions: liConnected ? this.fmt(li.impressions || 0) : '—', sessions: this.fmt(li.sessions),
        ctr: liConnected && li.impressions ? +(li.sessions / li.impressions * 100).toFixed(1) + '%' : '—',
        keyEvents: this.fmt(Math.round(li.keyEvents)), revenue: this.money(li.revenue),
        connected: liConnected,
        badgeLabel: liConnected ? 'Connected' : 'Not connected',
        badgeStyle: liConnected
          ? { marginLeft: 'auto', fontSize: '10px', fontWeight: 600, color: '#059669', background: '#ecfdf5', padding: '3px 8px', borderRadius: '9999px' }
          : { marginLeft: 'auto', fontSize: '10px', fontWeight: 600, color: '#4f46e5', background: '#eef2ff', padding: '3px 8px', borderRadius: '9999px', cursor: 'pointer', textDecoration: 'underline' },
        subtitle: liConnected ? 'Connector live · impressions + click-throughs' : 'Connector not set up yet (click badge to connect in Settings)',
        imprCaption: liConnected ? 'from LinkedIn API' : 'connector needed'
      };

      /* social table */
      const socColors = { 'LinkedIn': '#0a66c2', 'Reddit': '#ff4500', 'YouTube': '#dc2626', 'X (Twitter)': '#0f172a', 'Facebook': '#1877f2', 'Instagram': '#c13584' };
      off.social = data.social.map(r => ({
        platform: r.platform, source: r.source, channel: r.channel,
        connected: r.connected, notConnected: !r.connected,
        imprFmt: r.connected && r.impressions != null ? this.fmt(r.impressions) : '—',
        sessFmt: this.fmt(r.sessions), engFmt: Math.round(r.engagedRate * 100) + '%',
        keyFmt: this.fmt(Math.round(r.keyEvents)), revFmt: this.money(r.revenue),
        badge: r.platform.slice(0, 1),
        badgeStyle: { width: '26px', height: '26px', borderRadius: '6px', background: socColors[r.platform] || '#64748b', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '13px', fontWeight: 700, flexShrink: 0 }
      }));

      /* referring domains (sortable) */
      const refRows = this.sortRows(data.referrers.slice(), s.offSort);
      off.sort = { sessions: this.mkSortHandler('offSort', 'sessions'), keyEvents: this.mkSortHandler('offSort', 'keyEvents'), revenue: this.mkSortHandler('offSort', 'revenue') };
      off.arrow = { sessions: this.arrow(s.offSort, 'sessions'), keyEvents: this.arrow(s.offSort, 'keyEvents'), revenue: this.arrow(s.offSort, 'revenue') };
      off.referrers = refRows.map(r => ({
        domain: r.domain, rank: r.rank, tracked: r.tracked, canTrack: !r.tracked,
        rankStyle: { fontWeight: 600, color: r.rank >= 70 ? '#059669' : r.rank >= 40 ? '#2563eb' : '#64748b' },
        sessFmt: this.fmt(r.sessions), engFmt: Math.round(r.engagedRate * 100) + '%',
        keyFmt: this.fmt(Math.round(r.keyEvents)), revFmt: this.money(r.revenue),
        href: 'https://' + r.domain,
        onTrack: () => this.notify('"' + r.domain + '" flagged — added to backlink tracking on next sync')
      }));

      /* landing pages */
      off.landing = data.landingPages.map(r => ({
        url: r.url, topSource: r.topSource,
        sessFmt: this.fmt(r.sessions), engFmt: Math.round(r.engagedRate * 100) + '%',
        keyFmt: this.fmt(Math.round(r.keyEvents))
      }));

      vals.off = off;
    }


        /* ============ SITE AUDIT ============ */
    if (tab === 'pages') {
      vals.showPages = true;
      const auSetup = !data || data.score == null || (typeof data.score === 'object' && data.score.state === 'setup') || (data.crawl && (data.crawl.status === 'never' || data.crawl.pagesCrawled === 0));

      if (auSetup) {
        vals.au = {
          setup: true,
          subTabs: [], showOverview: false, showIssues: false, showCrawled: false,
          showCompare: false, showProgress: false, showStats: false,
          domain: project.domain, crawlDate: '', pagesCrawled: 0, crawlDuration: '', userAgent: '',
          barSegs: [], breakRows: [], sevTotals: [], cats: [], vitals: [], domChecks: [], topIssues: [],
          sevFilters: [], catFilters: [], noIssues: true, issueRows: [], search: '',
          tableTabStyle: {}, treeTabStyle: {}, showTable: false, showTree: false,
          pgSearch: '', pageRows: [], pageRowCount: '', treeRows: [],
          statKpis: [], statCharts: [],
          cmpOptions: [], cmpOptions2: [], cmpFilters: [], cmpKpis: [], cmpEmpty: true, cmpRows: [],
          cmpA: '', cmpB: '', cmpALabel: '', cmpBLabel: '',
          progToggles: [], progLines: [], progFrom: '', progTo: '', progRows: []
        };
        return vals;
      }

      const SEVC = { error: '#dc2626', warning: '#d97706', notice: '#2563eb' };
      const sevRank = { error: 0, warning: 1, notice: 2 };
      const scoreColor = v => v >= 80 ? '#059669' : v >= 60 ? '#d97706' : '#dc2626';
      const scoreChip = v => ({ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', minWidth: '34px', height: '22px', padding: '0 6px', borderRadius: '4px', fontSize: '12px', fontWeight: 700, background: v >= 80 ? '#dcfce7' : v >= 60 ? '#fef3c7' : '#fee2e2', color: v >= 80 ? '#15803d' : v >= 60 ? '#b45309' : '#b91c1c' });
      const dot = c => ({ width: '9px', height: '9px', borderRadius: '50%', background: c, flexShrink: 0 });
      const sub = s.auSub;
      const totalIssues = data.totals.errors + data.totals.warnings + data.totals.notices;
      const goSub = v => { this.setState({ auSub: v }); this.pushNav({ auSub: v }); };
      const subBase = { padding: '10px 16px', fontSize: '13px', fontWeight: 600, cursor: 'pointer', color: '#64748b', borderBottom: '2px solid transparent', marginBottom: '-1px' };
      const activeChecks = data.checks.filter(c => !c.hidden && c.count > 0);
      const hiddenChecks = data.checks.filter(c => c.hidden);
      const crawlDate = data.crawl.startedAt;
      const au = {
        domain: project.domain,
        crawlDate, pagesCrawled: data.crawl.pagesCrawled, crawlDuration: data.crawl.duration, userAgent: data.crawl.userAgent,
        subTabs: [['overview', 'Overview'], ['issues', 'Issues (' + this.fmt(totalIssues) + ')'], ['crawled', 'Crawled Pages (' + data.crawl.pagesCrawled + ')'], ['stats', 'Statistics'], ['compare', 'Compare Crawls'], ['progress', 'Progress']].map(t => ({
          label: t[1],
          style: sub === t[0] ? Object.assign({}, subBase, { color: '#4f46e5', borderBottom: '2px solid #4f46e5' }) : subBase,
          click: () => goSub(t[0])
        })),
        showOverview: sub === 'overview', showIssues: sub === 'issues', showCrawled: sub === 'crawled',
        showCompare: sub === 'compare', showProgress: sub === 'progress', showStats: sub === 'stats',
        score: data.score, search: s.auSearch, pgSearch: s.auPgSearch
      };

      if (sub === 'overview') {
        const sc = scoreColor(data.score);
        au.gaugeOuter = { width: '128px', height: '128px', borderRadius: '50%', background: 'conic-gradient(' + sc + ' ' + (data.score * 3.6) + 'deg, #f1f5f9 0deg)', display: 'flex', alignItems: 'center', justifyContent: 'center' };
        au.gaugeNum = { fontSize: '34px', fontWeight: 800, lineHeight: 1, color: sc };
        au.scoreWord = data.score >= 80 ? 'Good' : data.score >= 60 ? 'Needs work' : 'Poor';
        au.scoreWordStyle = { fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: sc };
        const bd = data.breakdown;
        const bdRows = [
          ['healthy', 'Healthy', '#059669'], ['withIssues', 'With issues', '#d97706'],
          ['broken', 'Broken (4xx/5xx)', '#dc2626'], ['redirected', 'Redirected', '#8b5cf6'], ['blocked', 'Blocked', '#64748b']
        ];
        au.barSegs = bdRows.filter(r => bd[r[0]] > 0).map(r => ({ style: { flex: String(bd[r[0]]), background: r[2] } }));
        au.breakRows = bdRows.map(r => ({
          label: r[1], count: bd[r[0]], dot: dot(r[2]),
          click: () => goSub('crawled')
        }));
        const sevCardBase = { display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', borderRadius: '10px', cursor: 'pointer', flex: 1 };
        au.sevTotals = [
          ['error', 'Errors', data.totals.errors, '#fef2f2', '#b91c1c'],
          ['warning', 'Warnings', data.totals.warnings, '#fffbeb', '#b45309'],
          ['notice', 'Notices', data.totals.notices, '#eff6ff', '#1d4ed8']
        ].map(v => ({
          label: v[1], count: this.fmt(v[2]),
          style: Object.assign({}, sevCardBase, { background: v[3], color: v[4] }),
          click: () => { this.setState({ auSub: 'issues', auSev: v[0], auCat: 'all' }); this.pushNav({ auSub: 'issues' }); }
        }));
        au.cats = Object.entries(data.catScore).map(([name, sc2]) => {
          const failing = activeChecks.filter(c => c.category === name).length;
          return {
            name, score: sc2,
            scoreStyle: { fontSize: '24px', fontWeight: 800, lineHeight: 1, color: scoreColor(sc2) },
            issueLine: failing ? failing + ' check' + (failing === 1 ? '' : 's') + ' failing' : 'All checks passed',
            click: () => { this.setState({ auSub: 'issues', auCat: name, auSev: 'all' }); this.pushNav({ auSub: 'issues' }); }
          };
        });
        const vitalVerdict = (m) => m.p75 <= m.good ? ['Good', '#dcfce7', '#15803d'] : m.p75 <= m.poor ? ['Needs work', '#fef3c7', '#b45309'] : ['Poor', '#fee2e2', '#b91c1c'];
        au.vitals = [
          ['LCP', 'Largest Contentful Paint', data.cwv.lcp],
          ['TBT', 'Total Blocking Time', data.cwv.tbt],
          ['CLS', 'Cumulative Layout Shift', data.cwv.cls]
        ].map(v => {
          const m = v[2], vd = vitalVerdict(m);
          const b = m.buckets, tot = Math.max(1, b.good + b.mid + b.poor);
          return {
            name: v[0], desc: v[1], p75: m.p75, unit: m.unit,
            verdict: vd[0], badge: { fontSize: '11px', fontWeight: 700, padding: '2px 9px', borderRadius: '999px', background: vd[1], color: vd[2] },
            numStyle: { fontSize: '30px', fontWeight: 800, marginTop: '10px', color: vd[2] },
            segs: [
              { style: { flex: String(b.good / tot || 0.001), background: '#059669' } },
              { style: { flex: String(b.mid / tot || 0.001), background: '#d97706' } },
              { style: { flex: String(b.poor / tot || 0.001), background: '#dc2626' } }
            ],
            goodLbl: 'Good ' + b.good, midLbl: 'Needs impr. ' + b.mid, poorLbl: 'Poor ' + b.poor
          };
        });
        au.domChecks = data.domainChecks.map(d => ({
          label: d.label, detail: d.detail, mark: d.ok ? '✓' : '!',
          icon: { display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '20px', height: '20px', borderRadius: '50%', fontSize: '12px', fontWeight: 700, background: d.ok ? '#dcfce7' : '#fef3c7', color: d.ok ? '#15803d' : '#b45309', flexShrink: 0 }
        }));
        au.topIssues = activeChecks.slice().sort((a, b2) => sevRank[a.severity] - sevRank[b2.severity] || b2.count - a.count).slice(0, 6).map(c => ({
          title: c.title, category: c.category, count: this.fmt(c.count),
          dot: dot(SEVC[c.severity]),
          countStyle: { fontSize: '12px', fontWeight: 700, color: SEVC[c.severity], minWidth: '28px', textAlign: 'right' },
          click: () => { this.setState({ auSub: 'issues', auSev: 'all', auCat: 'all', auOpen: c.id, auSearch: '' }); this.pushNav({ auSub: 'issues' }); }
        }));
      }

      if (sub === 'issues') {
        const fBase = { padding: '5px 12px', fontSize: '12px', fontWeight: 500, borderRadius: '6px', cursor: 'pointer', color: '#64748b' };
        const fActive = Object.assign({}, fBase, { background: 'white', color: '#0f172a', boxShadow: '0 1px 2px rgba(0,0,0,0.05)' });
        au.sevFilters = [
          ['all', 'All (' + activeChecks.length + ')'],
          ['error', 'Errors (' + activeChecks.filter(c => c.severity === 'error').length + ')'],
          ['warning', 'Warnings (' + activeChecks.filter(c => c.severity === 'warning').length + ')'],
          ['notice', 'Notices (' + activeChecks.filter(c => c.severity === 'notice').length + ')'],
          ['hidden', 'Hidden (' + hiddenChecks.length + ')']
        ].map(f => ({ label: f[1], style: s.auSev === f[0] ? fActive : fBase, click: () => this.setState({ auSev: f[0], auOpen: null }) }));
        const chipBase = { padding: '5px 11px', fontSize: '12px', fontWeight: 500, borderRadius: '999px', cursor: 'pointer', color: '#64748b', border: '1px solid #e2e8f0', background: 'white' };
        const chipActive = Object.assign({}, chipBase, { borderColor: '#4f46e5', color: '#4f46e5', background: '#eef2ff' });
        au.catFilters = ['all'].concat(Object.keys(data.catScore)).map(cat => ({
          label: cat === 'all' ? 'All categories' : cat,
          style: s.auCat === cat ? chipActive : chipBase,
          click: () => this.setState({ auCat: cat, auOpen: null })
        }));
        let list = s.auSev === 'hidden' ? hiddenChecks : activeChecks.filter(c => s.auSev === 'all' || c.severity === s.auSev);
        if (s.auCat !== 'all') list = list.filter(c => c.category === s.auCat);
        if (s.auSearch) { const q = s.auSearch.toLowerCase(); list = list.filter(c => c.title.toLowerCase().includes(q) || c.category.toLowerCase().includes(q)); }
        list = list.slice().sort((a, b2) => sevRank[a.severity] - sevRank[b2.severity] || b2.count - a.count);
        au.noIssues = list.length === 0;
        const statusOf = pg2 => pg2 ? (pg2.statusCode + (pg2.kind === 'gone' ? ' · broken' : pg2.kind === 'redirect' ? ' · redirect' : '')) : '200';
        const pgByUrl = {};
        data.crawledPages.forEach(pg2 => { pgByUrl[pg2.url] = pg2; });
        au.issueRows = list.map(c => {
          const open = s.auOpen === c.id;
          const shown = c.pages.slice(0, 8);
          return {
            title: c.title, category: c.category, open, howToFix: c.howToFix,
            dot: dot(c.hidden ? '#cbd5e1' : SEVC[c.severity]),
            rowStyle: { display: 'flex', alignItems: 'center', gap: '12px', padding: '13px 20px', cursor: 'pointer', opacity: c.hidden ? 0.6 : 1 },
            countLabel: this.fmt(c.count) + ' page' + (c.count === 1 ? '' : 's'),
            countStyle: { fontSize: '12px', fontWeight: 700, color: c.hidden ? '#94a3b8' : SEVC[c.severity], minWidth: '60px', textAlign: 'right' },
            chev: { color: '#cbd5e1', fontSize: '18px', transform: open ? 'rotate(90deg)' : 'none', transition: 'transform 0.15s ease' },
            toggle: () => this.setState({ auOpen: open ? null : c.id }),
            hasPages: c.pages.length > 0,
            pages: shown.map(u => { const pg2 = pgByUrl[u]; return { url: u, score: pg2 ? pg2.score : '—', scoreStyle: scoreChip(pg2 ? pg2.score : 0), status: statusOf(pg2) }; }),
            more: c.pages.length > 8, moreLabel: '+ ' + (c.pages.length - 8) + ' more pages — export for the full list',
            exportPages: () => this.downloadCsv(project.domain + '-' + c.id + '.csv', [['url', 'url']], c.pages.map(u => ({ url: u }))),
            hide: () => this.toggleAuditCheck(c.id),
            hideLabel: c.hidden ? 'Restore check' : 'Hide this check'
          };
        });
      }

      if (sub === 'crawled') {
        const vBase = { padding: '5px 12px', fontSize: '12px', fontWeight: 500, borderRadius: '6px', cursor: 'pointer', color: '#64748b' };
        const vActive = Object.assign({}, vBase, { background: 'white', color: '#0f172a', boxShadow: '0 1px 2px rgba(0,0,0,0.05)' });
        au.tableTabStyle = s.auView === 'table' ? vActive : vBase;
        au.treeTabStyle = s.auView === 'tree' ? vActive : vBase;
        au.showTable = s.auView === 'table';
        au.showTree = s.auView === 'tree';
        if (s.auView === 'table') {
          let rows = data.crawledPages.map(pg2 => Object.assign({}, pg2, { issues: pg2.errors * 10000 + pg2.warnings * 100 + pg2.notices }));
          if (s.auPgSearch) { const q = s.auPgSearch.toLowerCase(); rows = rows.filter(r => r.url.toLowerCase().includes(q)); }
          rows = this.sortRows(rows, s.auPgSort);
          au.pageRows = rows.slice(0, 40).map(r => ({
            open: () => this.setState({ auPage: r.id }),
            url: r.url, score: r.score, scoreStyle: scoreChip(r.score),
            status: String(r.statusCode),
            statusStyle: { padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 700, background: r.statusCode === 200 ? '#dcfce7' : r.statusCode < 400 ? '#f3e8ff' : '#fee2e2', color: r.statusCode === 200 ? '#15803d' : r.statusCode < 400 ? '#7c3aed' : '#b91c1c' },
            issuesLabel: r.errors + 'E · ' + r.warnings + 'W · ' + r.notices + 'N',
            depth: r.depth, inLinks: r.inLinks,
            loadLabel: (r.loadTimeMs / 1000).toFixed(1) + ' s',
            loadStyle: { fontSize: '12.5px', fontWeight: 600, color: r.loadTimeMs > 3000 ? '#dc2626' : r.loadTimeMs > 1500 ? '#b45309' : '#64748b' }
          }));
          au.pageRowCount = rows.length > 40 ? 'Showing 40 of ' + rows.length + ' pages — refine with the URL filter or export the full list' : rows.length + ' page' + (rows.length === 1 ? '' : 's');
        } else {
          au.treeRows = data.structure.map(t => ({
            folder: t.folder, pages: t.pages, avgScore: t.avgScore, scoreStyle: scoreChip(t.avgScore),
            errors: t.errors, warnings: t.warnings, notices: t.notices
          }));
        }
      }
      if (sub === 'stats') {
        const cp = data.crawledPages;
        const ok = cp.filter(x => x.kind === 'ok');
        const avg = (arr, f) => arr.length ? arr.reduce((s2, x) => s2 + f(x), 0) / arr.length : 0;
        au.statKpis = [
          { label: 'Avg. page score', value: Math.round(avg(ok, x => x.score)), sub: 'across ' + ok.length + ' healthy pages' },
          { label: 'Avg. load time', value: (avg(ok, x => x.loadTimeMs) / 1000).toFixed(1) + ' s', sub: 'server response + render' },
          { label: 'Avg. internal links', value: Math.round(avg(ok, x => x.internalLinks)), sub: 'outgoing per page' },
          { label: 'Avg. word count', value: this.fmt(Math.round(avg(ok, x => x.wordCount))), sub: 'per indexable page' }
        ];
        const mkChart = (title, defs, colorAt) => {
          const total = Math.max(1, defs.reduce((s2, d) => s2 + d[1], 0));
          return {
            title,
            rows: defs.map((d, k) => {
              const col = colorAt(k, d);
              return {
                label: d[0], count: d[1], pct: Math.round((d[1] / total) * 100) + '%',
                dot: { width: '8px', height: '8px', borderRadius: '50%', background: col, flexShrink: 0 },
                bar: { height: '100%', width: Math.max(1, Math.round((d[1] / total) * 100)) + '%', background: col, borderRadius: '4px' }
              };
            })
          };
        };
        const seq = ['#4f46e5', '#818cf8', '#c7d2fe', '#e0e7ff'];
        const gwp = ['#059669', '#d97706', '#dc2626'];
        au.statCharts = [
          mkChart('HTTP status codes', [
            ['200 OK', cp.filter(x => x.statusCode === 200).length],
            ['3xx redirect', cp.filter(x => x.statusCode >= 300 && x.statusCode < 400).length],
            ['4xx client error', cp.filter(x => x.statusCode >= 400 && x.statusCode < 500).length],
            ['5xx server error', cp.filter(x => x.statusCode >= 500).length]
          ], (k) => k === 0 ? '#059669' : k === 1 ? '#8b5cf6' : k === 2 ? '#dc2626' : '#991b1b'),
          mkChart('Crawl depth', [
            ['1 click', cp.filter(x => x.depth <= 1).length],
            ['2 clicks', cp.filter(x => x.depth === 2).length],
            ['3 clicks', cp.filter(x => x.depth === 3).length],
            ['4+ clicks', cp.filter(x => x.depth >= 4).length]
          ], k => seq[k]),
          mkChart('Load time', [
            ['Fast (<1.5 s)', ok.filter(x => x.loadTimeMs < 1500).length],
            ['Average (1.5–3 s)', ok.filter(x => x.loadTimeMs >= 1500 && x.loadTimeMs <= 3000).length],
            ['Slow (>3 s)', ok.filter(x => x.loadTimeMs > 3000).length]
          ], k => gwp[k]),
          mkChart('Content length', [
            ['In-depth (1000+ words)', ok.filter(x => x.wordCount >= 1000).length],
            ['Standard (250–999)', ok.filter(x => x.wordCount >= 250 && x.wordCount < 1000).length],
            ['Thin (<250 words)', ok.filter(x => x.wordCount < 250).length]
          ], k => gwp[k])
        ];
      }

      if (sub === 'compare' && !data.snapshots.length) {
        // No audit history yet (nothing records historical crawl snapshots) -- show an empty
        // state instead of crashing on snaps[0].
        au.cmpOptions = []; au.cmpOptions2 = []; au.cmpFilters = []; au.cmpKpis = [];
        au.cmpRows = []; au.cmpEmpty = true; au.cmpA = ''; au.cmpB = '';
        au.cmpALabel = '—'; au.cmpBLabel = '—';
      } else if (sub === 'compare') {
        const snaps = data.snapshots;
        const iA = Math.min(s.auCmpA != null ? s.auCmpA : 0, snaps.length - 1);
        const iB = Math.min(s.auCmpB != null ? s.auCmpB : snaps.length - 1, snaps.length - 1);
        const A = snaps[iA], B = snaps[iB];
        au.cmpA = String(iA); au.cmpB = String(iB);
        const opt = snaps.map((sn, k) => ({ value: String(k), label: sn.date + (k === snaps.length - 1 ? ' (latest)' : '') }));
        au.cmpOptions = opt; au.cmpOptions2 = opt;
        au.cmpALabel = A.date; au.cmpBLabel = B.date;
        const deltaChip = (d, invert) => {
          const good = invert ? d > 0 : d < 0;
          const col = d === 0 ? ['#f1f5f9', '#64748b'] : good ? ['#dcfce7', '#15803d'] : ['#fee2e2', '#b91c1c'];
          return { padding: '2px 9px', borderRadius: '999px', fontSize: '12px', fontWeight: 700, background: col[0], color: col[1] };
        };
        const sgn = d => (d > 0 ? '+' : '') + d;
        au.cmpKpis = [
          ['Health score', B.score, A.score, true],
          ['Errors', B.errors, A.errors, false],
          ['Warnings', B.warnings, A.warnings, false],
          ['Pages crawled', B.pagesCrawled, A.pagesCrawled, true]
        ].map(k => ({
          label: k[0], now: this.fmt(k[1]), was: this.fmt(k[2]),
          delta: sgn(k[1] - k[2]), deltaStyle: deltaChip(k[1] - k[2], k[3])
        }));
        const fBase2 = { padding: '5px 12px', fontSize: '12px', fontWeight: 500, borderRadius: '6px', cursor: 'pointer', color: '#64748b' };
        const fActive2 = Object.assign({}, fBase2, { background: 'white', color: '#0f172a', boxShadow: '0 1px 2px rgba(0,0,0,0.05)' });
        let rows = data.checks.map(c => ({
          c, a: A.byCheck[c.id] || 0, b: B.byCheck[c.id] || 0
        })).map(r => Object.assign(r, { d: r.b - r.a }));
        const nFixed = rows.filter(r => r.d < 0).length, nNew = rows.filter(r => r.d > 0).length;
        au.cmpFilters = [['all', 'All changes (' + rows.filter(r => r.d !== 0).length + ')'], ['fixed', 'Fixed (' + nFixed + ')'], ['new', 'New (' + nNew + ')']].map(f => ({
          label: f[1], style: s.auCmpFilter === f[0] ? fActive2 : fBase2,
          click: () => this.setState({ auCmpFilter: f[0] })
        }));
        rows = rows.filter(r => s.auCmpFilter === 'fixed' ? r.d < 0 : s.auCmpFilter === 'new' ? r.d > 0 : r.d !== 0);
        rows.sort((x, y) => Math.abs(y.d) - Math.abs(x.d));
        au.cmpEmpty = rows.length === 0;
        au.cmpRows = rows.map(r => ({
          title: r.c.title, category: r.c.category,
          dot: dot(SEVC[r.c.severity]),
          a: r.a, b: r.b, delta: sgn(r.d) + (r.d < 0 ? ' fixed' : ' new'),
          deltaStyle: deltaChip(r.d, false)
        }));
      }

      if (sub === 'progress' && !data.snapshots.length) {
        // No audit history yet -- empty state instead of crashing on snaps[0].date.
        au.progToggles = []; au.progLines = []; au.progRows = [];
        au.progFrom = '—'; au.progTo = '—';
      } else if (sub === 'progress') {
        const snaps = data.snapshots;
        const prog = s.auProg;
        const METRICS = [
          ['score', 'Health score', '#4f46e5', sn => sn.score],
          ['errors', 'Errors', '#dc2626', sn => sn.errors],
          ['warnings', 'Warnings', '#d97706', sn => sn.warnings],
          ['notices', 'Notices', '#2563eb', sn => sn.notices],
          ['pages', 'Pages crawled', '#059669', sn => sn.pagesCrawled]
        ];
        const chipBase2 = { display: 'inline-flex', alignItems: 'center', gap: '7px', padding: '5px 11px', fontSize: '12px', fontWeight: 500, borderRadius: '999px', cursor: 'pointer', color: '#64748b', border: '1px solid #e2e8f0', background: 'white' };
        au.progToggles = METRICS.map(m => {
          const on = !!prog[m[0]];
          return {
            label: m[1],
            dot: { width: '8px', height: '8px', borderRadius: '50%', background: on ? m[2] : '#cbd5e1', flexShrink: 0 },
            style: on ? Object.assign({}, chipBase2, { borderColor: m[2], color: '#0f172a' }) : chipBase2,
            click: () => this.setState(st => ({ auProg: Object.assign({}, st.auProg, { [m[0]]: !st.auProg[m[0]] }) }))
          };
        });
        au.progLines = METRICS.filter(m => prog[m[0]]).map(m => {
          const vals2 = snaps.map(m[3]);
          const max = Math.max(1, ...vals2);
          const pts = vals2.map((v, k) => {
            const x = (k / (snaps.length - 1)) * 590 + 5;
            const y = 190 - (v / max) * 175;
            return x.toFixed(1) + ',' + y.toFixed(1);
          }).join(' ');
          return { pts, color: m[2] };
        });
        au.progFrom = snaps[0].date; au.progTo = snaps[snaps.length - 1].date;
        au.progRows = snaps.slice().reverse().map((sn, k) => ({
          date: sn.date, latest: k === 0,
          score: sn.score, scoreStyle: scoreChip(sn.score),
          errors: this.fmt(sn.errors), warnings: this.fmt(sn.warnings), notices: this.fmt(sn.notices),
          pages: sn.pagesCrawled
        }));
      }

      /* page detail drawer */
      if (s.auPage) {
        const pg3 = data.crawledPages.find(x => x.id === s.auPage);
        if (pg3) {
          const cwvDot = (v, good, poor) => ({ width: '8px', height: '8px', borderRadius: '50%', flexShrink: 0, background: v <= good ? '#059669' : v <= poor ? '#d97706' : '#dc2626' });
          vals.pd = {
            show: true, url: pg3.url,
            score: pg3.score, scoreStyle: scoreChip(pg3.score),
            status: pg3.statusCode + (pg3.kind === 'gone' ? ' · broken' : pg3.kind === 'redirect' ? ' · redirect' : pg3.kind === 'noindex' ? ' · blocked' : ' OK'),
            statusStyle: { marginLeft: 'auto', padding: '3px 10px', borderRadius: '999px', fontSize: '11px', fontWeight: 700, background: pg3.statusCode === 200 ? '#dcfce7' : pg3.statusCode < 400 ? '#f3e8ff' : '#fee2e2', color: pg3.statusCode === 200 ? '#15803d' : pg3.statusCode < 400 ? '#7c3aed' : '#b91c1c' },
            stats: [
              { label: 'Crawl depth', value: pg3.depth + (pg3.depth === 1 ? ' click' : ' clicks') },
              { label: 'In-links', value: pg3.inLinks },
              { label: 'Load time', value: (pg3.loadTimeMs / 1000).toFixed(1) + ' s' },
              { label: 'Internal links', value: pg3.internalLinks },
              { label: 'External links', value: pg3.externalLinks },
              { label: 'Word count', value: this.fmt(pg3.wordCount) }
            ],
            hasCwv: !!pg3.cwv,
            cwv: pg3.cwv ? [
              { name: 'LCP', value: pg3.cwv.lcp + ' s', dot: cwvDot(pg3.cwv.lcp, 2.5, 4) },
              { name: 'TBT', value: pg3.cwv.tbt + ' ms', dot: cwvDot(pg3.cwv.tbt, 200, 600) },
              { name: 'CLS', value: pg3.cwv.cls, dot: cwvDot(pg3.cwv.cls, 0.1, 0.25) }
            ] : [],
            checkCount: pg3.failed.length, noChecks: pg3.failed.length === 0,
            checks: pg3.failed.map(id => {
              const c = data.checks.find(x => x.id === id) || { title: id, severity: 'notice' };
              return {
                title: c.title, sev: c.severity,
                sevStyle: { fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: SEVC[c.severity] },
                dot: dot(SEVC[c.severity]),
                click: () => { this.setState({ auPage: null, auSub: 'issues', auSev: 'all', auCat: 'all', auOpen: id, auSearch: '' }); this.pushNav({ auSub: 'issues' }); }
              };
            })
          };
        }
      }

      vals.au = au;
    }


        /* ============ AI OPTIMIZATION ============ */
    if (tab === 'ai') {
      vals.showAi = true;
      const d = data;
      const llm = d.llmPlatforms;
      const money3 = c => '$' + Number(c || 0).toFixed(c > 0 && c < 0.1 ? 3 : 2);
      const runCostOf = pr => pr.cfg.models.length * d.costs.model;
      const inputStyle = { padding: '9px 12px', fontSize: '13px', border: '1px solid #cbd5e1', borderRadius: '8px', background: 'white', color: '#0f172a', width: '100%' };
      const redBtn = { display: 'inline-flex', alignItems: 'center', gap: '6px', cursor: 'pointer', padding: '7px 14px', fontSize: '12.5px', fontWeight: 600, color: '#dc2626', border: '1px solid #fecaca', borderRadius: '8px', background: '#fff5f5', whiteSpace: 'nowrap' };
      const priBtn = { display: 'inline-flex', alignItems: 'center', gap: '8px', cursor: 'pointer', padding: '9px 18px', fontSize: '13px', fontWeight: 600, color: 'white', background: '#4f46e5', borderRadius: '8px' };
      const ghostBtn = { display: 'inline-flex', alignItems: 'center', gap: '6px', cursor: 'pointer', padding: '8px 14px', fontSize: '13px', fontWeight: 600, color: '#334155', border: '1px solid #cbd5e1', borderRadius: '8px', background: 'white' };
      const chip = (bg, fg) => ({ fontSize: '10px', fontWeight: 700, background: bg, color: fg, padding: '1px 7px', borderRadius: '4px', flexShrink: 0 });
      const CATC = { recommendation: ['#d1fae5', '#047857'], comparison: ['#dbeafe', '#1d4ed8'], cost: ['#ffedd5', '#c2410c'], question: ['#f3e8ff', '#7e22ce'], local: ['#fef3c7', '#b45309'] };
      const catChip = c => { const m = CATC[c] || CATC.question; return { label: c, style: Object.assign(chip(m[0], m[1]), { textTransform: 'capitalize' }) }; };
      const verdictChip = v => v === 'cited' ? { label: 'Cited', style: chip('#d1fae5', '#047857') } : v === 'mentioned' ? { label: 'Mentioned', style: chip('#dbeafe', '#1d4ed8') } : { label: 'Absent', style: chip('#fee2e2', '#b91c1c') };
      const toggle2 = on => ({
        track: { width: '40px', height: '22px', borderRadius: '9999px', background: on ? '#4f46e5' : '#cbd5e1', position: 'relative', cursor: 'pointer', flexShrink: 0 },
        knob: { position: 'absolute', top: '2px', left: on ? '20px' : '2px', width: '18px', height: '18px', borderRadius: '9999px', background: 'white', transition: 'left 0.15s ease' }
      });
      const aiv = { domain: project.domain, showWizard: false, showMain: false };

      /* shared target-editor drafts (wizard step 1-2 + edit-targets modal) */
      const wizBrand = s.aiWizBrand != null ? s.aiWizBrand : d.targets.brand;
      const wizAliases = s.aiWizAliases != null ? s.aiWizAliases : d.targets.aliases.join(', ');
      const comps = s.aiWizComps || d.targets.competitors;
      aiv.wizBrand = wizBrand;
      aiv.wizAliases = wizAliases;
      aiv.wizBrandSet = e => this.setState({ aiWizBrand: e.target.value });
      aiv.wizAliasesSet = e => this.setState({ aiWizAliases: e.target.value });
      aiv.wizComps = comps.map(c => ({ domain: c, remove: () => this.setState({ aiWizComps: comps.filter(x => x !== c) }) }));
      aiv.wizCompInput = s.aiWizCompInput;
      aiv.wizCompSet = e => this.setState({ aiWizCompInput: e.target.value });
      const compAdd = () => {
        const v = this.state.aiWizCompInput.trim().toLowerCase().replace(/^https?:\/\//, '').replace(/\/.*$/, '');
        if (!v || comps.includes(v) || comps.length >= 9) return;
        this.setState({ aiWizComps: comps.concat([v]), aiWizCompInput: '' });
      };
      aiv.wizCompAdd = compAdd;
      aiv.wizCompKey = e => { if (e.key === 'Enter') compAdd(); };
      aiv.wizCompNote = comps.length + ' of 9 competitors — you + competitors map to the 10 API target entities';

      /* ---------- FIRST-RUN WIZARD ---------- */
      if (!d.setupDone) {
        aiv.showWizard = true;
        const step = s.aiWiz || 1;
        const names = ['Your brand', 'Competitors', 'Starter prompts'];
        aiv.wizSteps = names.map((nm, i2) => {
          const n = i2 + 1;
          const on = n === step, done = n < step;
          return {
            label: n + '. ' + nm,
            style: { display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 14px', borderRadius: '999px', fontSize: '12.5px', fontWeight: 600, background: on ? '#eef2ff' : 'transparent', color: on ? '#4338ca' : done ? '#059669' : '#94a3b8', border: '1px solid ' + (on ? '#c7d2fe' : 'transparent') }
          };
        });
        aiv.wizShow1 = step === 1; aiv.wizShow2 = step === 2; aiv.wizShow3 = step === 3;
        const selArr = s.aiWizSel || d.suggestions.slice(0, 6).map(x => x.id);
        aiv.wizSugs = d.suggestions.map(x => {
          const on = selArr.includes(x.id);
          const cc = catChip(x.category);
          return {
            text: x.text, catLabel: cc.label, catStyle: cc.style, vol: this.fmt(x.aiVolume),
            rowStyle: { display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 14px', borderRadius: '8px', border: '1px solid ' + (on ? '#c7d2fe' : '#e2e8f0'), background: on ? '#f5f7ff' : 'white', cursor: 'pointer' },
            checkStyle: { width: '15px', height: '15px', borderRadius: '4px', border: '1.5px solid ' + (on ? '#4f46e5' : '#cbd5e1'), background: on ? '#4f46e5' : 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, color: 'white', fontSize: '10px', fontWeight: 700 },
            checked: on,
            toggle: () => this.setState({ aiWizSel: on ? selArr.filter(i2 => i2 !== x.id) : selArr.concat([x.id]) })
          };
        });
        aiv.wizCustom = s.aiWizCustom;
        aiv.wizCustomSet = e => this.setState({ aiWizCustom: e.target.value });
        const customN = (s.aiWizCustom || '').split('\n').map(x => x.trim()).filter(Boolean).length;
        const totalN = selArr.length + customN;
        aiv.wizNext = () => this.setState({ aiWiz: step + 1 });
        aiv.wizBack = () => this.setState({ aiWiz: step - 1 });
        aiv.wizBackShown = step > 1;
        aiv.wizFinish = () => this.aiFinishSetup(d);
        aiv.wizFinishLabel = s.aiWizBusy ? 'Setting up…' : 'Finish setup — track ' + totalN + ' prompt' + (totalN === 1 ? '' : 's');
        aiv.wizWeekly = 'Weekly schedule ≈ ' + money3(totalN * 4 * d.costs.model * 4.3) + '/mo across 4 LLMs';
        aiv.inputStyle = inputStyle;
        vals.aiv = aiv;
      }

      /* ---------- MAIN ---------- */
      if (d.setupDone) {
        aiv.showMain = true;
        aiv.inputStyle = inputStyle;
        const kpi = d.kpis;
        const prompts = d.prompts;
        const listName = lid => (d.lists.find(l => l.id === lid) || { name: '—' }).name;
        const overCap = d.budget.spent / d.budget.cap;
        aiv.budgetLabel = 'AI spend ' + this.money(d.budget.spent) + ' of ' + this.money(d.budget.cap) + ' cap';
        aiv.budgetStyle = { fontSize: '12px', fontWeight: 600, padding: '4px 10px', borderRadius: '6px', background: overCap >= 0.8 ? '#fee2e2' : '#f1f5f9', color: overCap >= 0.8 ? '#b91c1c' : '#475569' };
        aiv.nextRunLabel = d.next_run ? ('Runs weekly · next ' + d.next_run) : 'Runs weekly · not yet scheduled';
        const allCost = prompts.reduce((a2, pr) => a2 + runCostOf(pr), 0);
        aiv.runAllLabel = 'Run all now · ' + money3(allCost);
        aiv.runAllStyle = redBtn;
        aiv.runAll = () => { if (prompts.length) this.aiRun({}); };
        aiv.hasPrompts = prompts.length > 0;

        const sub2 = s.aiSub;
        const goSub = v => { this.setState({ aiSub: v, aiOpen: null }); this.pushNav({ aiSub: v }); };
        const subBase2 = { padding: '10px 16px', fontSize: '13px', fontWeight: 600, cursor: 'pointer', color: '#64748b', borderBottom: '2px solid transparent', marginBottom: '-1px' };
        aiv.subTabs = [['visibility', 'AI Visibility'], ['prompts', 'Prompts (' + prompts.length + ')'], ['aikw', 'AI Keywords (' + d.aiKeywords.length + ')'], ['inspector', 'Answer Inspector'], ['history', 'History (' + d.history.length + ')']].map(t => ({
          label: t[1],
          style: sub2 === t[0] ? Object.assign({}, subBase2, { color: '#4f46e5', borderBottom: '2px solid #4f46e5' }) : subBase2,
          click: () => goSub(t[0])
        }));
        aiv.showVisibility = sub2 === 'visibility'; aiv.showPrompts = sub2 === 'prompts';
        aiv.showAikw = sub2 === 'aikw'; aiv.showInspector = sub2 === 'inspector'; aiv.showHistory = sub2 === 'history';

        /* targets card + edit modal */
        aiv.tgBrand = d.targets.brand;
        aiv.tgAliases = d.targets.aliases;
        aiv.tgComps = d.targets.competitors;
        aiv.tgEdit = () => this.setState({ aiTgOpen: true, aiWizBrand: d.targets.brand, aiWizAliases: d.targets.aliases.join(', '), aiWizComps: d.targets.competitors.slice(), aiWizCompInput: '' });
        aiv.tgOpen = s.aiTgOpen;
        aiv.tgClose = () => this.setState({ aiTgOpen: false, aiWizBrand: null, aiWizAliases: null, aiWizComps: null, aiWizCompInput: '' });
        aiv.tgSave = () => this.aiSaveTargets(d);

        if (sub2 === 'visibility') {
          const sov = d.sov;
          const maxSov = Math.max.apply(null, sov.rows.map(r => r.sov)) || 1;
          aiv.sovPct = sov.you + '%';
          aiv.sovDelta = (sov.delta >= 0 ? '▲ +' : '▼ ') + Math.abs(sov.delta) + ' pts vs. last week';
          aiv.sovDeltaStyle = { fontSize: '12px', fontWeight: 600, padding: '3px 8px', borderRadius: '4px', background: sov.delta >= 0 ? '#ecfdf5' : '#fff1f2', color: sov.delta >= 0 ? '#059669' : '#e11d48' };
          aiv.sovRows = sov.rows.map((r, i2) => ({
            rank: '#' + (i2 + 1), domain: r.domain, sovFmt: r.sov + '%',
            mentionsFmt: this.fmt(r.mentions) + ' mentions',
            nameStyle: { fontSize: '13px', fontWeight: r.isYou ? 700 : 500, color: r.isYou ? '#4338ca' : '#334155', flex: 1, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' },
            barStyle: { height: '8px', borderRadius: '4px', width: Math.max(3, Math.round((r.sov / maxSov) * 100)) + '%', background: r.isYou ? '#4f46e5' : '#cbd5e1' },
            youChip: r.isYou
          }));
          aiv.kpis = [
            { label: 'Brand mentions · 30d', value: this.fmt(kpi.mentions), sub: 'AI Overviews + ChatGPT' },
            { label: 'AI impressions', value: this.fmt(kpi.impressions), sub: 'est. answer views citing you' },
            { label: 'Cited pages', value: kpi.cited_pages, sub: 'of your URLs used as sources' },
            { label: 'Prompt coverage', value: kpi.prompt_coverage.cited + ' of ' + kpi.prompt_coverage.total, sub: 'tracked prompts citing you' }
          ];
          const chipBase3 = { display: 'inline-flex', alignItems: 'center', gap: '7px', padding: '5px 11px', fontSize: '12px', fontWeight: 500, borderRadius: '999px', cursor: 'pointer', color: '#64748b', border: '1px solid #e2e8f0', background: 'white' };
          aiv.platToggles = d.mentionPlatforms.map(pl2 => {
            const on = !!s.aiPlat[pl2.id];
            return {
              label: pl2.name,
              dot: { width: '8px', height: '8px', borderRadius: '50%', background: on ? pl2.color : '#cbd5e1', flexShrink: 0 },
              style: on ? Object.assign({}, chipBase3, { borderColor: pl2.color, color: '#0f172a' }) : chipBase3,
              click: () => this.setState(st => ({ aiPlat: Object.assign({}, st.aiPlat, { [pl2.id]: !st.aiPlat[pl2.id] }) }))
            };
          });
          const allVals = [];
          d.mentionPlatforms.forEach(pl2 => { if (s.aiPlat[pl2.id]) d.trend.forEach(pt2 => allVals.push(pt2[pl2.id])); });
          const maxV = Math.max(1, ...allVals);
          aiv.trendLines = d.mentionPlatforms.filter(pl2 => s.aiPlat[pl2.id]).map(pl2 => {
            const pts = d.trend.map((pt2, k) => {
              const x = (k / (d.trend.length - 1)) * 590 + 5;
              const y = 190 - (pt2[pl2.id] / maxV) * 175;
              return x.toFixed(1) + ',' + y.toFixed(1);
            }).join(' ');
            return { pts, color: pl2.color };
          });
          aiv.trendFrom = d.trend.length ? d.trend[0].date : '';
          aiv.trendTo = d.trend.length ? d.trend[d.trend.length - 1].date : '';
          aiv.topPages = d.topPages.map(pg2 => ({
            url: pg2.url, mentions: pg2.mentions, imprFmt: this.fmt(pg2.impressions),
            platforms: pg2.platforms.join(' · ') || '—'
          }));
          const maxShare = Math.max.apply(null, d.topDomains.map(dm => dm.share)) || 1;
          aiv.topDomains = d.topDomains.map((dm, i2) => ({
            rank: i2 + 1, domain: dm.domain, shareFmt: dm.share + '%', mentionsFmt: this.fmt(dm.mentions),
            nameStyle: { fontSize: '13px', fontWeight: dm.isYou ? 700 : 500, color: dm.isYou ? '#4338ca' : '#334155', flex: 1, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' },
            barStyle: { height: '7px', borderRadius: '4px', width: Math.max(3, Math.round((dm.share / maxShare) * 100)) + '%', background: dm.isYou ? '#4f46e5' : dm.isComp ? '#f59e0b' : '#cbd5e1' },
            tagLabel: dm.isYou ? 'You' : dm.isComp ? 'Competitor' : '',
            tagStyle: dm.isYou ? chip('#eef2ff', '#4338ca') : chip('#fef3c7', '#b45309')
          }));
        }

        if (sub2 === 'prompts') {
          /* --- prompt explorer --- */
          aiv.expQ = s.aiExpQ;
          aiv.expSet = e => this.setState({ aiExpQ: e.target.value });
          aiv.expKey = e => { if (e.key === 'Enter') this.aiExplore(); };
          aiv.expRun = () => this.aiExplore();
          aiv.expLabel = s.aiExploring ? 'Exploring…' : 'Explore prompts';
          aiv.expBtnStyle = priBtn;
          aiv.hasExp = !!(s.aiExp && s.aiExp.rows);
          if (aiv.hasExp) {
            const selSet = new Set(s.aiExpSel);
            const rows2 = s.aiExp.rows;
            const selTexts = () => rows2.filter(r => selSet.has(r.text) && !r.tracked).map(r => r.text);
            aiv.expMeta = rows2.length + ' prompt ideas · ' + s.aiExp.location + ' · est. cost ' + this.money(s.aiExp.cost);
            aiv.expClear = () => this.setState({ aiExp: null, aiExpSel: [], aiExpAddOpen: false });
            aiv.expSelCount = s.aiExpSel.length;
            aiv.expAnySel = s.aiExpSel.length > 0;
            aiv.expAddOpen = s.aiExpAddOpen;
            aiv.expAddToggle = () => this.setState(st => ({ aiExpAddOpen: !st.aiExpAddOpen }));
            aiv.expAddBtnStyle = Object.assign({}, priBtn, { padding: '7px 14px', fontSize: '12.5px', opacity: s.aiExpSel.length ? 1 : 0.5, cursor: s.aiExpSel.length ? 'pointer' : 'default' });
            aiv.expLists = d.lists.map(l => ({
              name: l.name,
              onAdd: () => this.aiAddPrompts(selTexts(), l.id, () => this.setState({ aiExpSel: [], aiExpAddOpen: false }))
            }));
            aiv.expNewName = s.aiNewPlName;
            aiv.expNewSet = e => this.setState({ aiNewPlName: e.target.value });
            const expCreateAdd = () => {
              const nm = this.state.aiNewPlName.trim();
              const texts = selTexts();
              if (!nm || !texts.length) return;
              this.aiPost('lists', { op: 'create', name: nm })
                .then(r => this.aiAddPrompts(texts, r.id, () => this.setState({ aiExpSel: [], aiExpAddOpen: false, aiNewPlName: '', aiListFilter: r.id })))
                .catch(() => {});
            };
            aiv.expNewCreate = expCreateAdd;
            aiv.expNewKey = e => { if (e.key === 'Enter') expCreateAdd(); };
            aiv.expRows = rows2.map(r => {
              const on = selSet.has(r.text);
              const cc = catChip(r.category);
              return {
                text: r.text, volFmt: this.fmt(r.aiVolume), tracked: r.tracked,
                catLabel: cc.label, catStyle: cc.style,
                rowBg: on ? '#f5f7ff' : 'white',
                checkStyle: { width: '15px', height: '15px', borderRadius: '4px', border: '1.5px solid ' + (on ? '#4f46e5' : '#cbd5e1'), background: on ? '#4f46e5' : 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, color: 'white', fontSize: '10px', fontWeight: 700 },
                checked: on,
                toggle: () => { if (r.tracked) return; this.setState(st => ({ aiExpSel: on ? st.aiExpSel.filter(x => x !== r.text) : st.aiExpSel.concat([r.text]) })); }
              };
            });
          }

          /* --- list chips + manage --- */
          const counts = { all: prompts.length };
          d.lists.forEach(l => { counts[l.id] = prompts.filter(pr => pr.listId === l.id).length; });
          const fBase = { padding: '5px 12px', fontSize: '12px', fontWeight: 500, borderRadius: '999px', cursor: 'pointer', color: '#64748b', border: '1px solid #e2e8f0', background: 'white' };
          const fActive = Object.assign({}, fBase, { borderColor: '#4f46e5', color: '#4f46e5', background: '#eef2ff', fontWeight: 600 });
          aiv.listChips = [{ id: 'all', name: 'All' }].concat(d.lists).map(l => ({
            label: l.name + ' (' + counts[l.id] + ')',
            style: s.aiListFilter === l.id ? fActive : fBase,
            click: () => this.setState({ aiListFilter: l.id })
          }));
          aiv.listsOpen = s.aiListsOpen;
          aiv.listsToggle = () => this.setState(st => ({ aiListsOpen: !st.aiListsOpen }));
          aiv.manageRows = d.lists.map(l => ({
            name: l.name, count: counts[l.id] + ' prompt' + (counts[l.id] === 1 ? '' : 's'),
            rename: e => { const nm = e.target.value.trim(); if (nm && nm !== l.name) this.aiListOp('rename', l.id, nm); },
            del: () => this.aiListOp('delete', l.id, null, () => this.setState({ aiListFilter: 'all' })),
            canDel: d.lists.length > 1
          }));
          aiv.newPlName = s.aiNewPlName;
          aiv.newPlSet = e => this.setState({ aiNewPlName: e.target.value });
          const createList = () => { const nm = this.state.aiNewPlName.trim(); if (nm) this.aiListOp('create', null, nm, () => this.setState({ aiNewPlName: '' })); };
          aiv.newPlCreate = createList;
          aiv.newPlKey = e => { if (e.key === 'Enter') createList(); };

          /* --- composer --- */
          aiv.composerOpen = s.aiComposerOpen;
          aiv.composerShow = () => this.setState({ aiComposerOpen: true, aiComposerList: this.state.aiComposerList || (d.lists[0] || {}).id });
          aiv.composerHide = () => this.setState({ aiComposerOpen: false });
          aiv.compText = s.aiComposerText;
          aiv.compTextSet = e => this.setState({ aiComposerText: e.target.value });
          aiv.compList = s.aiComposerList || (d.lists[0] || {}).id;
          aiv.compListSet = e => this.setState({ aiComposerList: e.target.value });
          aiv.compListOptions = d.lists.map(l => ({ value: l.id, label: l.name }));
          aiv.compSugs = d.suggestions.slice(0, 5).map(x => ({
            text: x.text,
            add: () => this.setState(st => ({ aiComposerText: (st.aiComposerText ? st.aiComposerText.replace(/\n?$/, '\n') : '') + x.text }))
          }));
          const compLines = (s.aiComposerText || '').split('\n').map(x => x.trim()).filter(Boolean);
          aiv.compCount = compLines.length;
          aiv.compAddLabel = 'Add ' + compLines.length + ' prompt' + (compLines.length === 1 ? '' : 's');
          aiv.compAddStyle = Object.assign({}, priBtn, { opacity: compLines.length ? 1 : 0.5, cursor: compLines.length ? 'pointer' : 'default' });
          aiv.compAdd = () => { if (compLines.length) this.aiAddPrompts(compLines, this.state.aiComposerList || (d.lists[0] || {}).id, () => this.setState({ aiComposerOpen: false, aiComposerText: '' })); };

          /* --- prompt table --- */
          aiv.noPrompts = prompts.length === 0;
          aiv.platNames = llm.map(pl2 => pl2.name);
          aiv.promptGridCols = 'minmax(280px, 1.8fr) repeat(' + llm.length + ', 1fr)';
          const cell = r => {
            if (!r) return { label: 'off', style: Object.assign(chip('#f8fafc', '#cbd5e1'), { fontSize: '11px', fontWeight: 500 }) };
            if (!r.mentioned) return { label: '—', style: { display: 'inline-flex', alignItems: 'center', justifyContent: 'center', minWidth: '44px', height: '24px', borderRadius: '4px', fontSize: '12px', fontWeight: 600, background: '#f8fafc', color: '#cbd5e1' } };
            if (r.cited) return { label: 'Cited #' + r.position, style: { display: 'inline-flex', alignItems: 'center', justifyContent: 'center', minWidth: '44px', height: '24px', padding: '0 8px', borderRadius: '4px', fontSize: '12px', fontWeight: 700, background: '#d1fae5', color: '#047857' } };
            return { label: 'Mentioned', style: { display: 'inline-flex', alignItems: 'center', justifyContent: 'center', minWidth: '44px', height: '24px', padding: '0 8px', borderRadius: '4px', fontSize: '12px', fontWeight: 600, background: '#dbeafe', color: '#1d4ed8' } };
          };
          const visPrompts = prompts.filter(pr => s.aiListFilter === 'all' || pr.listId === s.aiListFilter);
          aiv.promptEmptyFiltered = prompts.length > 0 && visPrompts.length === 0;
          aiv.promptRows = visPrompts.map(pr => {
            const open = s.aiOpen === pr.id;
            const citedN = llm.filter(pl2 => pr.cfg.models.includes(pl2.id) && pr.results[pl2.id].cited).length;
            return {
              text: pr.text, open,
              meta: listName(pr.listId) + ' · ' + pr.cfg.models.length + ' model' + (pr.cfg.models.length === 1 ? '' : 's') + ' · ' + pr.cfg.cadence + ' · ' + (pr.cfg.city || pr.cfg.country) + (pr.lastRun ? ' · last run ' + pr.lastRun : ' · not run yet'),
              cells: llm.map(pl2 => cell(pr.cfg.models.includes(pl2.id) ? pr.results[pl2.id] : null)),
              toggle: () => this.setState({ aiOpen: open ? null : pr.id }),
              chev: { color: '#cbd5e1', fontSize: '18px', transform: open ? 'rotate(90deg)' : 'none', transition: 'transform 0.15s ease', flexShrink: 0 },
              coverage: citedN + ' of ' + pr.cfg.models.length + ' models cite you',
              details: llm.filter(pl2 => pr.cfg.models.includes(pl2.id)).map(pl2 => ({
                name: pl2.name,
                dot: { width: '8px', height: '8px', borderRadius: '50%', background: pl2.color, flexShrink: 0 },
                snippet: pr.results[pl2.id].snippet
              })),
              runLabel: 'Run now · ' + money3(runCostOf(pr)),
              runStyle: redBtn,
              run: () => this.aiRun({ promptId: pr.id }),
              inspect: () => this.aiInspect(pr.text, pr.id),
              cfgOpen: () => this.setState({ aiCfgOpen: pr.id, aiCfgDraft: Object.assign({}, pr.cfg, { models: pr.cfg.models.slice(), listId: pr.listId }) }),
              remove: () => this.aiPost('prompts-remove', { id: pr.id }).then(() => { this.aiReload(); this.notify('Prompt removed'); }).catch(() => {})
            };
          });
          const flt = d.lists.find(l => l.id === s.aiListFilter);
          if (flt) {
            const listCost = visPrompts.reduce((a2, pr) => a2 + runCostOf(pr), 0);
            aiv.runListShown = visPrompts.length > 0;
            aiv.runListLabel = 'Run "' + flt.name + '" now · ' + money3(listCost);
            aiv.runListStyle = redBtn;
            aiv.runList = () => this.aiRun({ listId: flt.id });
          } else { aiv.runListShown = false; }

          /* --- config modal --- */
          const cfgPr = s.aiCfgOpen ? prompts.find(pr => pr.id === s.aiCfgOpen) : null;
          if (cfgPr && s.aiCfgDraft) {
            const dr = s.aiCfgDraft;
            const setDr = patch => this.setState(st => ({ aiCfgDraft: Object.assign({}, st.aiCfgDraft, patch) }));
            const tg = toggle2(!!dr.webSearch);
            aiv.cfg = {
              open: true, text: cfgPr.text,
              models: llm.map(pl2 => {
                const on = dr.models.includes(pl2.id);
                return {
                  name: pl2.name,
                  style: { display: 'inline-flex', alignItems: 'center', gap: '7px', padding: '6px 12px', fontSize: '12.5px', fontWeight: 600, borderRadius: '8px', cursor: 'pointer', border: '1px solid ' + (on ? pl2.color : '#e2e8f0'), background: on ? '#f8fafc' : 'white', color: on ? '#0f172a' : '#94a3b8' },
                  dot: { width: '8px', height: '8px', borderRadius: '50%', background: on ? pl2.color : '#cbd5e1', flexShrink: 0 },
                  toggle: () => { const next = on ? dr.models.filter(m => m !== pl2.id) : dr.models.concat([pl2.id]); if (next.length) setDr({ models: next }); }
                };
              }),
              webTrack: tg.track, webKnob: tg.knob,
              webToggle: () => setDr({ webSearch: !dr.webSearch }),
              webNote: dr.webSearch ? 'Web search on — answers can cite live sources' : 'Web search off — no citations returned',
              country: dr.country, countrySet: e => setDr({ country: e.target.value }),
              city: dr.city, citySet: e => setDr({ city: e.target.value }),
              cadence: dr.cadence, cadenceSet: e => setDr({ cadence: e.target.value }),
              listId: dr.listId, listSet: e => setDr({ listId: e.target.value }),
              listOptions: d.lists.map(l => ({ value: l.id, label: l.name })),
              costNote: 'One run ≈ ' + money3(dr.models.length * d.costs.model) + ' · ' + (dr.cadence === 'manual' ? 'manual runs only' : dr.cadence + ' ≈ ' + money3(dr.models.length * d.costs.model * (dr.cadence === 'daily' ? 30 : 4.3)) + '/mo'),
              close: () => this.setState({ aiCfgOpen: null, aiCfgDraft: null }),
              save: () => this.aiPost('prompts-config', { id: cfgPr.id, cfg: { models: dr.models, webSearch: dr.webSearch, country: dr.country, city: dr.city, cadence: dr.cadence }, listId: dr.listId })
                .then(() => { this.setState({ aiCfgOpen: null, aiCfgDraft: null }); this.aiReload(); this.notify('Prompt settings saved'); }).catch(() => {})
            };
          } else { aiv.cfg = { open: false }; }
        }

        if (sub2 === 'aikw') {
          const allRows = d.aiKeywords;
          const gaps = allRows.filter(r => r.gap);
          aiv.kwKpis = [
            { label: 'Total AI search volume', value: this.fmt(allRows.reduce((a2, r) => a2 + r.aiVolume, 0)), sub: 'est. monthly prompts on your keywords' },
            { label: 'AI-heavy keywords', value: allRows.filter(r => r.ratio >= 30).length, sub: 'AI volume ≥ 30% of Google volume' },
            { label: 'Visibility gaps', value: gaps.length, sub: 'high AI volume, zero mentions of you' }
          ];
          /* search + segment filters */
          const segDefs = [['all', 'All'], ['heavy', 'AI-heavy'], ['gap', 'Gaps'], ['mentioned', 'Mentioned']];
          const segCounts = {
            all: allRows.length,
            heavy: allRows.filter(r => r.ratio >= 30).length,
            gap: gaps.length,
            mentioned: allRows.filter(r => r.mentions > 0).length
          };
          const segBase = { padding: '5px 12px', fontSize: '12px', fontWeight: 500, borderRadius: '999px', cursor: 'pointer', color: '#64748b', border: '1px solid #e2e8f0', background: 'white' };
          const segActive = Object.assign({}, segBase, { borderColor: '#4f46e5', color: '#4f46e5', background: '#eef2ff', fontWeight: 600 });
          const seg = s.aiKwSeg || 'all';
          aiv.kwSegs = segDefs.map(sd => ({
            label: sd[1] + ' (' + segCounts[sd[0]] + ')',
            style: seg === sd[0] ? segActive : segBase,
            click: () => this.setState({ aiKwSeg: sd[0] })
          }));
          let rows = allRows.filter(r => seg === 'all' || (seg === 'heavy' && r.ratio >= 30) || (seg === 'gap' && r.gap) || (seg === 'mentioned' && r.mentions > 0));
          if (s.aiKwQ) { const q2 = s.aiKwQ.toLowerCase(); rows = rows.filter(r => r.kw.toLowerCase().includes(q2)); }
          aiv.kwQ = s.aiKwQ || '';
          aiv.kwQSet = e => this.setState({ aiKwQ: e.target.value });
          aiv.kwNoRows = rows.length === 0;
          aiv.kwCount = rows.length + ' of ' + allRows.length + ' keywords';
          /* selection */
          const kwSel = s.aiKwSel || [];
          const kwSelSet = new Set(kwSel);
          const visSel = rows.filter(r => kwSelSet.has(r.kw));
          const allOn = rows.length > 0 && rows.every(r => kwSelSet.has(r.kw));
          aiv.kwAllChecked = allOn;
          aiv.kwAllCheckStyle = { width: '15px', height: '15px', borderRadius: '4px', border: '1.5px solid ' + (allOn ? '#4f46e5' : '#cbd5e1'), background: allOn ? '#4f46e5' : 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, color: 'white', fontSize: '10px', fontWeight: 700, cursor: 'pointer' };
          aiv.kwToggleAll = () => this.setState({ aiKwSel: allOn ? [] : rows.map(r => r.kw) });
          aiv.kwAnySel = visSel.length > 0;
          aiv.kwSelCount = visSel.length + ' selected';
          aiv.kwClearSel = () => this.setState({ aiKwSel: [], aiKwAddOpen: false });
          aiv.kwToolbarBg = visSel.length > 0 ? '#f5f7ff' : '#f8fafc';
          /* management actions */
          const promptOf = kw2 => 'What is the best ' + kw2 + ' and who do you recommend?';
          const selPromptTexts = () => visSel.map(r => promptOf(r.kw));
          aiv.kwAddOpen = s.aiKwAddOpen;
          aiv.kwAddToggle = () => this.setState(st => ({ aiKwAddOpen: !st.aiKwAddOpen }));
          aiv.kwAddBtnStyle = { display: 'inline-flex', alignItems: 'center', gap: '6px', cursor: visSel.length ? 'pointer' : 'default', padding: '7px 14px', fontSize: '12.5px', fontWeight: 600, color: 'white', background: '#4f46e5', borderRadius: '8px', opacity: visSel.length ? 1 : 0.5 };
          aiv.kwLists = d.lists.map(l => ({
            name: l.name,
            onAdd: () => this.aiAddPrompts(selPromptTexts(), l.id, () => this.setState({ aiKwSel: [], aiKwAddOpen: false }))
          }));
          aiv.kwNewName = s.aiNewPlName;
          aiv.kwNewSet = e => this.setState({ aiNewPlName: e.target.value });
          const kwCreateAdd = () => {
            const nm = this.state.aiNewPlName.trim();
            const texts = selPromptTexts();
            if (!nm || !texts.length) return;
            this.aiPost('lists', { op: 'create', name: nm })
              .then(r => this.aiAddPrompts(texts, r.id, () => this.setState({ aiKwSel: [], aiKwAddOpen: false, aiNewPlName: '' })))
              .catch(() => {});
          };
          aiv.kwNewCreate = kwCreateAdd;
          aiv.kwNewKey = e => { if (e.key === 'Enter') kwCreateAdd(); };
          aiv.kwExport = () => {
            const exp = visSel.length ? visSel : rows;
            this.downloadCsv(project.domain + '-ai-keywords.csv',
              [['keyword', 'kw'], ['ai_volume', 'aiVolume'], ['google_volume', 'gVolume'], ['ai_share_pct', 'ratio'], ['intent', 'intent'], ['your_mentions', 'mentions']], exp);
            this.notify('Exported ' + exp.length + ' AI keyword' + (exp.length === 1 ? '' : 's') + ' (CSV)');
          };
          aiv.kwExportLabel = 'Export CSV ' + (visSel.length ? '(' + visSel.length + ')' : '(all ' + rows.length + ')');
          aiv.kwRows = rows.map(r => {
            const iv = this.intentView(r.intent);
            const on = kwSelSet.has(r.kw);
            return {
              checked: on,
              rowBg: on ? '#f5f7ff' : 'white',
              checkStyle: { width: '15px', height: '15px', borderRadius: '4px', border: '1.5px solid ' + (on ? '#4f46e5' : '#cbd5e1'), background: on ? '#4f46e5' : 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, color: 'white', fontSize: '10px', fontWeight: 700, cursor: 'pointer' },
              toggleSel: () => this.setState(st => ({ aiKwSel: on ? (st.aiKwSel || []).filter(x => x !== r.kw) : (st.aiKwSel || []).concat([r.kw]) })),
              kw: r.kw, aiVolFmt: this.fmt(r.aiVolume), gVolFmt: this.fmt(r.gVolume),
              spark: this.spark(r.trend, 46, 16),
              sparkColor: r.trend[11] >= r.trend[0] ? '#22c55e' : '#ef4444',
              ratioLabel: r.ratio == null ? '—' : r.ratio + '%',
              ratioStyle: { fontSize: '12px', fontWeight: 700, color: r.ratio >= 30 ? '#7c3aed' : '#64748b', textAlign: 'right' },
              intentLabel: iv.label, intentStyle: iv.style,
              mentions: r.mentions,
              gap: r.gap,
              mentionsStyle: { fontSize: '13px', fontWeight: 600, color: r.mentions === 0 ? '#cbd5e1' : '#0f172a', textAlign: 'right' },
              track: () => this.aiInspect('What is the best ' + r.kw + ' and who do you recommend?', null)
            };
          });
        }

        if (sub2 === 'inspector') {
          aiv.inspQ = s.aiInspQ;
          aiv.inspQSet = e => this.setState({ aiInspQ: e.target.value });
          aiv.inspQKey = e => { if (e.key === 'Enter') this.aiInspect(this.state.aiInspQ, null); };
          aiv.inspRun = () => this.aiInspect(this.state.aiInspQ, null);
          aiv.inspRunLabel = s.aiInspecting ? 'Inspecting…' : 'Inspect now · ' + money3(d.costs.inspect);
          aiv.inspRunStyle = Object.assign({}, redBtn, { padding: '9px 16px', fontSize: '13px' });
          const entry = s.aiInspEntry || d.history[0] || null;
          aiv.inspHasEntry = !!entry;
          aiv.inspecting = s.aiInspecting;
          if (entry) {
            const sc2 = entry.scrape;
            const vc = verdictChip(entry.verdict);
            aiv.inspPrompt = entry.question;
            aiv.inspMeta = sc2.model + ' · ' + sc2.location + ' · captured ' + entry.ts;
            aiv.inspVerdict = entry.verdict === 'cited' ? 'You are cited at position #' + entry.position : entry.verdict === 'mentioned' ? 'You are mentioned but not cited' : 'You are not mentioned in this answer';
            aiv.inspVerdictStyle = Object.assign({}, vc.style, { fontSize: '12px', padding: '4px 10px', borderRadius: '999px' });
            aiv.inspParas = sc2.paragraphs.map(pa => ({
              text: pa.text,
              style: pa.hit
                ? { fontSize: '14px', lineHeight: 1.65, color: '#312e81', background: '#eef2ff', border: '1px solid #c7d2fe', borderRadius: '8px', padding: '12px 14px', margin: 0 }
                : { fontSize: '14px', lineHeight: 1.65, color: '#334155', margin: 0, padding: '0 14px' }
            }));
            aiv.inspCites = sc2.citations.map(c2 => ({
              n: '[' + c2.n + ']', title: c2.title, domain: c2.domain,
              rowStyle: { display: 'flex', alignItems: 'flex-start', gap: '10px', padding: '10px 14px', borderTop: '1px solid #f8fafc', background: c2.isYou ? '#eef2ff' : 'transparent' },
              titleStyle: { fontSize: '13px', fontWeight: c2.isYou ? 700 : 500, color: c2.isYou ? '#4338ca' : '#334155' },
              youChip: c2.isYou
            }));
          }
        }

        if (sub2 === 'history') {
          aiv.histEmpty = d.history.length === 0;
          aiv.histRows = d.history.map(e => {
            const vc = verdictChip(e.verdict);
            return {
              date: e.ts, question: e.question,
              verdictLabel: vc.label, verdictStyle: vc.style,
              pos: e.position ? '#' + e.position : '—',
              costFmt: money3(e.cost),
              open: () => { this.setState({ aiInspEntry: e, aiSub: 'inspector' }); this.pushNav({ aiSub: 'inspector' }); }
            };
          });
        }

        vals.aiv = aiv;
      }
    }


        /* ============ ADS SUITE (Paid Overview / Campaigns / Terms / Attribution) ============ */
    if (this.ADSTABS.includes(tab)) {
      const t = data.totals, pv = data.prev, cs = data.campaigns;
      const pctD = (a, b) => (b ? Math.round(((a - b) / b) * 100) : null);
      const chip = (d, invert) => {
        if (d == null || !isFinite(d)) return { label: '', style: {} };
        const good = invert ? d <= 0 : d >= 0;
        return { label: (d > 0 ? '+' : '') + d + '%', style: { fontSize: '11px', fontWeight: 600, color: good ? '#059669' : '#dc2626' } };
      };
      const platformChip = pl => ({
        fontSize: '10px', fontWeight: 500, whiteSpace: 'nowrap', padding: '1px 8px', borderRadius: '4px',
        background: pl === 'Meta' ? '#eef2ff' : '#eff6ff', color: pl === 'Meta' ? '#4f46e5' : '#2563eb',
        border: '1px solid ' + (pl === 'Meta' ? '#c7d2fe' : '#bfdbfe')
      });
      const roasSt = v => ({ fontWeight: 600, color: v >= 3 ? '#059669' : v >= 1.5 ? '#2563eb' : '#dc2626' });
      const fBase = { padding: '4px 12px', fontSize: '12px', fontWeight: 500, borderRadius: '6px', cursor: 'pointer', color: '#64748b' };
      const fActive = Object.assign({}, fBase, { background: 'white', color: '#0f172a', boxShadow: '0 1px 2px rgba(0,0,0,0.05)' });
      const fmtTs = z => z ? new Date(z).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }) : '—';
      const sm = data.syncMeta || {};
      const adsSetup = !data || !sm || !sm.connected || sm.state === 'setup' || (data.totals && data.totals.spend === 0 && (!data.campaigns || !data.campaigns.length));
      vals.adsSync = {
        cadence: sm.connected ? sm.cadence : 'not yet connected',
        last: fmtTs(sm.last_pull), next: fmtTs(sm.next_pull),
        quota: sm.ops_used + ' / ' + this.fmt(sm.ops_limit) + ' ops today',
        ga4: sm.ga4_tokens_used + ' / ' + this.fmt(sm.ga4_tokens_limit) + ' tokens',
        dotStyle: { width: '7px', height: '7px', borderRadius: '9999px', background: sm.connected ? '#10b981' : '#cbd5e1' }
      };
      const fmtD = z => new Date(z + 'T00:00:00').toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
      vals.adsWindow = data.window && data.window.from ? (fmtD(data.window.from) + ' – ' + fmtD(data.window.to) + ' · ' + data.window.days + ' days') : '';
      const wastedTerms = data.searchTerms.filter(x => x.status === 'wasted');
      const wasted = wastedTerms.reduce((s2, x2) => s2 + x2.cost, 0);

      /* ---- Paid Overview ---- */
      if (tab === 'ads') {
        vals.showAds = true;
        if (adsSetup) {
          vals.ads = { setup: true };
          return vals;
        }
        const cpa = t.conversions ? t.spend / t.conversions : 0;
        const pCpa = pv.conversions ? pv.spend / pv.conversions : 0;
        const kpi = (label, value, c, note) => ({ label, value, chipLabel: c.label, chipStyle: c.style, note: note || '' });
        const noChip = { label: '', style: {} };
        vals.ads = {
          kpis: [
            kpi('Spend', this.money(t.spend), chip(pctD(t.spend, pv.spend), true), 'vs. previous period'),
            kpi('Conversions', String(Math.round(t.conversions)), chip(pctD(t.conversions, pv.conversions)), 'Google Ads + Meta'),
            kpi('CPA', this.money(cpa), chip(pCpa ? Math.round((cpa - pCpa) / pCpa * 100) : null, true), 'cost / conversion'),
            kpi('ROAS', t.roas.toFixed(2) + 'x', noChip, this.money(t.conv_value) + ' conv. value'),
            kpi('Avg CPC', this.money(t.cpc), noChip, this.fmt(t.clicks) + ' clicks'),
            kpi('GA4 key events', String(Math.round(t.ga4_key_events)), noChip, 'GA4 attribution')
          ]
        };
        const tr = data.trend;
        const W = 600, H = 220, P = 8;
        const maxSp = Math.max.apply(null, tr.map(d => d.spend).concat([1]));
        const maxCv = Math.max.apply(null, tr.map(d => Math.max(d.conversions, d.ga4_key_events)).concat([1]));
        const xs = i => (tr.length > 1 ? P + i * ((W - 2 * P) / (tr.length - 1)) : W / 2);
        const yOf = (v, max) => H - P - (v / max) * (H - 2 * P);
        const pts = (k, max) => tr.map((d, i) => xs(i).toFixed(1) + ',' + yOf(d[k], max).toFixed(1)).join(' ');
        vals.ads.spendPts = pts('spend', maxSp);
        vals.ads.convPts = pts('conversions', maxCv);
        vals.ads.ga4Pts = pts('ga4_key_events', maxCv);
        vals.ads.spendArea = tr.length ? 'M' + xs(0).toFixed(1) + ',' + (H - P) + ' L' + vals.ads.spendPts.split(' ').join(' L') + ' L' + xs(tr.length - 1).toFixed(1) + ',' + (H - P) + ' Z' : '';
        vals.ads.trendStart = tr.length ? tr[0].date : '';
        vals.ads.trendEnd = tr.length ? tr[tr.length - 1].date : '';
        vals.ads.trendRangeLabel = s.range === '7d' ? 'last 7 days' : s.range === '90d' ? 'last 90 days' : 'last 30 days';
        const pc = data.pacing;
        const over = pc.projected > pc.monthly_budget * 1.05, under = pc.projected < pc.monthly_budget * 0.8;
        vals.ads.pacing = {
          budget: this.money(pc.monthly_budget), mtd: this.money(pc.mtd_spend), projected: this.money(pc.projected),
          dayLabel: 'day ' + pc.day_of_month + ' of ' + pc.days_in_month,
          statusLabel: over ? 'Over pace' : under ? 'Under pace' : 'On pace',
          statusStyle: { fontSize: '11px', fontWeight: 600, padding: '2px 8px', borderRadius: '4px', background: over ? '#fee2e2' : under ? '#fef9c3' : '#ecfdf5', color: over ? '#b91c1c' : under ? '#a16207' : '#059669' },
          barStyle: { height: '100%', width: pc.pct + '%', background: over ? '#dc2626' : '#4f46e5', borderRadius: '9999px', transition: 'width 0.3s ease' },
          channels: pc.channels.map(c => ({
            platform: c.platform, mtdFmt: this.money(c.mtd), budgetFmt: this.money(c.budget),
            barStyle: { height: '100%', width: c.pct + '%', background: c.platform === 'Meta' ? '#818cf8' : '#4f46e5', borderRadius: '9999px' }
          }))
        };
        const attn = [];
        cs.filter(c => c.status === 'enabled' && c.lost_is_budget >= 15).forEach(c => attn.push({
          sev: 'medium', title: '"' + c.name + '" is limited by budget',
          detail: 'Losing ' + c.lost_is_budget + '% of impression share to budget in this period.',
          action: 'Adjust budget', go: () => this.go('campaigns')
        }));
        cs.filter(c => c.status === 'enabled' && c.cpa && c.prev.conversions > 0.5).forEach(c => {
          const p2 = c.prev.spend / c.prev.conversions;
          if (p2 > 0 && c.cpa > p2 * 1.3) attn.push({
            sev: 'high', title: 'CPA up ' + Math.round((c.cpa / p2 - 1) * 100) + '% on "' + c.name + '"',
            detail: this.money(c.cpa) + ' now vs. ' + this.money(p2) + ' in the previous period.',
            action: 'Review campaign', go: () => this.go('campaigns')
          });
        });
        if (wastedTerms.length) attn.push({
          sev: 'medium', title: this.money(wasted) + ' spent on zero-conversion search terms',
          detail: wastedTerms.length + ' term' + (wastedTerms.length === 1 ? '' : 's') + ' with clicks but no conversions in this period.',
          action: 'Review terms', go: () => this.go('terms')
        });
        vals.ads.attention = attn.slice(0, 4).map(x2 => Object.assign({}, x2, { sevLabel: x2.sev, sevStyle: this.sevChip(x2.sev) }));
        vals.ads.attEmpty = attn.length === 0;
      }

      /* ---- Campaigns ---- */
      if (tab === 'campaigns') {
        vals.showCampaigns = true;
        if (adsSetup) {
          vals.cmp = { setup: true };
          return vals;
        }
        let rows = cs.slice();
        if (s.cmpFilter === 'google') rows = rows.filter(c => c.platform === 'Google Ads');
        if (s.cmpFilter === 'meta') rows = rows.filter(c => c.platform === 'Meta');
        if (s.cmpFilter === 'paused') rows = rows.filter(c => c.status === 'paused');
        if (s.cmpSearch.trim()) rows = rows.filter(c => c.name.toLowerCase().includes(s.cmpSearch.trim().toLowerCase()));
        if (s.cmpSort && s.cmpSort.key) rows = this.sortRows(rows, s.cmpSort);
        const totC = rows.reduce((o, c) => ({ spend: o.spend + c.spend, clicks: o.clicks + c.clicks, impressions: o.impressions + c.impressions, conversions: o.conversions + c.conversions, conv_value: o.conv_value + c.conv_value, budget: o.budget + (c.status === 'enabled' ? c.budget_daily : 0) }), { spend: 0, clicks: 0, impressions: 0, conversions: 0, conv_value: 0, budget: 0 });
        vals.cmp = {
          count: rows.length + ' of ' + cs.length + ' campaigns',
          notEmpty: rows.length > 0,
          totLabel: rows.length + ' campaign' + (rows.length === 1 ? '' : 's'),
          totBudget: this.money(totC.budget) + '/day active',
          totSpend: this.money(totC.spend),
          totClicks: this.fmt(totC.clicks),
          totCtr: totC.impressions ? (totC.clicks / totC.impressions * 100).toFixed(2) + '%' : '—',
          totCpc: totC.clicks ? this.money(totC.spend / totC.clicks) : '—',
          totConv: String(Math.round(totC.conversions)),
          totCpa: totC.conversions ? this.money(totC.spend / totC.conversions) : '—',
          totRoas: totC.spend ? (totC.conv_value / totC.spend).toFixed(2) + 'x' : '—',
          search: s.cmpSearch,
          filters: [['all', 'All'], ['google', 'Google Ads'], ['meta', 'Meta'], ['paused', 'Paused']].map(f => ({
            label: f[1], style: s.cmpFilter === f[0] ? fActive : fBase,
            click: () => this.setState({ cmpFilter: f[0] })
          })),
          empty: rows.length === 0,
          rows: rows.map(c => {
            const on = c.status === 'enabled';
            const editing = s.editBudgetId === c.id;
            const open = s.cmpOpenId === c.id;
            return {
              name: c.name, typeLabel: c.type, platform: c.platform, platformStyle: platformChip(c.platform),
              statusLabel: on ? 'Active' : 'Paused',
              statusTextStyle: { fontSize: '11px', fontWeight: 600, color: on ? '#059669' : '#94a3b8', width: '44px', flexShrink: 0 },
              track: { width: '36px', height: '20px', borderRadius: '9999px', background: on ? '#4f46e5' : '#cbd5e1', position: 'relative', cursor: 'pointer', transition: 'background 0.15s ease', flexShrink: 0 },
              knob: { position: 'absolute', top: '2px', left: on ? '18px' : '2px', width: '16px', height: '16px', borderRadius: '9999px', background: 'white', transition: 'left 0.15s ease' },
              onToggle: () => this.setCampaignStatus(c),
              toggleAria: (on ? 'Pause' : 'Enable') + ' ' + c.name,
              nameColor: on ? '#334155' : '#94a3b8',
              editing, notEditing: !editing,
              budgetFmt: this.money(c.budget_daily),
              budgetVal: s.editBudgetVal,
              onBudgetClick: () => this.setState({ editBudgetId: c.id, editBudgetVal: String(c.budget_daily) }),
              onBudgetInput: e => this.setState({ editBudgetVal: e.target.value }),
              onBudgetKey: e => { if (e.key === 'Enter') this.saveBudget(c); if (e.key === 'Escape') this.setState({ editBudgetId: null }); },
              onBudgetBlur: () => { if (this.state.editBudgetId === c.id) this.saveBudget(c); },
              spendFmt: this.money(c.spend), imprFmt: this.fmt(c.impressions), clicksFmt: this.fmt(c.clicks),
              ctrFmt: c.ctr + '%', cpcFmt: this.money(c.cpc),
              convFmt: String(Math.round(c.conversions)), cpaFmt: c.cpa != null ? this.money(c.cpa) : '—',
              roasFmt: c.roas.toFixed(2) + 'x', roasStyle: roasSt(c.roas),
              isLabel: c.lost_is_budget ? c.lost_is_budget + '%' : '—',
              isStyle: { fontSize: '12.5px', fontWeight: 600, color: c.lost_is_budget >= 15 ? '#b45309' : '#94a3b8' },
              open,
              onOpen: () => this.setState(st2 => ({ cmpOpenId: st2.cmpOpenId === c.id ? null : c.id })),
              openAria: (open ? 'Collapse' : 'Expand') + ' ' + c.name,
              chevStyle: { display: 'inline-flex', color: '#94a3b8', cursor: 'pointer', padding: '6px', transform: open ? 'rotate(180deg)' : 'none', transition: 'transform 0.15s ease' },
              groupsLabel: (c.type === 'Performance Max' ? 'Asset groups' : c.platform === 'Meta' ? 'Ad sets' : 'Ad groups'),
              hasTerms: c.platform === 'Google Ads',
              onViewTerms: () => { this.setState({ termCampaign: c.id, termFilter: 'all' }); this.go('terms'); },
              adGroups: c.adGroups.map(g => ({
                name: g.name, spendFmt: this.money(g.spend), clicksFmt: this.fmt(g.clicks) + ' clicks',
                convFmt: Math.round(g.conversions) + ' conv.', cpaFmt: g.cpa != null ? this.money(g.cpa) + ' CPA' : '— CPA'
              }))
            };
          })
        };
      }

      /* ---- Search Terms ---- */
      if (tab === 'terms') {
        vals.showTerms = true;
        if (adsSetup) {
          vals.trm = { setup: true };
          return vals;
        }
        const scopeCmp = s.termCampaign ? cs.find(c2 => c2.id === s.termCampaign) : null;
        const all = scopeCmp ? data.searchTerms.filter(x2 => x2.campaignId === scopeCmp.id) : data.searchTerms;
        const counts = {
          all: all.length,
          converting: all.filter(x2 => x2.status === 'converting').length,
          wasted: all.filter(x2 => x2.status === 'wasted').length,
          managed: all.filter(x2 => x2.status === 'negative' || x2.status === 'tracked').length
        };
        let rows = all;
        if (s.termFilter === 'converting') rows = all.filter(x2 => x2.status === 'converting');
        if (s.termFilter === 'wasted') rows = all.filter(x2 => x2.status === 'wasted');
        if (s.termFilter === 'managed') rows = all.filter(x2 => x2.status === 'negative' || x2.status === 'tracked');
        if (s.trmMatch !== 'all') rows = rows.filter(x2 => x2.matchType === s.trmMatch);
        if (s.trmSearch.trim()) {
          const q2 = s.trmSearch.trim().toLowerCase();
          rows = rows.filter(x2 => x2.term.toLowerCase().includes(q2) || x2.matchedKeyword.toLowerCase().includes(q2));
        }
        rows = this.sortRows(rows, s.trmSort);
        const totT = rows.reduce((o, x2) => ({ impressions: o.impressions + x2.impressions, clicks: o.clicks + x2.clicks, cost: o.cost + x2.cost, conversions: o.conversions + x2.conversions }), { impressions: 0, clicks: 0, cost: 0, conversions: 0 });
        const per = s.trmPer;
        const pageMax = Math.max(0, Math.ceil(rows.length / per) - 1);
        const page = Math.min(s.trmPage, pageMax);
        const pageRows = rows.slice(page * per, (page + 1) * per);
        const selSet = new Set(s.trmSel);
        const actionableFn = x2 => x2.status === 'converting' || x2.status === 'wasted';
        const selRows = rows.filter(x2 => selSet.has(x2.id) && actionableFn(x2));
        const pageIds = pageRows.filter(actionableFn).map(x2 => x2.id);
        const allChecked = pageIds.length > 0 && pageIds.every(i2 => selSet.has(i2));
        const ck = on => ({ width: '15px', height: '15px', borderRadius: '4px', border: '1.5px solid ' + (on ? '#4f46e5' : '#cbd5e1'), background: on ? '#4f46e5' : 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 });
        const navBtn = en => ({ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '26px', height: '26px', border: '1px solid #e2e8f0', borderRadius: '7px', cursor: en ? 'pointer' : 'default', color: en ? '#334155' : '#cbd5e1', background: 'white' });
        const mtTitle = {
          exact: 'Exact match — the query matched this keyword exactly',
          phrase: 'Phrase match — the query contained this keyword phrase',
          broad: 'Broad match — the query was semantically related to this keyword'
        };
        const stChipMap = {
          converting: { label: 'Converting', bg: '#ecfdf5', fg: '#059669' },
          wasted: { label: 'No conversions', bg: '#fef2f2', fg: '#b91c1c' },
          negative: { label: 'Negative added', bg: '#f1f5f9', fg: '#64748b' },
          tracked: { label: 'Tracking as keyword', bg: '#eef2ff', fg: '#4338ca' }
        };
        vals.trm = {
          kpis: [
            { label: 'Term spend', value: this.money(all.reduce((s2, x2) => s2 + x2.cost, 0)), note: all.length + ' terms in period' },
            { label: 'Wasted spend', value: this.money(wasted), note: counts.wasted + ' zero-conversion terms', accent: '#b91c1c' },
            { label: 'Converting terms', value: String(counts.converting), note: 'clicks that became conversions', accent: '#059669' },
            { label: 'Negatives added', value: String(data.negatives.length), note: 'written back on next sync' }
          ].map(k => ({ label: k.label, value: k.value, note: k.note, valueStyle: { fontSize: '24px', fontWeight: 700, color: k.accent || '#0f172a' } })),
          filters: [['all', 'All'], ['converting', 'Converting'], ['wasted', 'Wasted spend'], ['managed', 'Managed']].map(f => ({
            label: f[1] + ' (' + counts[f[0]] + ')',
            style: s.termFilter === f[0] ? fActive : fBase,
            click: () => this.setState({ termFilter: f[0], trmPage: 0 })
          })),
          scoped: !!scopeCmp,
          scopeLabel: scopeCmp ? 'Campaign: ' + scopeCmp.name : '',
          clearScope: () => this.setState({ termCampaign: null, trmPage: 0 }),
          search: s.trmSearch,
          onSearch: e => this.setState({ trmSearch: e.target.value, trmPage: 0 }),
          match: s.trmMatch,
          onMatch: e => this.setState({ trmMatch: e.target.value, trmPage: 0 }),
          countLine: rows.length ? ('Showing ' + (page * per + 1) + '–' + Math.min(rows.length, (page + 1) * per) + ' of ' + rows.length + ' term' + (rows.length === 1 ? '' : 's') + (rows.length === all.length ? '' : ' (' + all.length + ' total)')) : 'No matching terms',
          empty: rows.length === 0,
          notEmpty: rows.length > 0,
          totLabel: rows.length + ' term' + (rows.length === 1 ? '' : 's'),
          totImpr: this.fmt(totT.impressions), totClicks: this.fmt(totT.clicks), totCost: this.money(totT.cost),
          totConv: String(Math.round(totT.conversions)),
          totCpa: totT.conversions ? this.money(totT.cost / totT.conversions) : '—',
          hasSel: selRows.length > 0, selCount: selRows.length,
          bulkNeg: () => this.bulkNegatives(selRows, 'phrase'),
          bulkTrack: () => this.bulkPromote(selRows),
          clearSel: () => this.setState({ trmSel: [] }),
          allChecked, allCheckStyle: ck(allChecked),
          toggleAll: () => this.setState(st2 => {
            const cur = new Set(st2.trmSel);
            if (allChecked) pageIds.forEach(i2 => cur.delete(i2)); else pageIds.forEach(i2 => cur.add(i2));
            return { trmSel: Array.from(cur) };
          }),
          per: String(per),
          onPer: e => this.setState({ trmPer: +e.target.value, trmPage: 0 }),
          pageLabel: (page + 1) + ' of ' + (pageMax + 1),
          prevPage: () => { if (page > 0) this.setState({ trmPage: page - 1 }); },
          nextPage: () => { if (page < pageMax) this.setState({ trmPage: page + 1 }); },
          prevStyle: navBtn(page > 0), nextStyle: navBtn(page < pageMax),
          rows: pageRows.map(t2 => {
            const c2 = stChipMap[t2.status] || stChipMap.wasted;
            const canSel = actionableFn(t2);
            const checked = canSel && selSet.has(t2.id);
            return {
              term: t2.term, matched: t2.matchedKeyword, campaign: t2.campaign,
              matchLabel: t2.matchType,
              matchTitle: mtTitle[t2.matchType] || '',
              matchStyle: { fontSize: '10px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', color: '#64748b', background: '#f1f5f9', padding: '1px 6px', borderRadius: '4px', cursor: 'help' },
              imprFmt: this.fmt(t2.impressions), clicksFmt: this.fmt(t2.clicks), costFmt: this.money(t2.cost),
              convFmt: t2.conversions ? String(t2.conversions) : '0',
              cpaFmt: t2.cpa != null ? this.money(t2.cpa) : '—',
              statusLabel: c2.label,
              statusStyle: { fontSize: '10.5px', fontWeight: 600, background: c2.bg, color: c2.fg, padding: '2px 8px', borderRadius: '4px', whiteSpace: 'nowrap' },
              actionable: canSel, canSel,
              checked, checkStyle: ck(checked),
              selAria: (checked ? 'Deselect ' : 'Select ') + t2.term,
              onSel: () => this.setState(st2 => { const cur = new Set(st2.trmSel); if (cur.has(t2.id)) cur.delete(t2.id); else cur.add(t2.id); return { trmSel: Array.from(cur) }; }),
              negOpen: s.negMenuFor === t2.id,
              onNegMenu: () => this.setState(st2 => ({ negMenuFor: st2.negMenuFor === t2.id ? null : t2.id })),
              negPhrase: () => this.addNegative(t2, 'phrase'),
              negExact: () => this.addNegative(t2, 'exact'),
              negBroad: () => this.addNegative(t2, 'broad'),
              onTrack: () => this.promoteTerm(t2),
              onCampaign: () => { this.setState({ cmpSearch: t2.campaign, cmpFilter: 'all', cmpOpenId: t2.campaignId }); this.go('campaigns'); },
              negAria: 'Add ' + t2.term + ' as negative keyword',
              trackAria: 'Track ' + t2.term + ' as organic keyword'
            };
          })
        };
      }

      /* ---- Attribution ---- */
      if (tab === 'attribution') {
        vals.showAttribution = true;
        if (adsSetup) {
          vals.att = { setup: true };
          return vals;
        }
        const rowsA = data.attribution;
        const maxConv = Math.max.apply(null, rowsA.map(r2 => Math.max(r2.ads_conversions, r2.ga4_key_events)).concat([1]));
        vals.att = {
          totals: {
            ads: String(Math.round(t.conversions)), ga4: String(Math.round(t.ga4_key_events)),
            adsVal: this.money(t.conv_value), ga4Val: this.money(t.ga4_revenue),
            gap: (t.conversions ? Math.round((t.ga4_key_events - t.conversions) / t.conversions * 100) : 0) + '%'
          },
          rows: rowsA.map(r2 => ({
            name: r2.name, platform: r2.platform, platformStyle: platformChip(r2.platform),
            onCampaign: () => { this.setState({ cmpSearch: r2.name, cmpFilter: 'all', cmpOpenId: r2.id }); this.go('campaigns'); },
            ads: String(Math.round(r2.ads_conversions)), ga4: String(Math.round(r2.ga4_key_events)),
            adsBar: { height: '6px', borderRadius: '9999px', background: '#4f46e5', width: Math.max(2, Math.round(r2.ads_conversions / maxConv * 100)) + '%' },
            ga4Bar: { height: '6px', borderRadius: '9999px', background: '#10b981', width: Math.max(2, Math.round(r2.ga4_key_events / maxConv * 100)) + '%' },
            adsVal: this.money(r2.ads_value), ga4Val: this.money(r2.ga4_revenue),
            gapLabel: (r2.gap_pct > 0 ? '+' : '') + r2.gap_pct + '%',
            gapStyle: { fontSize: '11.5px', fontWeight: 600, color: Math.abs(r2.gap_pct) <= 25 ? '#64748b' : '#b45309' }
          })),
          pages: data.landingPages.map(lp => ({
            url: lp.url, campaign: lp.campaign,
            sessions: this.fmt(lp.sessions),
            erLabel: Math.round(lp.engagedRate * 100) + '%',
            erBar: { height: '5px', borderRadius: '9999px', background: lp.engagedRate >= 0.5 ? '#10b981' : lp.engagedRate >= 0.35 ? '#f59e0b' : '#dc2626', width: Math.round(lp.engagedRate * 100) + '%' },
            keyEvents: String(lp.keyEvents), revenue: this.money(lp.revenue)
          }))
        };
      }
    }


        /* ============ ALERTS ============ */
    if (tab === 'alerts') {
      vals.showAlerts = true;
      const feed = data.feed;
      const counts = {
        all: feed.length,
        high: feed.filter(f => f.severity === 'high').length,
        medium: feed.filter(f => f.severity === 'medium').length,
        acked: feed.filter(f => f.acknowledged).length
      };
      const fBase = { padding: '4px 12px', fontSize: '12px', fontWeight: 500, borderRadius: '6px', cursor: 'pointer', color: '#64748b' };
      const fActive = Object.assign({}, fBase, { background: 'white', color: '#0f172a', boxShadow: '0 1px 2px rgba(0,0,0,0.05)' });
      const rows = feed.filter(f => {
        if (s.alFilter === 'all') return true;
        if (s.alFilter === 'acked') return f.acknowledged;
        return f.severity === s.alFilter;
      });
      const kindMap = { anomaly: 'Anomaly', ranking: 'Ranking', backlink: 'Backlink', technical: 'Technical', system: 'System', ai: 'AI Visibility', ads: 'Ads' };
      vals.al = {
        hasUnacked: feed.some(f => !f.acknowledged),
        filters: [['all', 'All'], ['high', 'High'], ['medium', 'Medium'], ['acked', 'Acknowledged']].map(f => ({
          label: f[1] + ' (' + counts[f[0] === 'acked' ? 'acked' : f[0]] + ')',
          style: s.alFilter === f[0] ? fActive : fBase,
          click: () => { this.setState({ alFilter: f[0] }); this.pushNav({ alFilter: f[0] }); }
        })),
        empty: rows.length === 0,
        rows: rows.map(f => ({
          title: f.title, detail: f.detail, date: f.ts,
          kindLabel: kindMap[f.kind] || f.kind,
          sevLabel: f.severity, sevStyle: this.sevChip(f.severity),
          acknowledged: f.acknowledged, showAck: !f.acknowledged && f.severity !== 'info',
          ack: () => this.ackAlert(f.id),
          rowStyle: { display: 'flex', alignItems: 'center', gap: '14px', padding: '14px 20px', borderTop: '1px solid #f1f5f9', opacity: f.acknowledged ? 0.55 : 1 }
        }))
      };
    }


        /* ============ SETTINGS ============ */
    if (tab === 'settings') {
      if (!vals.canManageSettings) {
        setTimeout(() => this.go('overview'), 0);
        vals.showSettings = false;
        return vals;
      }
      vals.showSettings = true;
      const u = data.usage;
      const prefs = s.prefs || data.prefs;
      const toggle = on => ({
        track: { width: '40px', height: '22px', borderRadius: '9999px', background: on ? '#4f46e5' : '#cbd5e1', position: 'relative', cursor: 'pointer', transition: 'background 0.15s ease', flexShrink: 0 },
        knob: { position: 'absolute', top: '2px', left: on ? '20px' : '2px', width: '18px', height: '18px', borderRadius: '9999px', background: 'white', transition: 'left 0.15s ease' }
      });
      const scopeFor = { 'Position tracking (SERP Standard)': 'positions', 'Backlinks summary + new/lost deltas': 'backlinks', 'Site audit crawl (OnPage)': 'audit', 'Keyword volume refresh (Labs)': 'keywords' };
      const crawlCfg = s.crawlCfg || data.crawl;
      const ws = s.wsDraft || data.workspace;
      const team = s.teamDraft || data.team;
      const notif = s.notifDraft || data.notifications;
      const ai = s.aiDraft || data.aiConfig;
      const sec = s.secDraft || data.security;
      const dp = s.dataDraft || data.dataPrefs;
      const syncCfg = s.syncCfg || data.syncConfig;
      const platConn = s.platConn || data.platformConnectors;
      const rulesArr = (s.rules || data.alertRules || []);
      const cur = s.settingsSub || 'general';

      /* ---- sub-tab bar ---- */
      const invitedCount = team.filter(m => m.status === 'invited').length;
      const enabledRules = rulesArr.filter(r => r.on).length;
      const overCap = u.est_monthly > s.budgetCap;
      const subDefs = [
        ['general', 'General', null],
        ['team', 'Team & Access', invitedCount ? String(team.length) : String(team.length)],
        ['connections', 'Connections', null],
        ['automation', 'Automation', null],
        ['budget', 'Usage & Budget', overCap ? '!' : null],
        ['alerts', 'Alerts & Rules', String(enabledRules)],
        ['ai', 'AI Summaries', null],
        ['security', 'Security & Data', null]
      ];
      const tabBase = { display: 'flex', alignItems: 'center', gap: '7px', padding: '9px 4px', marginRight: '20px', fontSize: '13.5px', fontWeight: 500, color: '#64748b', cursor: 'pointer', borderBottom: '2px solid transparent', whiteSpace: 'nowrap' };
      const tabOn = Object.assign({}, tabBase, { color: '#4f46e5', fontWeight: 600, borderBottom: '2px solid #4f46e5' });

      const cadenceLabels = { '12h': 'Every 12 hours', daily: 'Daily', weekly: 'Weekly', biweekly: 'Every 2 weeks', monthly: 'Monthly', manual: 'Manual only' };
      const mkOpts = keys => keys.map(k => ({ value: k, label: cadenceLabels[k] }));
      const SYNC_MODS = [
        ['positions', 'Position tracking', 'SERP Standard queue · ~$0.0015/keyword', ['daily', 'weekly', 'biweekly', 'monthly', 'manual'], 'positions'],
        ['backlinks', 'Backlinks', 'Summary + new/lost deltas', ['weekly', 'biweekly', 'monthly', 'manual'], 'backlinks'],
        ['audit', 'Site audit crawl', 'OnPage crawl · ~$0.00125/page', ['weekly', 'biweekly', 'monthly', 'manual'], 'audit'],
        ['keywords', 'Keyword volumes', 'Labs volume / KD / intent refresh', ['weekly', 'monthly', 'manual'], 'keywords'],
        ['ads', 'Ads (Google + GA4)', 'GAQL reports + GA4 runReport · $0', ['12h', 'daily', 'manual'], null],
        ['ai', 'AI visibility', 'LLM mention checks across 5 models', ['weekly', 'biweekly', 'monthly', 'manual'], 'ai']
      ];

      const PLAT = [
        ['linkedin', 'LinkedIn', 'LinkedIn Marketing API — impressions & CTR for Organic Social'],
        ['reddit', 'Reddit', 'Reddit API — community & post engagement'],
        ['youtube', 'YouTube', 'YouTube Data API — video impressions & watch signals'],
        ['x', 'X (Twitter)', 'X API — post impressions & reach'],
        ['facebook', 'Facebook', 'Meta Graph API — page & post reach'],
        ['instagram', 'Instagram', 'Meta Graph API — reach & engagement'],
        ['meta_ads', 'Meta Ads', 'Meta Marketing API — paid campaign metrics']
      ];
      const roleOptions = ['Owner', 'Admin', 'Analyst'].map(r => ({ value: r, label: r }));
      const inviteRoleOptions = ['Admin', 'Analyst'].map(r => ({ value: r, label: r }));
      const routeOptions = [['none', 'Don\u2019t notify'], ['email', 'Email immediately'], ['digest', 'Weekly digest'], ['slack', 'Slack']].map(x => ({ value: x[0], label: x[1] }));
      const q = data.budget.quotas;
      const bar = (used, limit, color) => ({ pct: Math.min(100, Math.round((used / limit) * 100)), style: { height: '100%', borderRadius: '9999px', background: color, width: Math.min(100, Math.round((used / limit) * 100)) + '%' } });

      vals.st = {
        /* sub-tabs */
        subTabs: subDefs.map(d => ({
          label: d[1], badge: d[2],
          badgeStyle: { fontSize: '10.5px', fontWeight: 700, padding: '1px 7px', borderRadius: '9999px', background: d[2] === '!' ? '#fee2e2' : (cur === d[0] ? '#eef2ff' : '#f1f5f9'), color: d[2] === '!' ? '#b91c1c' : (cur === d[0] ? '#4f46e5' : '#94a3b8') },
          style: cur === d[0] ? tabOn : tabBase, click: () => this.setSettingsSub(d[0])
        })),
        gen: cur === 'general', team: cur === 'team', conn: cur === 'connections',
        auto: cur === 'automation', bud: cur === 'budget', alr: cur === 'alerts',
        aiT: cur === 'ai', sec: cur === 'security',

        /* ---- general ---- */
        domain: data.project.domain, vertical: data.project.vertical,
        projectIdLabel: 'project: ' + data.project.id,
        competitors: data.project.competitors,
        gsc: s.creds.gsc, ga4: s.creds.ga4,
        credsSaveLabel: s.credsSaved ? 'Saved \u2713' : 'Save credentials',
        ws: ws, savedWs: s.savedWs ? 'Saved \u2713' : 'Save workspace',
        seatPct: Math.min(100, Math.round((ws.seats_used / ws.seats_total) * 100)),
        toggleEmail: toggle(!!prefs.email_alerts),
        toggleDigest: toggle(!!prefs.weekly_digest),

        /* ---- team ---- */
        teamRows: team.map((m, idx) => {
          const isOwner = m.role === 'Owner' || idx === 0;
          return {
            name: m.name, email: m.email, initials: m.initials,
            isInvited: m.status === 'invited', role: isOwner ? 'Owner' : m.role,
            roleOptions: isOwner ? roleOptions : inviteRoleOptions, isOwner: isOwner,
            canDelete: !isOwner,
            lastLabel: m.status === 'invited' ? 'Invite pending' : 'Active ' + (m.last_active || ''),
            avatarStyle: { width: '36px', height: '36px', borderRadius: '9999px', background: m.status === 'invited' ? '#f1f5f9' : '#e0e7ff', color: m.status === 'invited' ? '#94a3b8' : '#4338ca', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '13px', fontWeight: 600, flexShrink: 0 },
            setRole: e => this.changeRole(m.id, e.target.value),
            remove: () => this.removeMember(m.id)
          };
        }),
        inviteEmail: s.inviteEmail, inviteUsername: s.inviteUsername, invitePassword: s.invitePassword,
        inviteRole: s.inviteRole || 'Analyst', inviteRoleOptions, roleOptions, createUserError: s.createUserError || null,
        inviteMode: s.inviteMode || 'email',
        isEmailMode: (s.inviteMode || 'email') === 'email',
        isDirectMode: (s.inviteMode || 'email') === 'direct',
        inviteModeEmailStyle: { padding: '5px 12px', fontSize: '12.5px', fontWeight: (s.inviteMode || 'email') === 'email' ? 600 : 500, background: (s.inviteMode || 'email') === 'email' ? 'white' : 'transparent', color: (s.inviteMode || 'email') === 'email' ? '#4f46e5' : '#64748b', borderRadius: '6px', cursor: 'pointer', boxShadow: (s.inviteMode || 'email') === 'email' ? '0 1px 2px rgba(0,0,0,0.06)' : 'none' },
        inviteModeDirectStyle: { padding: '5px 12px', fontSize: '12.5px', fontWeight: (s.inviteMode || 'email') === 'direct' ? 600 : 500, background: (s.inviteMode || 'email') === 'direct' ? 'white' : 'transparent', color: (s.inviteMode || 'email') === 'direct' ? '#4f46e5' : '#64748b', borderRadius: '6px', cursor: 'pointer', boxShadow: (s.inviteMode || 'email') === 'direct' ? '0 1px 2px rgba(0,0,0,0.06)' : 'none' },
        inviteStatusMsg: s.inviteStatusMsg || null,
        inviteErrorMsg: s.inviteErrorMsg || null,
        invitationRows: (data.invitations || []).map(inv => ({
          id: inv.id,
          email: inv.email,
          role: inv.role,
          invitedBy: inv.invited_by || 'Owner',
          expiresAtLabel: inv.expires_at ? ('Expires ' + inv.expires_at.slice(0, 10)) : 'Pending',
          resend: () => this.resendInvite(inv.id),
          revoke: () => this.revokeInvite(inv.id)
        })),
        hasInvitations: !!(data.invitations && data.invitations.length > 0),

        /* ---- connections ---- */
        // Final-review finding: every connector card was hardcoded green with a static
        // "All healthy" header, regardless of the real SyncLog status -- an error/never-run
        // connector would still render as healthy. Derive the card color and header text
        // from the real status instead.
        dataConnectors: data.connectors.map(c => {
          // Real SyncLog.status values (apps/sync/models.py SyncStatus) are
          // never/running/success/error -- NOT "ok". Final-review finding: comparing
          // against 'ok' meant no connector ever matched, so every successfully-synced
          // connector rendered red -- the opposite of honest, worse than the hardcoded
          // green it replaced. Only "error" is unhealthy; never/running are neutral (a
          // connector that hasn't synced yet isn't "broken").
          const ok = c.status === 'success';
          const bad = c.status === 'error';
          return {
            name: c.name, last: c.last_sync || 'never', records: this.fmt(c.records) + ' records',
            error: c.error,
            cardStyle: bad
              ? { padding: '14px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '10px' }
              : { padding: '14px', background: ok ? '#f0fdf4' : '#f8fafc', border: '1px solid ' + (ok ? '#bbf7d0' : '#e2e8f0'), borderRadius: '10px' },
            dotStyle: { width: '8px', height: '8px', borderRadius: '9999px', background: bad ? '#dc2626' : (ok ? '#22c55e' : '#cbd5e1') },
            recordsStyle: { fontSize: '12px', color: bad ? '#b91c1c' : (ok ? '#15803d' : '#64748b'), marginTop: '2px' }
          };
        }),
        healthLabel: data.connectors.length === 0
          ? 'No sources synced yet.'
          : (data.connectors.some(c => c.status === 'error') ? 'Some sources need attention.' : 'All healthy.'),
        platRows: PLAT.map(p => {
          const on = !!platConn[p[0]]; const tg = toggle(on);
          return {
            key: p[0], name: p[1], desc: p[2], connected: on,
            statusLabel: on ? 'Connected' : 'Not connected',
            statusStyle: { fontSize: '11px', fontWeight: 600, padding: '2px 9px', borderRadius: '9999px', background: on ? '#ecfdf5' : '#f1f5f9', color: on ? '#059669' : '#94a3b8' },
            actionLabel: on ? 'Disconnect' : 'Connect',
            actionStyle: { padding: '7px 14px', border: '1px solid ' + (on ? '#e2e8f0' : '#c7d2fe'), background: on ? 'white' : '#eef2ff', color: on ? '#64748b' : '#4338ca', borderRadius: '8px', fontSize: '13px', fontWeight: 600, cursor: 'pointer' },
            toggle: () => this.togglePlatform(p[0])
          };
        }),

        /* ---- automation: sync + crawl ---- */
        // data.sync.next_run/.day are honestly null (no scheduler exists yet) -- avoid the
        // literal "null (null)" string JS string-concatenation would otherwise produce.
        nextRun: data.sync.next_run ? (data.sync.next_run + ' (' + data.sync.day + ')') : 'not yet scheduled',
        lastRun: data.sync.last_run || 'never',
        syncRows: SYNC_MODS.map(m => ({
          label: m[1], desc: m[2], value: syncCfg[m[0]] || 'weekly', options: mkOpts(m[3]),
          onChange: e => this.editSyncCfg(m[0], e.target.value),
          canSync: !!m[4] && !syncing, run: () => this.startSync(m[4])
        })),
        crawlMax: String(crawlCfg.maxPages), crawlFreq: crawlCfg.frequency, crawlExcl: crawlCfg.excludedPaths,
        jsToggle: toggle(!!crawlCfg.jsRendering),
        robotsToggle: toggle(!!crawlCfg.respectRobots),
        crawlSaveLabel: s.crawlSaved ? 'Saved \u2713' : 'Save crawl settings',

        /* ---- usage & budget ---- */
        mtd: this.money(u.month_to_date), budget: this.money(u.budget),
        budgetPct: Math.min(100, Math.round((u.month_to_date / u.budget) * 100)),
        projected: this.money(u.est_monthly),
        budgetCap: s.budgetCap, savedBudget: s.savedBudget ? 'Saved \u2713' : '',
        enforceToggle: toggle(!!s.budgetEnforce),
        capBar: { height: '100%', borderRadius: '9999px', background: overCap ? '#f59e0b' : '#10b981', width: Math.min(100, Math.round((u.est_monthly / s.budgetCap) * 100)) + '%' },
        overCap: overCap,
        quotaGa4: bar(q.ga4_tokens_used, q.ga4_tokens_limit, '#6366f1'),
        quotaGa4Label: this.fmt(q.ga4_tokens_used) + ' / ' + this.fmt(q.ga4_tokens_limit) + ' tokens today',
        quotaAds: bar(q.ads_ops_used, q.ads_ops_limit, '#0ea5e9'),
        quotaAdsLabel: q.ads_ops_used + ' / ' + this.fmt(q.ads_ops_limit) + ' ops/day',
        quotaGsc: bar(q.gsc_queries_used, q.gsc_queries_limit, '#8b5cf6'),
        quotaGscLabel: q.gsc_queries_used + ' / ' + this.fmt(q.gsc_queries_limit) + ' queries/day',
        usageRows: u.items.map(item => ({
          module: item.module, cadence: item.cadence,
          estFmt: item.est == null ? (item.note || '\u2014') : this.money(item.est),
          canSync: !!scopeFor[item.module] && !syncing,
          run: () => this.startSync(scopeFor[item.module])
        })),

        /* ---- alerts & rules + notifications ---- */
        ruleRows: rulesArr.map(r => {
          const tg = toggle(r.on);
          return {
            label: r.label, threshold: r.threshold, unit: r.unit || '\u2014',
            labelStyle: { fontSize: '13px', color: r.on ? '#334155' : '#94a3b8', flex: 1 },
            track: tg.track, knob: tg.knob,
            toggle: () => this.editRule(r.id, { on: !r.on }),
            setThreshold: e => this.editRule(r.id, { threshold: Math.max(1, parseInt(e.target.value, 10) || 1) })
          };
        }),
        notif: notif, savedNotif: s.savedNotif ? 'Saved \u2713' : 'Save notifications',
        notifEmailToggle: toggle(!!notif.email_enabled),
        notifWeeklyToggle: toggle(!!notif.weekly_digest),
        notifSlackToggle: toggle(!!notif.slack_enabled),
        routeOptions,

        /* ---- ai summaries ---- */
        ai: ai, savedAi: s.savedAi ? 'Saved \u2713' : 'Save AI settings',
        modelOptions: [['gpt-4o', 'GPT-4o'], ['gpt-4o-mini', 'GPT-4o mini'], ['claude-3-5-sonnet', 'Claude 3.5 Sonnet'], ['claude-3-5-haiku', 'Claude 3.5 Haiku']].map(x => ({ value: x[0], label: x[1] })),
        providerOptions: ['OpenAI', 'Anthropic'].map(x => ({ value: x, label: x })),
        toneOptions: ['Concise', 'Detailed', 'Executive'].map(x => ({ value: x, label: x })),
        aiCadenceOptions: mkOpts(['weekly', 'biweekly', 'monthly']),

        /* ---- security & data ---- */
        twofaToggle: toggle(!!sec.twofa), ssoToggle: toggle(!!sec.sso),
        sessions: sec.sessions.map(x => ({
          device: x.device, meta: x.ip + ' · ' + x.location + ' · ' + x.last,
          current: x.current, revoke: () => this.revokeSession(x.id)
        })),
        tokens: sec.tokens.map(x => ({
          name: x.name, prefix: x.prefix + '\u2026', meta: 'Created ' + x.created + (x.last_used ? ' · last used ' + x.last_used : ' · never used'),
          revoke: () => this.revokeToken(x.id)
        })),
        newTokenName: s.newTokenName,
        dp: dp, savedData: s.savedData ? 'Saved \u2713' : 'Save data preferences',
        formatOptions: ['CSV', 'XLSX', 'JSON'].map(x => ({ value: x, label: x })),
        retentionOptions: [['12m', '12 months'], ['24m', '24 months'], ['36m', '36 months'], ['forever', 'Keep forever']].map(x => ({ value: x[0], label: x[1] }))
      };
    }

    return vals;
  }


}
