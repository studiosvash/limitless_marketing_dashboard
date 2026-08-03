  state = {
    tab: 'overview', seoOpen: true, adsOpen: true,
    cmpFilter: 'all', cmpSearch: '', cmpOpenId: null, cmpSort: { key: 'spend', dir: -1 },
    editBudgetId: null, editBudgetVal: '', termFilter: 'all', termCampaign: null,
    trmSearch: '', trmMatch: 'all', trmSort: { key: 'cost', dir: -1 }, trmSel: [], trmPage: 0, trmPer: 10, negMenuFor: null,
    /* null until GET /api/projects answers — there is nothing to guess from before that.
       This used to default to the literal slug 'fusehealth', which is wrong two different
       ways: on a deployment whose database has no such project every boot-time request
       (page data, sync log, sync resume) fired at a 404, and on one that DOES have it the
       app silently opened a project the user never chose. See boot(). */
    projectId: null, projects: [],
    addSiteOpen: false, addSiteDomain: '', addSiteName: '', addSiteError: null, addSiteBusy: false,
    addSiteStep: 1, addSiteGsc: '', addSiteGa4: '', addSiteDataforseo: '',
    addSiteGscOptions: [], addSiteChecking: false, addSiteCheckResult: null,
    range: '28d',
    cache: {}, loading: true, error: null, chartHoverIndex: null,
    /* Real SyncLog rows ({name, status, records, last_sync, error}) for the selected project,
       read from GET /api/projects/<id>/settings -> `connectors`. Kept OUT of `cache` on
       purpose: fetchTab('settings') re-seeds every Settings draft as a side effect, and a
       badge refresh must never throw away an unsaved edit in the Settings tab. `syncLogFor`
       pins the rows to the project they were read for, so switching sites never shows the
       previous site's freshness. See srcBadge(). */
    syncLog: null, syncLogFor: null,
    ncOpen: false,
    sync: { active: false, progress: 0, step: '', cost: 0, steps: [], warnings: [] },
    syncPanelOpen: false,
    freshness: 'Weekly · Mon',
    doQuery: '', doData: null, doLoading: false, doError: null, doSel: [], doTracked: [],
    /* Domain Overview "send to Position Tracking" destination picker. The lookup is for an
       ARBITRARY domain — usually a competitor's — so the project the keywords belong in is
       frequently NOT the one currently selected in the topbar. Sending silently to
       state.projectId filed competitor keywords into whatever project happened to be open.
       doPickRows holds the pending rows until a destination is confirmed. */
    doPickOpen: false, doPickRows: null, doPickPid: null,
    delProjOpen: false, delProjText: '', delProjBusy: false,
    explorerQ: '', explorerLoc: 'United States', research: null, researching: false,
    matchType: 'broad', selectedKws: [], sendOpen: false, exportOpen: false, sendSub: null, newListName: '', kwLists: [], toast: null, showLists: false,
    resVolMin: 0, resKdMin: 0, resKdMax: 100, resIntents: [], resIncl: '', resExcl: '', resOpenFilter: null, resGroup: null, resGroupMode: 'number', resDrawer: null,
    kwSeg: null, kwSort: { key: 'clicks', dir: -1 },
    blFilter: 'all', blSort: { key: 'rank', dir: -1 },
    blTab: 'overview', blFollow: 'all', gapOnly: true,
    offSort: { key: 'sessions', dir: -1 },
    pgSort: { key: 'clicks', dir: -1 },
    auSub: 'overview', auSev: 'all', auCat: 'all', auSearch: '', auOpen: null, auView: 'table', auPgSearch: '', auPgSort: { key: 'score', dir: 1 },
    /* Crawled Pages table, 0-indexed. The table used to render `rows.slice(0, 40)` full stop:
       on a 1 139-page site that hid 96% of a payload the browser already had, and the footer
       told you to "export the full list" to see your own pages. */
    auPgPage: 0,
    /* id of the audit check whose affected-page list is fully expanded (null = preview only) */
    auAllPages: null,
    auCmpA: null, auCmpB: null, auCmpFilter: 'all', auProg: { score: true, errors: true, warnings: true, notices: false, pages: false },
    aiSub: 'visibility', /* keys must track mentionPlatforms' ids (llm_mentions_service.MENTION_PLATFORMS), not llmPlatforms' four-engine ids -- the two lists are deliberately separate */ aiPlat: { google: true, chat_gpt: true }, aiOpen: null,
    aiWiz: 1, aiWizBrand: null, aiWizAliases: null, aiWizComps: null, aiWizCompInput: '', aiWizSel: null, aiWizCustom: '', aiWizBusy: false,
    aiTgOpen: false, aiListFilter: 'all', aiListsOpen: false, aiNewPlName: '',
    aiComposerOpen: false, aiComposerText: '', aiComposerList: null,
    aiCfgOpen: null, aiCfgDraft: null, aiPromptSel: [],
    aiExpQ: '', aiExploring: false, aiExp: null, aiExpSel: [], aiExpAddOpen: false,
    aiKwQ: '', aiKwSeg: 'all', aiKwSel: [], aiKwAddOpen: false,
    aiInspQ: '', aiInspecting: false, aiInspEntry: null,
    crawlCfg: null, crawlSaved: false, auPage: null, rules: null,
    alFilter: 'all',
    creds: { gsc: '', ga4: '', dataforseo: '' }, credsFor: null, credsSaved: false,
    credsTesting: false, credsTestResult: null,
    prefs: null, prefsFor: null,
    settingsSub: 'general', setFor: null,
    wsDraft: null, notifDraft: null, aiDraft: null, secDraft: null, dataDraft: null, teamDraft: null,
    syncCfg: null, budgetCap: 75, budgetEnforce: true,
    savedWs: false, savedNotif: false, savedAi: false, savedData: false, savedBudget: false,
    inviteEmail: '', inviteRole: 'Analyst', newTokenName: '',
    inviteMode: 'email', inviteStatusMsg: null, inviteErrorMsg: null,
    acceptInviteToken: null, acceptEmail: '', acceptRole: '', acceptInvitedBy: '', acceptUsername: '', acceptPassword: '', acceptError: null, acceptSuccess: null,
    cpwOpen: false, cpwOld: '', cpwNew: '', cpwNew2: '', cpwErr: false, cpwMsg: '', cpwBusy: false
  };

  /* ---------- constants ---------- */
  get VALID() { return ['overview', 'seo', 'domain_overview', 'keywords', 'positioning', 'backlinks', 'offsite', 'pages', 'ai', 'ads', 'campaigns', 'terms', 'attribution', 'alerts', 'settings']; }
  get SEOTABS() { return ['seo', 'domain_overview', 'keywords', 'positioning', 'backlinks', 'offsite', 'pages', 'ai']; }
  get ADSTABS() { return ['ads', 'campaigns', 'terms', 'attribution']; }
  get RES() { return { overview: 'overview', seo: 'seo', domain_overview: 'seo', keywords: 'keywords', positioning: 'positions', backlinks: 'backlinks', offsite: 'offsite', pages: 'audit', ai: 'ai', ads: 'ads', campaigns: 'ads', terms: 'ads', attribution: 'ads', alerts: 'alerts', settings: 'settings' }; }

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
    /* Outside-click dismissal for the topbar notification centre. Escape is already
       handled by installA11y's single keydown listener (_onEsc, extended there rather
       than duplicated); this is a different event type, so it needs its own listener.
       Anything inside [data-nc-root] is the bell's own trigger or panel — clicking it
       must not self-dismiss, otherwise the trigger would close what it just opened. */
    this._onDocClick = (e) => {
      if (!this._alive || !this.state.ncOpen) return;
      const t = e.target;
      if (t && t.closest && t.closest('[data-nc-root]')) return;
      this.setState({ ncOpen: false });
    };
    document.addEventListener('click', this._onDocClick);
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
    document.removeEventListener('click', this._onDocClick);
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
      if (s.addSiteOpen || s.negMenuFor || s.sendOpen || s.exportOpen || s.ncOpen) {
        this.setState({ addSiteOpen: false, negMenuFor: null, sendOpen: false, exportOpen: false, ncOpen: false });
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
    const range = ['7d', '28d', '90d'].includes(this.props.defaultRange) ? this.props.defaultRange : this.state.range;
    /* Keyword lists come from the SERVER now (site-scoped, shared by the team) — they are
       fetched per project in openProject via loadKeywordLists. localStorage is read exactly
       once more, as a MIGRATION source: lists built before this change live only in this
       browser, and abandoning them would delete a colleague's research without warning. */
    let kwLists = [{ id: 'l1', name: 'Priority targets', keywords: [] }];
    /* Which project to open. A remembered choice is a real prior decision by this user, so
       it is opened straight away and its data loads in parallel with the project list. With
       NO remembered choice there is nothing to go on, so the app waits for /api/projects
       instead of guessing: the old code fell back to the hardcoded slug 'fusehealth', which
       either 404'd every boot request on a deployment without that project, or silently
       opened a project the user never picked on one that had it. `loading` is already true
       in the initial state, so the wait shows the skeleton rather than an empty screen. */
    let pid = null;
    try { pid = localStorage.getItem('fh_selected_project') || null; } catch (e) {}
    this.setState({ tab, range, kwLists, projectId: pid, seoOpen: this.state.seoOpen || this.SEOTABS.includes(tab), adsOpen: this.state.adsOpen || this.ADSTABS.includes(tab) });
    this._hist = [Object.assign(this.navSnapshot(), { tab, projectId: pid })];
    this._histIdx = 0;

    const openProject = (id) => {
      this.fetchTab(tab, id, range, false);
      if (tab !== 'alerts') this.fetchTab('alerts', id, range, false);
      this.loadSyncLog(id);
      this.resumeActiveSync(id);
      this.loadKeywordLists(id);
    };

    api.get('/api/projects').then(ps => {
      if (!this._alive) return;
      this.setState({ projects: ps });
      /* No projects at all is a real answer, not a pending one — stop the skeleton rather
         than spinning forever on a workspace whose first action is "add a site". */
      if (!ps.length) { this.setState({ loading: false }); return; }
      const resolved = ps.some(p => p.id === pid) ? pid : ps[0].id;
      /* Persisted here, not only in setProject(): until now the remembered-project key was
         written ONLY when the user used the topbar switcher, so a single-project workspace
         never remembered anything and re-ran this resolution on every reload. */
      try { localStorage.setItem('fh_selected_project', resolved); } catch (e) {}
      if (resolved === pid) return;                    // already loading the right one
      /* The remembered project is gone (deleted, or this browser last used a different
         deployment). Clear `error` as well as switching: its 404 may already have painted
         the error state over a view that is about to receive real data. */
      this.setState({ projectId: resolved, error: null });
      openProject(resolved);
    }).catch(err => {
      /* The site switcher, the "add site" duplicate check and every project-scoped label
         are built from this list. If it never arrives the user is stranded on whichever
         project was remembered, with no visible reason — so this one gets a toast even
         though nobody pressed a button. */
      if (!this._alive) return;
      this.notify(this.errText(err, 'Could not load your site list'));
    });
    if (pid) openProject(pid);
    /* Deliberately silent: this is a boot-time prefetch of a static autocomplete file for the
       Position Tracking location box, which positioning.js already falls back to a short
       built-in country list for when `allUsCities` is absent. Nothing the user asked for has
       failed, and a toast about a city list on every page load would be pure noise. */
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
            next.creds = {
              gsc: data.credentials.gsc_property, ga4: data.credentials.ga4_property_id,
              dataforseo: data.credentials.dataforseo_target_domain,
            };
            next.credsFor = pid;
            next.credsTestResult = null;
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
            next.budgetCap = data.budget.cap;
            next.budgetEnforce = data.budget.enforce;
            next.setFor = pid;
          }
          return next;
        });
      })
      /* Guarded on BOTH the project and the tab this response belongs to. A rejection for a
         view the user has since moved off must not paint "Couldn't load this view" over the
         one they are now looking at — boot() can have a stale remembered project's 404 land
         after the correct project's data has already arrived, and because renderVals() bails
         out early on `s.error`, that leaves a fully-loaded page showing an error box. */
      .catch(e => {
        if (!this._alive || this.state.projectId !== pid) return;
        this.setState(s => (s.tab === tab
          ? { loading: false, error: (e && e.message) || 'Request failed' }
          : {}));
      });
  }

  /* Loads the per-connector SyncLog rows that every "Data source" badge is built from.
     Deliberately NOT fetchTab('settings'): that path seeds wsDraft/notifDraft/teamDraft/…
     from the response, so re-running it after every sync would silently discard a half-typed
     Settings form. This writes one isolated state slot and nothing else.

     Silent on failure by design — nobody pressed a button, and the consequence of a failure
     is simply that no badge renders (srcBadge() returns show:false). A toast about a
     provenance lookup would be noise, and a badge built from a failed read would be a guess. */
  loadSyncLog(pid) {
    pid = pid || this.state.projectId;
    window.FuseAPI.get('/api/projects/' + pid + '/settings')
      .then(d => {
        if (!this._alive) return;
        this.setState({ syncLog: (d && d.connectors) || [], syncLogFor: pid });
      })
      .catch(() => { if (this._alive) this.setState({ syncLog: null, syncLogFor: pid }); });
  }

  fetchLiveSerp(kw, location) {
    this.setState({ ptSerpKw: kw, ptSerpLoading: true, ptSerpData: null, ptSerpError: null });
    /* `project` is sent so the backend can attribute this call's DataForSEO charge to the
       right project. Without it every live SERP lookup wrote a connector_costs row with an
       empty site_id — real money no project's Usage & Budget panel could ever show. The
       backend resolves it leniently, so a missing project degrades attribution, not the
       lookup itself. */
    window.FuseAPI.post('/api/live-serp', { keyword: kw, location, project: this.state.projectId })
      .then(res => {
        if (!this._alive || this.state.ptSerpKw !== kw) return;
        if (res.error) {
          this.setState({ ptSerpLoading: false, ptSerpError: res.error });
        } else {
          this.setState({ ptSerpLoading: false, ptSerpData: res.items || [] });
        }
      })
      .catch(e => {
        if (!this._alive || this.state.ptSerpKw !== kw) return;
        this.setState({ ptSerpLoading: false, ptSerpError: e.message || 'Failed to fetch SERP' });
      });
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
      auSub: snap.auSub || 'overview', auOpen: null, auAllPages: null,
      aiSub: snap.aiSub || 'visibility', aiOpen: null,
      seoOpen: this.state.seoOpen || this.SEOTABS.includes(snap.tab), adsOpen: this.state.adsOpen || this.ADSTABS.includes(snap.tab), error: null,
      selectedKws: [], sendOpen: false, exportOpen: false, sendSub: null, showLists: false
    });
    try { if (('#' + snap.tab) !== location.hash) history.replaceState(null, '', '#' + snap.tab); } catch (e) {}
    this.fetchTab(snap.tab, snap.projectId, this.state.range, false);
    if (pidChanged && snap.tab !== 'alerts') this.fetchTab('alerts', snap.projectId, this.state.range, false);
    if (pidChanged) { this.setState({ syncLog: null, syncLogFor: snap.projectId }); this.loadSyncLog(snap.projectId); }
    setTimeout(() => { this._navApplying = false; }, 0);
  }
  histBack() { if (this._hist && this._histIdx > 0) this.applyNav(this._histIdx - 1); }
  histFwd() { if (this._hist && this._histIdx < this._hist.length - 1) this.applyNav(this._histIdx + 1); }

  toggleAddSite() {
    this.setState(s => ({
      addSiteOpen: !s.addSiteOpen, addSiteStep: 1, addSiteDomain: '', addSiteName: '', addSiteError: null,
      addSiteGsc: '', addSiteGa4: '', addSiteDataforseo: '', addSiteGscOptions: [],
      addSiteChecking: false, addSiteCheckResult: null,
    }));
  }

  /* The registration form of a domain — the client-side twin of
     pipeline/utils/site_ids.normalize_domain(). Keep the two in step: this one decides what the
     user sees, that one decides what gets stored, and a disagreement shows up as "That site is
     already added" on a domain the dropdown doesn't list (or worse, the reverse).

     https://premierstaff.com   http://premierstaff.com   premierstaff.com
     https://www.premierstaff.com   http://www.premierstaff.com   www.premierstaff.com
     all mean ONE site: premierstaff.com. Stripping `www.` is the part that was missing, and it
     is why premierstaff.com and www.premierstaff.com could both be added as separate projects. */
  _normalizeDomain(value) {
    return String(value || '')
      .trim().toLowerCase()
      .replace(/^sc-domain:/, '')
      .replace(/^[a-z][a-z0-9+.-]*:\/\//, '')  // any scheme, not just http(s)
      .replace(/^[^/@]*@/, '')                 // user:pass@
      .split('/')[0]                           // path
      .split(':')[0]                           // port
      .replace(/\.+$/, '')                     // fully-qualified trailing dot
      .replace(/^www\./, '');
  }

  /* Normalised the same way everywhere it's used (submit validation, the duplicate check, and
     the connection-check call) so the three agree. */
  _addSiteDomain() {
    return this._normalizeDomain(this.state.addSiteDomain);
  }

  /* Step 1 -> 2. This step is pure client-side validation, matching what addSiteSubmit always
     checked before creating anything — moved here so a site with an obviously bad domain, or
     one already added, never reaches the Connections step at all. */
  addSiteNext() {
    const domain = this._addSiteDomain();
    if (!domain || !/^[a-z0-9][a-z0-9\-\.]*\.[a-z]{2,}$/.test(domain)) {
      this.setState({ addSiteError: 'Enter a valid domain, e.g. example.com' });
      return;
    }
    // Normalise the stored side too, not just the typed side. A project registered before
    // normalize_domain existed still carries `www.` in its domain, and comparing the raw value
    // would let the user add its non-www twin -- the exact duplicate this check exists to stop.
    const dupe = this.state.projects.find(p => this._normalizeDomain(p.domain) === domain);
    if (dupe) {
      this.setState({ addSiteError: 'That site is already added as ' + dupe.domain });
      return;
    }
    this.setState({ addSiteStep: 2, addSiteError: null });
    // Populate the GSC property dropdown as soon as the Connections step opens, so the field
    // is a picker from the first moment rather than free text the user might mistype (Search
    // Console reads a bare domain as a URL-prefix property, not the sc-domain: property most
    // accounts actually own). This alone is a live GSC call but not GA4/DataForSEO, so it does
    // not need to wait for the explicit "Check all connections" press.
    window.FuseAPI.post('/api/connection-check', { domain, include_optional: false })
      .then(result => {
        if (!this._alive) return;
        const gscCheck = (result.checks || []).find(c => c.id === 'gsc');
        if (gscCheck && gscCheck.options) this.setState({ addSiteGscOptions: gscCheck.options });
      })
      .catch(() => {}); // best-effort prefill; the Check button below still works standalone
  }
  addSiteBack() { this.setState({ addSiteStep: 1, addSiteError: null }); }

  /* The "Check all connections" button. Calls the same live GSC/GA4/DataForSEO probe Settings
     uses, but BEFORE the site exists — POST /api/connection-check takes a bare domain, not a
     project slug, specifically so this can run pre-creation. Its GSC check also returns every
     verified property the connected account can query; addSiteGscOptions renders those as a
     dropdown so the property can be picked rather than typed, which is the one field a typo
     silently breaks (Search Console reads a bare domain as a URL-prefix property, not the
     sc-domain: property most accounts actually own). */
  addSiteCheck() {
    if (this.state.addSiteChecking) return;
    this.setState({ addSiteChecking: true, addSiteCheckResult: null });
    window.FuseAPI.post('/api/connection-check', {
      domain: this._addSiteDomain(),
      gsc_property: this.state.addSiteGsc,
      ga4_property_id: this.state.addSiteGa4,
      dataforseo_target: this.state.addSiteDataforseo,
      include_optional: false,
    }).then(result => {
      if (!this._alive) return;
      const gscCheck = result.checks.find(c => c.id === 'gsc');
      this.setState(s => ({
        addSiteChecking: false, addSiteCheckResult: result,
        addSiteGscOptions: (gscCheck && gscCheck.options) || s.addSiteGscOptions,
        // Auto-fill the box with the resolved property so "Add site" persists what was
        // actually verified, not whatever partial string the user was still typing.
        addSiteGsc: (gscCheck && gscCheck.resolved) || s.addSiteGsc,
      }));
    }).catch(err => {
      if (!this._alive) return;
      this.setState({ addSiteChecking: false });
      this.notify(this.errText(err, 'Could not run the connection check'));
    });
  }

  /* Shared submit path for both "Add site & start sync" and "Skip for now" — they differ only
     in whether credentials ride along. Skipping still creates the site (per the design: GA4/
     GSC-backed pages simply stay empty until Settings -> Connections is filled in later). */
  _addSiteCreate(withCreds) {
    if (this.state.addSiteBusy) return;
    const domain = this._addSiteDomain();
    const body = { domain, name: this.state.addSiteName.trim() || undefined };
    if (withCreds) {
      if (this.state.addSiteGsc.trim()) body.gsc_property = this.state.addSiteGsc.trim();
      if (this.state.addSiteGa4.trim()) body.ga4_property_id = this.state.addSiteGa4.trim();
      if (this.state.addSiteDataforseo.trim()) body.dataforseo_target_domain = this.state.addSiteDataforseo.trim();
    }
    this.setState({ addSiteBusy: true, addSiteError: null });
    window.FuseAPI.post('/api/projects', body)
      .then(p => {
        if (!this._alive) return;
        this.setState(s => ({
          projects: s.projects.concat([p]), addSiteBusy: false, addSiteOpen: false,
          addSiteDomain: '', addSiteName: '', addSiteStep: 1,
          addSiteGsc: '', addSiteGa4: '', addSiteDataforseo: '', addSiteCheckResult: null,
        }));
        if (withCreds && p.gsc_connected === false) {
          this.notify('Site added, but not found in Search Console. Please connect account in Settings.');
        } else if (!withCreds) {
          this.notify('Added ' + p.domain + ' — GA4/GSC not connected yet, so those pages will stay empty until you add them in Settings → Connections.');
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
  addSiteSubmit() { this._addSiteCreate(true); }
  addSiteSkip() { this._addSiteCreate(false); }

  /* Render vals for the Add-domain modal. Same result-row shape as Settings' credsTestRows
     (same tone map, same dot style) so the two connection-check surfaces look identical. */
  addSiteVals(s) {
    const step1 = s.addSiteStep === 1, step2 = s.addSiteStep === 2;
    const tone = {
      ok: ['#d1fae5', '#047857', '✓'], fail: ['#fee2e2', '#b91c1c', '✗'],
      absent: ['#f1f5f9', '#94a3b8', '—'], unknown: ['#fef3c7', '#b45309', '?'],
    };
    const checkRows = (s.addSiteCheckResult ? s.addSiteCheckResult.checks : []).map(c => {
      const t = tone[c.state] || tone.absent;
      return {
        label: c.label, detail: c.detail,
        dotStyle: { display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '18px', height: '18px', borderRadius: '50%', background: t[0], color: t[1], fontSize: '11px', fontWeight: 700, flexShrink: 0 },
        dotText: t[2],
      };
    });
    return {
      step1, step2, stepNum: s.addSiteStep, stepLabel: step1 ? 'Site details' : 'Connections',
      gscOptions: s.addSiteGscOptions, gsc: s.addSiteGsc, ga4: s.addSiteGa4, dataforseo: s.addSiteDataforseo,
      checkLabel: s.addSiteChecking ? 'Checking…' : 'Check all connections',
      checkShown: !!s.addSiteCheckResult, checkRows,
      backLabel: step1 ? 'Cancel' : '← Back',
      backAction: step1 ? (() => this.toggleAddSite()) : (() => this.addSiteBack()),
      skipLabel: s.addSiteBusy ? 'Adding…' : 'Skip for now',
      primaryLabel: step1 ? 'Next' : (s.addSiteBusy ? 'Adding…' : 'Add site & start sync'),
      primaryAction: step1 ? (() => this.addSiteNext()) : (() => this.addSiteSubmit()),
    };
  }
  setProject(pid) {
    try { localStorage.setItem('fh_selected_project', pid); } catch (e) {}
    this.pushNav({ projectId: pid, research: null, kwSeg: null, blFilter: 'all', alFilter: 'all' });
    this.setState({ projectId: pid, research: null, kwSeg: null, blFilter: 'all', alFilter: 'all', crawlCfg: null, crawlSaved: false, auPage: null, rules: null, termCampaign: null, cmpSearch: '', cmpOpenId: null, editBudgetId: null });
    this.fetchTab(this.state.tab, pid, this.state.range, false);
    if (this.state.tab !== 'alerts') this.fetchTab('alerts', pid, this.state.range, false);
    /* Freshness is per-project, so it has to be re-read here — otherwise every Data source
       badge would keep showing the previous site's sync dates. syncLogFor guards the window
       between the switch and the response landing. */
    this.setState({ syncLog: null, syncLogFor: pid });
    this.loadSyncLog(pid);
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
  startSync(scope, preTaskId, force) {
    if (this.state.sync.active && (!this.state.sync.projectId || this.state.sync.projectId === this.state.projectId)) return;
    const pid = this.state.projectId;
    const activeScope = scope || 'all';

    if (preTaskId != null) {
      // Task already created server-side — skip POST /sync and go straight to polling.
      this._pollSyncTask(preTaskId, activeScope, pid, 0, []);
      return;
    }

    window.FuseAPI.post('/api/projects/' + pid + '/sync', { scope: activeScope, force: !!force })
      .then(t => {
        if (!this._alive) return;
        /* Everything in this scope synced within the last 24 hours, so the server created no
           run — there was nothing to fetch. Ask rather than silently doing nothing: "I pressed
           Refresh and it ignored me" is worse than one prompt. This is the only place `force`
           is ever set. */
        if (t.fresh) {
          if (window.confirm('This was last fetched ' + this.agoText(t.last_synced) + '.'
              + '\n\nRefetch anyway? It will call the APIs again and re-spend any credits they cost.')) {
            this.startSync(scope, null, true);
          }
          return;
        }
        if (t.warnings && t.warnings.length) {
          // Shown once, at start, rather than repeated on every poll tick: "N steps will be
          // skipped because X credential is missing" is a fact about the whole run, not a
          // per-second update.
          t.warnings.forEach(w => this.notify(w));
        }
        this._pollSyncTask(t.task_id, activeScope, pid, t.est_cost || 0, t.steps || []);
      })
      .catch(err => { if (this._alive) this.notify(err.detail || 'Could not start sync'); });
  }

  /* "40 minutes ago" for the already-fetched prompt. Coarse on purpose — the user is deciding
     whether a refetch is worth it, not reading a timestamp. */
  agoText(iso) {
    const then = Date.parse(iso);
    if (isNaN(then)) return 'recently';
    const mins = Math.max(0, Math.round((Date.now() - then) / 60000));
    if (mins < 1) return 'moments ago';
    if (mins < 60) return mins + (mins === 1 ? ' minute ago' : ' minutes ago');
    const hrs = Math.round(mins / 60);
    if (hrs < 24) return hrs + (hrs === 1 ? ' hour ago' : ' hours ago');
    const days = Math.round(hrs / 24);
    return days + (days === 1 ? ' day ago' : ' days ago');
  }

  /* Stop the run in flight. The server marks the row cancelled and kills the sync process;
     this does NOT tear down the poll loop itself — letting the existing poller observe
     status='cancelled' keeps one code path in charge of finishing a run. The only immediate
     local change is the button label, so the click has visible feedback. */
  cancelSync() {
    const pid = this.state.sync.projectId || this.state.projectId;
    if (!pid || this.state.sync.stopping) return;
    this.setState(st => ({ sync: Object.assign({}, st.sync, { stopping: true }) }));
    window.FuseAPI.post('/api/projects/' + pid + '/sync/cancel', {})
      .then(r => {
        if (!this._alive) return;
        if (!r.cancelled) {
          /* Not a failure: it finished while the click was in flight. The poller is about to
             report it done, so only the label needs putting back. */
          this.setState(st => ({ sync: Object.assign({}, st.sync, { stopping: false }) }));
          this.notify(r.reason || 'That refresh had already finished');
        }
      })
      .catch(err => {
        if (!this._alive) return;
        this.setState(st => ({ sync: Object.assign({}, st.sync, { stopping: false }) }));
        this.notify((err && err.detail) || 'Could not stop the refresh');
      });
  }

  /* Shared by a fresh start (startSync) and resuming after a reload (boot -> resumeActiveSync).
     Runs at 500ms for the first ~6s (fast enough that a short page-scope sync still feels
     live), then backs off to 2s. At 500ms against a handful of gunicorn workers, sustained
     polling was itself part of "everything feels frozen when I click around" — a request that
     takes longer than the interval piles up behind the next one and competes with whatever
     page GET the user just triggered. A 20-30 minute "all" run does not need 500ms resolution
     for its remaining 29 minutes. */
  _pollSyncTask(taskId, scope, pid, estCost, initialSteps) {
    if (this._iv) { clearInterval(this._iv); this._iv = null; }

    this.setState({
      sync: {
        active: true, scope, progress: 0.02, step: (initialSteps && initialSteps[0]) || 'Starting…',
        cost: estCost, projectId: pid, startTime: Date.now(), steps: [], warnings: [],
      },
    });

    const POLL_GIVE_UP = 6;   // consecutive failed ticks before giving up on this run
    const SLOWDOWN_AFTER_MS = 6000;
    const FAST_MS = 500, SLOW_MS = 2000;
    let pollFails = 0;
    let inFlight = false;     // a slow tick must not stack a second request behind it
    let slowedDown = false;
    const startedAt = Date.now();

    const tick = () => {
      if (!this._alive) { clearInterval(this._iv); return; }
      if (inFlight) return;
      inFlight = true;
      window.FuseAPI.get('/api/tasks/' + taskId).then(st => {
        inFlight = false;
        if (!this._alive) { clearInterval(this._iv); return; }
        pollFails = 0;

        if (!slowedDown && Date.now() - startedAt > SLOWDOWN_AFTER_MS) {
          slowedDown = true;
          clearInterval(this._iv);
          this._iv = setInterval(tick, SLOW_MS);
        }

        if (st.done) {
          clearInterval(this._iv); this._iv = null;
          const wasCancelled = st.status === 'cancelled';
          this.setState(s => {
            const cache = {};
            Object.keys(s.cache).forEach(k2 => { if (k2.indexOf(pid + ':') !== 0) cache[k2] = s.cache[k2]; });
            return {
              sync: { active: false, scope: null, progress: 1, step: 'Done', cost: estCost, projectId: null, startTime: null, steps: [], warnings: [], stopping: false },
              /* A cancelled run did NOT refresh the page, so the freshness pill must not claim
                 it did. Whatever it wrote before stopping is still real, hence the refetch. */
              freshness: wasCancelled ? s.freshness : 'Just now',
              cache,
            };
          });
          this.fetchTab(this.state.tab, pid, this.state.range, true);
          if (this.state.tab !== 'alerts') this.fetchTab('alerts', pid, this.state.range, false);
          /* The whole point of a refresh is that the freshness changed — re-read the
             SyncLog rows so every Data source badge moves with the data it describes
             (including a connector whose run failed inside an otherwise "Done" sync). */
          this.loadSyncLog(pid);
          const proj = this.state.projects.find(p => p.id === pid) || {};
          const dom = proj.domain || pid;
          if (wasCancelled) {
            const left = Math.max(0, (st.total || 0) - (st.completed || 0));
            this.notify('Refresh stopped for ' + dom + (left ? ' — ' + left + ' step(s) did not run' : ''));
          } else {
          const scopeNotif = { domain_checks: 'Domain checks refreshed for ' + dom, audit: 'Crawl complete — Site Audit refreshed for ' + dom, positions: 'Positioning data refreshed for ' + dom, positions_new: 'New keywords measured for ' + dom, positioning_new: 'New keywords measured for ' + dom, positioning: 'Positioning data refreshed for ' + dom, keywords: 'Keywords data refreshed for ' + dom, backlinks: 'Backlinks data refreshed for ' + dom, ads: 'Ads data refreshed for ' + dom, ai: 'AI Optimization data refreshed for ' + dom, overview: 'Overview data refreshed for ' + dom, seo: 'SEO data refreshed for ' + dom };
          this.notify(scopeNotif[scope] || (scope === 'all' ? ('All modules refreshed for ' + dom) : (scope + ' refreshed for ' + dom)));
          }
        } else {
          this.setState(s => ({ sync: Object.assign({}, s.sync, {
            active: true, scope, progress: st.progress, step: st.step, cost: estCost, projectId: pid,
            steps: st.steps || [], elapsed: st.elapsed || 0,
          }) }));
        }
      }).catch(err => {
        inFlight = false;
        if (!this._alive) { clearInterval(this._iv); return; }
        pollFails++;
        if (pollFails < POLL_GIVE_UP) return;
        clearInterval(this._iv); this._iv = null;
        /* The sync itself may well still be running server-side — we have only lost sight
           of it — so the message says that instead of claiming the refresh failed, and the
           progress bar is cleared rather than left frozen at whatever % it reached. */
        this.setState({ sync: { active: false, scope: null, progress: 0, step: '', cost: estCost, projectId: null, startTime: null, steps: [], warnings: [] } });
        const why = (err && err.detail) ? ' (' + err.detail + ')' : '';
        this.notify('Lost track of the refresh' + why + ' — the sync may still be running. Reload the page to check.');
      });
    };
    this._iv = setInterval(tick, FAST_MS);
  }

  /* Called once from boot(). A sync used to become invisible on any hard reload — the client
     lost the task_id and GET /api/tasks/<id> needs one — which read exactly like "the sync
     stopped" even though a 20-30 minute run was still working server-side. Reaping runs first
     on the server side of this endpoint, so a row orphaned by an old crash is never mistaken
     for a live one. */
  resumeActiveSync(pid) {
    window.FuseAPI.get('/api/projects/' + pid + '/sync/active').then(a => {
      if (!this._alive || !a || a.task_id == null) return;
      if (this.state.sync.active) return; // a fresh startSync already beat us to it
      this._pollSyncTask(a.task_id, a.scope || 'all', pid, 0, []);
    }).catch(() => {}); // best-effort; a normal boot must never fail over this
  }

  /* ---------- keyword explorer ---------- */
  runResearch() {
    const q = this.state.explorerQ.trim();
    if (!q || this.state.researching) return;
    this.setState({ researching: true, selectedKws: [], sendOpen: false, exportOpen: false, sendSub: null });
    window.FuseAPI.post('/api/research', { project: this.state.projectId, keywords: q.split(','), location: this.state.explorerLoc })
      .then(r => { if (this._alive) { r.seeds = q.toLowerCase(); this.setState({ researching: false, research: r, matchType: 'broad', resGroup: null, resDrawer: null, resVolMin: 0, resKdMin: 0, resKdMax: 100, resIntents: [], resIncl: '', resExcl: '', resOpenFilter: null }); this.pushNav({ research: r }); } })
      .catch(err => { if (this._alive) this.setState({ researching: false, error: this.errText(err, 'Keyword research request failed') }); });
  }

  /* ---------- domain overview ---------- */

  /* The market a Domain Overview is read in. Single source of truth: the *project's*
     own location (projects[].location), which is exactly what positioning.js feeds the
     live-SERP drawer (ptWs.location = proj.location || 'United States'). Domain Overview
     previously used state.explorerLoc — the Keyword Explorer's dropdown — so clicking
     "Analyze" on a SERP result silently re-ran the lookup in a different market than the
     SERP the user was looking at. The project location wins because Position Tracking,
     the SERP drawer and the tracked-keyword writes (`site.location` server-side) are all
     already keyed to it; the explorer dropdown is a transient, per-search control. */
  doLocation() {
    const p = (this.state.projects || []).find(x => x.id === this.state.projectId) || {};
    return p.location || 'United States';
  }

  /* Google's `near` param needs a city/region and silently does nothing for a bare
     country name -- so a country-only location (the common case: most projects are just
     "United States") used to get dropped from "Open in Google" links entirely. `gl` is
     the real country-bias param, so every location -- country-only or city-level -- now
     maps to at least one filter, and city/state selections get both. Shared by the
     Position Tracking SERP drawer and the Keyword Research drawer so both "Open in
     Google" links stay in sync with the location the results were actually pulled for. */
  googleSerpLocationParam(location) {
    const COUNTRY_CODES = { 'United States': 'us', 'Canada': 'ca', 'United Kingdom': 'uk', 'Australia': 'au' };
    const loc = location || '';
    if (!loc) return '';
    if (COUNTRY_CODES[loc]) return '&gl=' + COUNTRY_CODES[loc];
    const near = loc.replace(/^United States - /, '');
    return '&near=' + encodeURIComponent(near) + '&gl=us';
  }

  runDomainOverview() {
    const q = this.state.doQuery.trim();
    if (!q || this.state.doLoading) return;
    this.setState({ doLoading: true, doError: null, doSel: [] });
    /* `project` lets the backend mark which returned keywords this project already tracks.
       Without it every row would offer Track even for keywords already on the list. */
    window.FuseAPI.post('/api/domain-overview', { target: q, location: this.doLocation(), project: this.state.projectId })
      .then(r => { if (this._alive) this.setState({ doLoading: false, doData: r, doError: r.error }); })
      .catch(e => { if (this._alive) this.setState({ doLoading: false, doError: 'Failed to fetch domain overview: ' + e }); });
  }

  analyzeUrlInDomainOverview(url) {
    if (!url) return;
    this.setState({ doQuery: url }, () => {
      this.go('domain_overview');
      this.runDomainOverview();
    });
  }

  /* keys the session-local "tracked from this screen" set by project, so switching
     projects never carries a mark across */
  doTrackKey(pid, kw) { return pid + '\u0000' + kw; }

  /* rows currently ticked in the Domain Overview keyword table, in sendKwsToTracking's
     expected shape ({kw, volume, kd, cpc, intent}). The ranked-keywords endpoint carries
     no keyword-difficulty figure, so `kd` is deliberately left absent rather than zeroed. */
  doSelectedRows() {
    const sel = this.state.doSel || [];
    if (!sel.length) return [];
    const kws = (this.state.doData && this.state.doData.keywords) || [];
    return kws.filter(k => sel.indexOf(k.keyword) >= 0)
      .map(k => ({ kw: k.keyword, volume: k.volume, cpc: k.cpc, intent: k.intent }));
  }

  /* Entry point for BOTH the per-row "+ Track" and the bulk "Track selected (N)".
     It does not send anything itself — it asks where to send first.

     Why: Domain Overview looks up an arbitrary domain, typically a competitor's. The
     keywords it returns usually belong in a DIFFERENT project from the one selected in
     the topbar (looking up eventstaff.com while the premierstaff.com project is open is
     the normal case, not an edge case). Sending to state.projectId silently filed them
     into whatever happened to be open, with only a toast naming the project afterwards.

     One project configured => no choice to make, so no dialog; it sends straight through.
     Asking would be pure friction with a single possible answer. */
  trackDomainOverviewKws(rows) {
    if (!rows || !rows.length) return;
    const projects = this.state.projects || [];
    if (projects.length > 1) {
      this.setState({
        doPickOpen: true,
        doPickRows: rows,
        /* Default to the active project: it is the most likely answer and keeps the
           one-project behaviour familiar. The user still has to confirm. */
        doPickPid: this.state.projectId
      });
      return;
    }
    this.doSendTrackedKws(rows, this.state.projectId);
  }

  doPickCancel() { this.setState({ doPickOpen: false, doPickRows: null, doPickPid: null }); }
  doPickSet(pid) { this.setState({ doPickPid: pid }); }
  doPickConfirm() {
    const rows = this.state.doPickRows;
    const pid = this.state.doPickPid;
    if (!rows || !rows.length || !pid) { this.doPickCancel(); return; }
    this.setState({ doPickOpen: false, doPickRows: null, doPickPid: null });
    this.doSendTrackedKws(rows, pid);
  }

  /* Reuses sendKwsToTracking for the POST + cache invalidation + refetch + toast, and
     only adds what is specific to this screen: clearing the selection and remembering
     which rows this session sent. `pid` is the CONFIRMED destination, which may differ
     from the active project — every mark and every cache key below uses it, not
     state.projectId, or a keyword sent to project B would show as tracked under A. */
  doSendTrackedKws(rows, pid) {
    if (!rows || !rows.length || !pid) return;
    const sent = this.sendKwsToTracking(pid, rows);
    this.setState(st => {
      const marks = (st.doTracked || []).slice();
      rows.forEach(r => {
        const key = this.doTrackKey(pid, r.kw);
        if (marks.indexOf(key) < 0) marks.push(key);
      });
      return { doSel: [], doTracked: marks };
    });
    /* The "Tracked" mark above is optimistic. sendKwsToTracking reports the outcome (and
       toasts the reason on failure), so a refused write takes its mark back instead of
       leaving the row claiming to be tracked when nothing was stored. */
    if (sent && sent.then) {
      sent.then(ok => {
        if (!this._alive || ok) return;
        const keys = rows.map(r => this.doTrackKey(pid, r.kw));
        this.setState(st => ({ doTracked: (st.doTracked || []).filter(k => keys.indexOf(k) < 0) }));
      });
    }
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

  /* Lists are server state now (site-scoped, shared). Every mutation already updates
     this.state.kwLists and then calls persistLists with the complete new array — the same
     wholesale model the localStorage version used — so persistence is one PUT of everything.
     A failed save is SAID OUT LOUD and the server copy re-fetched, so the screen never
     drifts from what is actually stored. */
  persistLists(lists) {
    const pid = this.state.projectId;
    if (!pid) return;
    window.FuseAPI.put('/api/projects/' + pid + '/keyword-lists', {
      lists: lists.map(l => ({
        name: l.name,
        keywords: (l.keywords || []).map(k => typeof k === 'string' ? { keyword: k }
          : { keyword: k.kw || k.keyword, volume: k.volume, kd: k.kd, cpc: k.cpc, intent: k.intent })
      }))
    }).catch(err => {
      if (!this._alive) return;
      this.notify(this.errText(err, 'Could not save keyword lists'));
      this.loadKeywordLists(pid);
    });
  }

  loadKeywordLists(pid) {
    window.FuseAPI.get('/api/projects/' + pid + '/keyword-lists').then(resp => {
      if (!this._alive) return;
      let lists = (resp && resp.lists) || [];
      /* One-time migration: lists created before they moved server-side exist only in this
         browser's localStorage. If the server has none and this browser has real ones, push
         them up ONCE, then drop the local copy so it can never shadow the shared state. An
         empty local default ("Priority targets" with no keywords) is not worth migrating. */
      if (!lists.length) {
        let legacy = [];
        try { legacy = JSON.parse(localStorage.getItem('fh_keyword_lists') || '[]') || []; } catch (e) {}
        const real = legacy.filter(l => (l.keywords || []).length);
        if (real.length) {
          legacy = legacy.map(l => Object.assign({}, l, {
            keywords: (l.keywords || []).map(k => typeof k === 'string' ? { kw: k } : k) }));
          lists = legacy;
          this.persistLists(legacy);
          this.notify('Keyword lists moved to the server — they are now shared with your team');
        }
      }
      try { localStorage.removeItem('fh_keyword_lists'); } catch (e) {}
      if (!lists.length) lists = [{ id: 'l1', name: 'Priority targets', keywords: [] }];
      this.setState({ kwLists: lists.map(l => ({ id: l.id || l.name, name: l.name, keywords: l.keywords || [] })) });
    }).catch(() => { /* keep the in-memory default; the next navigation retries */ });
  }

  // add a batch of keywords to a project's tracking (Position Tracking)
  sendKwsToTracking(pid, rows) {
    if (!rows.length) return;
    const payload = {
      /* serpFeatures/competition ride along so the tracked table keeps showing what the
         research view knew — they were silently dropped here for months and saved as NULL. */
      keywords: rows.map(r => ({ kw: r.kw, volume: r.volume, kd: r.kd, cpc: r.cpc, intent: r.intent,
        serpFeatures: r.serpFeatures || [], competition: r.competition }))
    };
    /* The .catch() used to sit BEFORE this .then(), which converted every rejection into a
       resolution: a POST the server had refused still marked the rows tracked, threw away the
       cached keyword/positioning tabs and toasted "N keywords sent to Position Tracking".
       The success path now runs only on success. Resolves true/false so callers that mark
       rows optimistically (trackDomainOverviewKws) can undo the mark. */
    return window.FuseAPI.post('/api/projects/' + pid + '/keywords', payload).then(() => {
      if (!this._alive) return true;
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
      /* Deliberately silent: the keywords were already saved and the user has been told so.
         This is only a background re-read to refresh the per-project keyword counts in the
         switcher; if it fails the counts are stale until the next load, which is not worth
         contradicting the success toast the user just received. */
      window.FuseAPI.get('/api/projects').then(ps => { if (this._alive) this.setState({ projects: ps }); }).catch(() => {});
      const proj = (this.state.projects.find(p => p.id === pid) || {}).domain || 'project';
      this.notify(rows.length + ' keyword' + (rows.length === 1 ? '' : 's') + ' sent to Position Tracking · ' + proj);
      return true;
    }).catch(err => {
      if (this._alive) this.notify(this.errText(err, 'Could not send those keywords to Position Tracking'));
      return false;
    });
  }

  addKwsToList(listId, rows) {
    /* Full row objects, not bare names: volume/KD/intent captured at save time are what
       lets the server count list keywords in the portfolio KPIs. */
    const kws = rows.map(r => ({ kw: r.kw, volume: r.volume, kd: r.kd, cpc: r.cpc, intent: r.intent }));
    const lists = this.state.kwLists.map(l => {
      if (l.id !== listId) return l;
      const merged = l.keywords.slice();
      const have = new Set(merged.map(k => (k.kw || k).toLowerCase()));
      kws.forEach(k => { if (!have.has(k.kw.toLowerCase())) { merged.push(k); have.add(k.kw.toLowerCase()); } });
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
    const lists = this.state.kwLists.concat([{ id, name: nm,
      keywords: rows.map(r => ({ kw: r.kw, volume: r.volume, kd: r.kd, cpc: r.cpc, intent: r.intent })) }]);
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
    const lists = this.state.kwLists.map(l => l.id === listId ? Object.assign({}, l, { keywords: l.keywords.filter(k => (k.kw || k) !== kw) }) : l);
    this.persistLists(lists);
    this.setState({ kwLists: lists });
  }

  sendListToTracking(listId) {
    const l = this.state.kwLists.find(x => x.id === listId);
    if (!l || !l.keywords.length) { this.notify('This list is empty'); return; }
    this.sendKwsToTracking(this.state.projectId, l.keywords.map(k => typeof k === 'string' ? { kw: k }
      : { kw: k.kw, volume: k.volume, kd: k.kd, cpc: k.cpc, intent: k.intent }));
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
      .catch(err => { if (this._alive) this.notify(this.errText(err, 'Could not update that campaign')); });
  }
  saveBudget(c) {
    const pid = this.state.projectId;
    const v = parseFloat(this.state.editBudgetVal);
    if (!v || v <= 0 || Math.round(v) === c.budget_daily) { this.setState({ editBudgetId: null }); return; }
    window.FuseAPI.post('/api/projects/' + pid + '/ads/budget', { campaignId: c.id, budgetDaily: v })
      .then(r => { if (!this._alive) return; this.setState({ editBudgetId: null }); this.notify('Daily budget for "' + c.name + '" set to $' + r.budgetDaily); this.adsInvalidate(pid); })
      .catch(err => { if (this._alive) { this.setState({ editBudgetId: null }); this.notify(this.errText(err, 'Could not update that budget')); } });
  }
  addNegative(t, matchType) {
    const pid = this.state.projectId;
    const mt = matchType || 'phrase';
    this.setState({ negMenuFor: null });
    window.FuseAPI.post('/api/projects/' + pid + '/ads/negatives', { term: t.term, matchType: mt, campaignId: t.campaignId })
      .then(() => { if (!this._alive) return; this.notify('"' + t.term + '" added as a ' + mt + '-match negative — written back to Google Ads on next sync'); this.adsInvalidate(pid); })
      .catch(err => { if (this._alive) this.notify(this.errText(err, 'Could not add that negative')); });
  }

  /* One press of a bulk button must produce one message, never one per row — but a plain
     Promise.all rejects on the first failure and reports nothing about the requests that
     already succeeded, so the user is told "could not add negatives" while some of them were
     in fact written. Each request is therefore settled on its own (Promise.allSettled is
     ES2020; this file targets ES2017, hence the two-argument .then), and the batch reports:
       all ok      → the original success line;
       none ok     → the server's reason, once;
       partial     → how many landed, and the rows that failed stay selected so the button can
                     simply be pressed again for exactly those.
     The ads cache is invalidated whenever at least one write landed, because the tab is now
     out of date either way. */
  bulkSettle(results) {
    const failed = results.filter(r => !r.ok);
    return { failed: failed, okCount: results.length - failed.length, total: results.length };
  }

  bulkNegatives(list, matchType) {
    const pid = this.state.projectId;
    if (!list.length) return;
    const mt = matchType || 'phrase';
    Promise.all(list.map(t => window.FuseAPI.post('/api/projects/' + pid + '/ads/negatives', { term: t.term, matchType: mt, campaignId: t.campaignId })
      .then(function () { return { ok: true, t: t }; }, function (err) { return { ok: false, t: t, err: err }; })))
      .then(results => {
        if (!this._alive) return;
        const r = this.bulkSettle(results);
        if (r.okCount) this.adsInvalidate(pid);
        this.setState({ trmSel: r.failed.map(x => x.t.id) });
        if (!r.failed.length) {
          this.notify(r.total + ' negative keyword' + (r.total === 1 ? '' : 's') + ' queued — written back via CampaignCriterionService on next sync');
        } else if (!r.okCount) {
          this.notify(this.errText(r.failed[0].err, 'Could not add those negatives'));
        } else {
          this.notify(r.okCount + ' of ' + r.total + ' negatives queued. ' + r.failed.length + ' failed — still selected, try again.');
        }
      });
  }

  bulkPromote(list) {
    const pid = this.state.projectId;
    if (!list.length) return;
    Promise.all(list.map(t => window.FuseAPI.post('/api/projects/' + pid + '/ads/promote', { term: t.term })
      .then(function () { return { ok: true, t: t }; }, function (err) { return { ok: false, t: t, err: err }; })))
      .then(results => {
        if (!this._alive) return;
        const r = this.bulkSettle(results);
        if (r.okCount) this.adsInvalidate(pid);
        this.setState({ trmSel: r.failed.map(x => x.t.id) });
        if (!r.failed.length) {
          this.notify(r.total + ' term' + (r.total === 1 ? '' : 's') + ' added to organic keyword tracking');
        } else if (!r.okCount) {
          this.notify(this.errText(r.failed[0].err, 'Could not add those keywords'));
        } else {
          this.notify(r.okCount + ' of ' + r.total + ' terms added. ' + r.failed.length + ' failed — still selected, try again.');
        }
      });
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
      .catch(err => { if (this._alive) this.notify(this.errText(err, 'Could not add that keyword')); });
  }

  notify(msg) { this.setState({ toast: msg }); clearTimeout(this._nt); this._nt = setTimeout(() => { if (this._alive) this.setState({ toast: null }); }, 2600); }

  /* Turns a rejected FuseAPI promise into one sentence a non-technical user can act on.
     Three cases, because they need different words:
       - server said no  → err.detail is already human-readable (DRF `detail`), use it verbatim;
       - transport died  → fetch() rejects with "Failed to fetch" / "NetworkError", which tells
                           the user nothing, so the caller's fallback + "couldn't reach the
                           server" is substituted;
       - sentinel        → 'not_yet_available' is the API saying the deployment has no such
                           feature (settings_service._SECURITY_REFUSED); say that plainly.
     `fallback` must name the action that failed ("Could not save crawl settings"), never be
     a generic "Error". */
  errText(err, fallback) {
    const raw = (err && (err.detail || err.message)) || '';
    if (raw === 'not_yet_available') return 'Not available in this deployment — nothing was saved.';
    if (!raw || /failed to fetch|networkerror|network request failed|load failed/i.test(raw)) {
      return fallback + ' — could not reach the server. Check your connection and try again.';
    }
    /* api.js's last resort when the error body carries no `detail`: "API 500 /api/…". That is
       a URL and a number, i.e. nothing a user can act on, so it becomes the named action plus
       the status code. */
    const m = /^API (\d{3}) \//.exec(raw);
    if (m) return fallback + ' — the server rejected it (error ' + m[1] + ').';
    return raw;
  }

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
    const pid = this.state.projectId;
    const ids = un.map(f => f.id);
    /* One button press gets one request and one message.
       History, so neither half is undone by accident:
         - It first fired N requests AND announced success immediately, before any had
           answered — "12 alerts acknowledged" appeared even when all twelve were refused.
         - That was fixed by settling every request and reporting once, which was correct but
           still meant one POST per row: ~104 requests from a single click on a real feed.
       So the reporting stays exactly as it was — all-ok, all-failed (with the server's
       reason), or a partial count naming how many did not save — but it is now driven by a
       single POST /api/alerts/ack that returns a per-id outcome. Only the ids the server
       confirms are marked acknowledged locally; the rest stay unacknowledged and retryable.
       ackAlert() is untouched and still serves the per-row Acknowledge button. */
    window.FuseAPI.post('/api/alerts/ack', { ids: ids, project: pid }).then(res => {
      if (!this._alive) return;
      const acked = (res && res.acknowledged) || [];
      const failed = (res && res.failed) || [];
      if (acked.length) {
        const ackedSet = {};
        acked.forEach(id => { ackedSet[id] = true; });
        this.setState(s => {
          const k = this.key('alerts', pid, s.range);
          const cur = s.cache[k];
          if (!cur) return {};
          const cache = Object.assign({}, s.cache);
          cache[k] = { feed: cur.feed.map(f => ackedSet[f.id] ? Object.assign({}, f, { acknowledged: true }) : f) };
          return { cache };
        });
      }
      if (!failed.length) {
        this.notify(acked.length + ' alert' + (acked.length === 1 ? '' : 's') + ' acknowledged');
      } else if (!acked.length) {
        this.notify(this.errText({ detail: failed[0].detail }, 'Could not acknowledge these alerts'));
      } else {
        this.notify(acked.length + ' of ' + ids.length + ' alerts acknowledged — ' + failed.length + ' could not be saved. Try those again.');
      }
    }).catch(err => {
      if (!this._alive) return;
      this.notify(this.errText(err, 'Could not acknowledge these alerts'));
    });
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
    /* The last state the server confirmed — what the switch must snap back to if the debounced
       save is refused. `base` alone is not enough: it is the local draft, which may already
       contain earlier edits from the same 600 ms window that were never persisted either. */
    const persisted = (data && data.alertRules) || base;
    const next = base.map(r => r.id === ruleId ? Object.assign({}, r, patch) : r);
    this.setState({ rules: next });
    clearTimeout(this._rt);
    this._rt = setTimeout(() => {
      window.FuseAPI.put('/api/projects/' + this.state.projectId + '/settings', { alertRules: next })
        .then(() => { if (this._alive) this.notify('Alert rules updated'); })
        .catch(err => {
          if (!this._alive) return;
          this.setState({ rules: persisted });
          this.notify(this.errText(err, 'Could not save the alert rule'));
        });
    }, 600);
  }

  saveCrawl() {
    const cfg = this.state.crawlCfg;
    if (!cfg) { this.setState({ crawlSaved: true }); return; }
    window.FuseAPI.put('/api/projects/' + this.state.projectId + '/settings', { crawl: cfg }).then(() => {
      if (!this._alive) return;
      this.setState({ crawlSaved: true });
      this.notify('Crawl settings saved — applies to the next crawl');
    }).catch(err => {
      if (!this._alive) return;
      /* keep the button on "Save" rather than flipping it to "Saved ✓" for a write that
         never landed — st.crawlSaveLabel is driven off this flag */
      this.setState({ crawlSaved: false });
      this.notify(this.errText(err, 'Could not save crawl settings'));
    });
  }

  /* ---------- alerts ---------- */
  /* ackAlert(id, opts) — the SINGLE-row path, used by each row's Acknowledge button in
   * alerts.js. Bulk acknowledgement no longer goes through here: ackAllAlerts() sends one
   * batch POST instead of calling this N times.
   *   opts.silent – suppress the failure toast. No current caller passes it (it existed for
   *                 the old fan-out ackAllAlerts); kept so a future caller that wants to
   *                 report its own aggregate result can still silence per-row toasts.
   * Always resolves (never rejects) to {ok:true} / {ok:false, err}, so the callers in
   * alerts.js can keep ignoring the return value without producing an unhandled rejection. */
  ackAlert(id, opts) {
    const pid = this.state.projectId;
    const silent = !!(opts && opts.silent);
    return window.FuseAPI.post('/api/alerts/' + id + '/ack', {}).then(() => {
      if (!this._alive) return { ok: true };
      this.setState(s => {
        const k = this.key('alerts', pid, s.range);
        const cur = s.cache[k];
        if (!cur) return {};
        const cache = Object.assign({}, s.cache);
        cache[k] = { feed: cur.feed.map(f => f.id === id ? Object.assign({}, f, { acknowledged: true }) : f) };
        return { cache };
      });
      return { ok: true };
    }).catch(err => {
      if (this._alive && !silent) this.notify(this.errText(err, 'Could not acknowledge this alert'));
      return { ok: false, err: err };
    });
  }

  /* unackAlert(id) — the row's Undo button. The exact inverse of ackAlert(): same single-row
   * path, same cache patch with acknowledged flipped back to false, so the row returns to the
   * unacknowledged list and the sidebar/bell badges (which derive from that one flag) count it
   * again. Deliberately sends no `project`, matching ackAlert: the ack was recorded for every
   * active project, so the undo has to clear the same set or it would only half-undo.
   * The local flag is flipped only after the server confirms — an alert that still reads
   * "acknowledged" on the next fetch must not look undone in the meantime. */
  unackAlert(id) {
    const pid = this.state.projectId;
    return window.FuseAPI.post('/api/alerts/' + id + '/unack', {}).then(() => {
      if (!this._alive) return { ok: true };
      this.setState(s => {
        const k = this.key('alerts', pid, s.range);
        const cur = s.cache[k];
        if (!cur) return {};
        const cache = Object.assign({}, s.cache);
        cache[k] = { feed: cur.feed.map(f => f.id === id ? Object.assign({}, f, { acknowledged: false }) : f) };
        return { cache };
      });
      this.notify('Acknowledgement undone');
      return { ok: true };
    }).catch(err => {
      if (this._alive) this.notify(this.errText(err, 'Could not undo this acknowledgement'));
      return { ok: false, err: err };
    });
  }

  /* ---------- settings ---------- */
  saveCreds() {
    const pid = this.state.projectId;
    window.FuseAPI.put('/api/projects/' + pid + '/settings', {
      credentials: {
        gsc_property: this.state.creds.gsc,
        ga4_property_id: this.state.creds.ga4,
        dataforseo_target_domain: this.state.creds.dataforseo,
      }
    }).then(() => {
      if (!this._alive) return;
      this.setState({ credsSaved: true, credsFor: null }); // credsFor: null re-seeds from the
      // server's normalised value next render (e.g. a pasted "properties/123" becomes "123"),
      // so the box shows what was actually stored, not what was typed.
      setTimeout(() => { if (this._alive) this.setState({ credsSaved: false }); }, 1800);
    }).catch(err => {
      if (!this._alive) return;
      /* the button must not read "Saved ✓" for credentials the server rejected — a wrong GSC
         property that looks saved is the difference between "no data yet" and "misconfigured" */
      this.setState({ credsSaved: false });
      this.notify(this.errText(err, 'Could not save these credentials'));
    });
  }

  /* "Saved ✓" only ever meant "the write succeeded", never "this actually works" — GA4 had no
     access check at all, so a wrong-but-present property id looked identical to a correct one
     until a sync failed 20 minutes later. This calls the same live probe the Add-domain modal
     uses, against whatever is in the form right now (not necessarily saved yet). */
  testConnections() {
    const pid = this.state.projectId;
    const domain = (this.state.projects.find(p => p.id === pid) || {}).domain || '';
    this.setState({ credsTesting: true, credsTestResult: null });
    window.FuseAPI.post('/api/connection-check', {
      domain: domain,
      gsc_property: this.state.creds.gsc,
      ga4_property_id: this.state.creds.ga4,
      dataforseo_target: this.state.creds.dataforseo,
      include_optional: false,
    }).then(result => {
      if (!this._alive) return;
      this.setState({ credsTesting: false, credsTestResult: result });
    }).catch(err => {
      if (!this._alive) return;
      this.setState({ credsTesting: false });
      this.notify(this.errText(err, 'Could not run the connection check'));
    });
  }

  togglePref(keyName) {
    const prev = this.state.prefs;
    const prefs = Object.assign({}, prev || {});
    prefs[keyName] = !prefs[keyName];
    this.setState({ prefs });
    window.FuseAPI.put('/api/projects/' + this.state.projectId + '/settings', { prefs }).catch(err => {
      if (!this._alive) return;
      /* optimistic switch — put it back, otherwise the user believes they turned email
         alerts on and simply never receives any */
      this.setState({ prefs: prev });
      this.notify(this.errText(err, 'Could not save that preference'));
    });
  }

  /* ---------- extended settings ---------- */
  /* `revert` (optional) is state to restore when the server refuses the change. Without it a
     rejected save leaves the toggle looking ON while nothing was stored — the Security tab did
     exactly that for 2FA, SSO, session-revoke and token-create, all of which the API returns a
     400 for. Swallowing the error here was the single line that made every one of those
     controls appear to work. */
  putSettings(body, msg, flag, revert) {
    window.FuseAPI.put('/api/projects/' + this.state.projectId + '/settings', body).then(() => {
      if (!this._alive) return;
      if (flag) { this.setState({ [flag]: true }); setTimeout(() => { if (this._alive) this.setState({ [flag]: false }); }, 1800); }
      if (msg) this.notify(msg);
    }).catch(err => {
      if (!this._alive) return;
      if (revert) this.setState(revert);
      var detail = (err && (err.detail || err.message)) || 'Could not save';
      this.notify(detail === 'not_yet_available'
        ? 'Not available in this deployment — nothing was saved.'
        : detail);
    });
  }
  editWs(patch) { this.setState(s => ({ wsDraft: Object.assign({}, s.wsDraft, patch), savedWs: false })); }
  saveWs() { this.putSettings({ workspace: this.state.wsDraft }, 'Workspace saved', 'savedWs'); }
  clearData() {
    if (window.confirm("Are you sure you want to permanently delete all synced analytics data for this project? This action cannot be undone.")) {
      /* There is no router ctx on this component — the active project lives in
         state, same as every other settings call in this file. */
      const pid = this.state.projectId;
      window.FuseAPI.del('/api/projects/' + pid + '/data')
        .then(() => {
          if (!this._alive) return;
          this.notify("Data cleared successfully. Reloading...");
          setTimeout(() => window.location.reload(), 1500);
        })
        .catch(e => { if (this._alive) this.notify("Failed to clear data: " + (e.message || "Unknown error")); });
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
  /* `togglePlatform` used to live here. It flipped a platformConnectors boolean and reported
     "Connected <platform>" without authenticating anything -- see the platRows comment in
     pages/settings.js for why that row is now inert. It also passed no `revert` to
     putSettings, so a failed save left the pill reading "Connected" until a reload. */
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
  /* Each of these four sets state optimistically and then asks the server. The API refuses
     twofa/sso/sessions/tokens (none of them are backed by anything real — see
     settings_service._SECURITY_REFUSED), so every one passes its pre-change draft as `revert`.
     Without that the switch stays visually ON after a refusal and the UI claims a security
     control the deployment does not have. */
  toggle2fa() {
    const prev = this.state.secDraft;
    const sec = Object.assign({}, prev, { twofa: !prev.twofa });
    this.setState({ secDraft: sec });
    this.putSettings({ security: sec }, sec.twofa ? 'Two-factor enabled' : 'Two-factor disabled', null, { secDraft: prev });
  }
  toggleSso() {
    const prev = this.state.secDraft;
    const sec = Object.assign({}, prev, { sso: !prev.sso });
    this.setState({ secDraft: sec });
    this.putSettings({ security: sec }, sec.sso ? 'SSO enabled' : 'SSO disabled', null, { secDraft: prev });
  }
  revokeSession(id) {
    const prev = this.state.secDraft;
    const sec = Object.assign({}, prev, { sessions: prev.sessions.filter(x => x.id !== id) });
    this.setState({ secDraft: sec });
    this.putSettings({ security: sec }, 'Session revoked', null, { secDraft: prev });
  }
  revokeToken(id) {
    const prev = this.state.secDraft;
    const sec = Object.assign({}, prev, { tokens: prev.tokens.filter(x => x.id !== id) });
    this.setState({ secDraft: sec });
    this.putSettings({ security: sec }, 'Token revoked', null, { secDraft: prev });
  }
  createToken() {
    const name = (this.state.newTokenName || '').trim();
    if (!name) { this.notify('Name the token first'); return; }
    /* The prefix is a made-up string that authenticates nothing — real API tokens come from
       DRF's authtoken, one per user. The server refuses this, so the optimistic row is
       reverted rather than left sitting in the table looking like a usable credential. */
    const prev = this.state.secDraft;
    const prevName = this.state.newTokenName;
    const tok = { id: 'tk' + Date.now().toString(36), name, prefix: 'lm_live_' + Math.random().toString(36).slice(2, 6), created: new Date().toISOString().slice(0, 10), last_used: null };
    const sec = Object.assign({}, prev, { tokens: prev.tokens.concat([tok]) });
    this.setState({ secDraft: sec, newTokenName: '' });
    this.putSettings({ security: sec }, 'API token created — copy it now', null, { secDraft: prev, newTokenName: prevName });
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
        setTimeout(() => { if (this._alive) this.setState({ cpwMsg: '', cpwOpen: false }); }, 2000);
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
  fmt(n) {
    if (n == null) return '—';
    if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
    if (n >= 100000) return Math.round(n / 1000) + 'K';
    return n.toLocaleString('en-US');
  }
  money(n) { return '$' + (n == null ? '0.00' : Number(n).toFixed(2)); }
  /* One decimal place, edge-of-render only -- never round inside a query_*_raw/service helper.
     SKILLS.md records why: _get_keywords_overview once formatted position as f"{avg:.0f}"
     before any caller saw it, so 8.4 arrived as 8 irrecoverably and the column then sorted as
     text ("1,234" < "9"). AVG(position)/AVG(keyword_difficulty) over ~28 daily rows routinely
     produces 35.857142857142854; fmt() alone does not fix this — toLocaleString('en-US') on
     that value returns "35.857", not "35.9". Sorting must still use the raw, unrounded number. */
  dec1(n) {
    if (n == null) return '—';
    const r = Math.round(n * 10) / 10;
    return (Number.isInteger(r) ? r.toFixed(0) : r.toFixed(1));
  }
  /* Alert timestamps arrive as date-only ISO strings ("2026-07-24" — see
     alerts_service.build_alerts_response). Appending T00:00:00 forces local-midnight
     parsing; a bare "YYYY-MM-DD" is parsed as UTC by spec, which shifts the day for
     anyone west of Greenwich and would show "yesterday" for today's alerts. Anything
     unparseable is returned verbatim rather than guessed at. */
  relTime(ts) {
    if (!ts) return '';
    const raw = String(ts);
    const d = new Date(raw.length <= 10 ? raw + 'T00:00:00' : raw);
    const t = d.getTime();
    if (isNaN(t)) return raw;
    const diff = Date.now() - t;
    if (diff < 60000) return 'just now';
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return mins + 'm ago';
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return hrs + 'h ago';
    const days = Math.floor(hrs / 24);
    if (days === 1) return 'yesterday';
    if (days < 7) return days + 'd ago';
    if (days < 35) return Math.floor(days / 7) + 'w ago';
    if (days < 365) return Math.floor(days / 30) + 'mo ago';
    return Math.floor(days / 365) + 'y ago';
  }
  posBadge(p) {
    // 28px fit a single digit; a decimal position like "35.9" needs more room.
    const base = { display: 'inline-flex', alignItems: 'center', justifyContent: 'center', minWidth: '38px', height: '24px', borderRadius: '4px', fontSize: '12px', fontWeight: 600 };
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
  chartHoverOut() {
    if (this.state.chartHoverIndex !== null) {
      this.setState({ chartHoverIndex: null });
    }
  }
  toggleAuditCheck(checkId) {
    const pid = this.state.projectId;
    window.FuseAPI.post('/api/projects/' + pid + '/audit/toggle-check', { checkId }).then(() => {
      if (!this._alive) return;
      this.setState({ auOpen: null, auAllPages: null });
      this.fetchTab('pages', pid, this.state.range, true);
    }).catch(err => {
      if (!this._alive) return;
      this.notify(this.errText(err, 'Could not hide that check'));
    });
  }
  toggleResolvedCheck(checkId) {
    const pid = this.state.projectId;
    window.FuseAPI.post('/api/projects/' + pid + '/audit/toggle-resolved', { checkId }).then(() => {
      if (!this._alive) return;
      this.setState({ auOpen: null, auAllPages: null });
      this.fetchTab('pages', pid, this.state.range, true);
    }).catch(err => {
      if (!this._alive) return;
      this.notify(this.errText(err, 'Could not update that check'));
    });
  }

  /* The one comparator behind every sortable table here (Crawled Pages, Keywords, Campaigns,
     Search Terms, Referring domains). Tested in static/spa/tests/sort_rows.test.js.

     UNMEASURED ROWS SINK TO THE BOTTOM IN BOTH DIRECTIONS. This used to substitute -1 for a
     null before subtracting, which is lower than every real metric on this dashboard (scores
     0-100, milliseconds, link counts, sessions) — so ascending order ranked every unmeasured
     row as worse than the worst measured one. On Site Audit -> Crawled Pages, which defaults
     to score-ascending and renders only the first 40 rows, that put all 28 never-Lighthoused
     pages on top and pushed all 27 real scores below the fold: the table read as an empty
     column of dashes on a site that had a full set of measurements.

     Everywhere else this codebase is careful that null means "not measured, and that is not
     zero" — it never renders null as 0 and never lets it into an average. Ranking null as
     worse-than-zero broke the same rule the moment a user sorted. An unmeasured row is not the
     best and not the worst; it is not a result, so it goes last either way and the ordering of
     the real values is unaffected. A real 0 is a result (an orphan page has 0 in-links) and
     still sorts as 0. */
  sortRows(rows, sort) {
    const dir = sort.dir;
    const unmeasured = v => v == null || v === '';
    return rows.slice().sort((a, b) => {
      const av = a[sort.key], bv = b[sort.key];
      const am = unmeasured(av), bm = unmeasured(bv);
      if (am || bm) return (am && bm) ? 0 : (am ? 1 : -1);
      if (typeof av === 'string' || typeof bv === 'string') return String(av).localeCompare(String(bv)) * dir;
      return (av - bv) * dir;
    });
  }
  arrow(sort, keyName) { return sort.key === keyName ? (sort.dir === -1 ? ' ↓' : ' ↑') : ''; }

  /* Pagination helpers, shared so a second paginated table cannot invent its own arithmetic.
     Tested in static/spa/tests/page_window.test.js, which extracts these two methods from this
     file rather than restating them — a restated copy passes forever after the original drifts.

     `pageSlice` CLAMPS rather than trusting the requested index: filtering can shrink a list
     under a reader who is on page 12, and an out-of-range slice renders an empty table that is
     indistinguishable from "nothing matched your filter". */
  pageSlice(total, requestedPage, size) {
    const pageCount = Math.max(1, Math.ceil(total / size));
    const pageIdx = Math.min(Math.max(0, requestedPage || 0), pageCount - 1);
    const from = pageIdx * size;
    return { pageCount: pageCount, pageIdx: pageIdx, from: from, shown: Math.max(0, Math.min(size, total - from)) };
  }

  /* Which page numbers to draw: a window of 7 around the current page, with first and last
     always reachable, and an ellipsis marking each gap. Returns [] for a single page so the
     nav row can be hidden entirely rather than drawing a lone "1". */
  pageWindow(pageCount, pageIdx) {
    const out = [];
    if (pageCount <= 1) return out;
    const WINDOW = 7;
    let lo = Math.max(0, pageIdx - Math.floor(WINDOW / 2));
    const hi = Math.min(pageCount - 1, lo + WINDOW - 1);
    lo = Math.max(0, Math.min(lo, hi - WINDOW + 1));
    if (lo > 0) { out.push(0); if (lo > 1) out.push('gap'); }
    for (let n = lo; n <= hi; n++) out.push(n);
    if (hi < pageCount - 1) { if (hi < pageCount - 2) out.push('gap'); out.push(pageCount - 1); }
    return out;
  }

  /* ================= Data source badges =================================================
     Every metric surface has to answer two questions without the user asking anyone:
       1. where did this number come from?  ->  GSC · GA4 · DataForSEO · Lighthouse · Google Ads
       2. how old is it?                    ->  the last run of the connector(s) behind it

     There is deliberately NO "estimated" tier. A number that was not measured does not get a
     badge admitting it — it is not on screen at all. If a surface has no connector that can
     honestly be named, that is a finding to report, not a badge to invent.

     Freshness comes from the real `SyncLog` rows (apps/sync/models.py) that
     settings_service.query_connectors_raw already returns on GET /settings, loaded into
     state.syncLog by loadSyncLog(). Three properties of those rows matter and are easy to
     get wrong:

       * `last_sync` is the last RUN, not the last SUCCESS. pipeline/connectors/base.py writes
         it for BOTH "success" and "error". So when the last run failed, the data on screen is
         OLDER than that date, and the badge has to say so instead of printing the date alone.
         Off-site's own banner already words it exactly this way; these badges match it.
       * status "running" sets `last_sync` back to null, so a connector that is mid-sync must
         not be reported as "never synced".
       * the real status vocabulary is never|running|success|error — never "ok".

     A surface fed by more than one connector (Site Audit's health score is 60% Lighthouse +
     40% GSC URL Inspection; Off-site joins GA4 sessions with DataForSEO referring domains) is
     reported as the union of its sources and the age of its OLDEST input — a card is only as
     fresh as the stalest thing in it — and it names which half is failing or missing rather
     than averaging the problem away.                                                        */

  /* brand shown in the badge (deduped) */
  get SRC_LABEL() {
    return {
      gsc: 'GSC', gsc_keywords: 'GSC', gsc_pages: 'GSC', url_inspection: 'GSC',
      ga4: 'GA4',
      pagespeed: 'Lighthouse',
      dataforseo_serp: 'DataForSEO', dataforseo_keywords: 'DataForSEO',
      dataforseo_backlinks: 'DataForSEO', dataforseo_onpage: 'DataForSEO',
      dataforseo_labs_competitors: 'DataForSEO', dataforseo_serp_competitors: 'DataForSEO',
      dataforseo_ai_keywords: 'DataForSEO',
      google_ads: 'Google Ads', google_ads_search_terms: 'Google Ads',
      sitemap: 'Sitemap', meta: 'Meta', linkedin: 'LinkedIn'
    };
  }
  /* short precise name, used only when one part of a mixed source is the problem */
  get SRC_PART() {
    return {
      gsc: 'GSC search', gsc_keywords: 'GSC queries', gsc_pages: 'GSC pages',
      url_inspection: 'GSC indexing', ga4: 'GA4', pagespeed: 'Lighthouse',
      dataforseo_serp: 'DataForSEO SERP', dataforseo_keywords: 'DataForSEO volume',
      dataforseo_backlinks: 'DataForSEO backlinks', dataforseo_onpage: 'DataForSEO OnPage',
      dataforseo_labs_competitors: 'DataForSEO competitors',
      dataforseo_serp_competitors: 'DataForSEO competitor SERP',
      dataforseo_ai_keywords: 'DataForSEO AI keywords',
      google_ads: 'Google Ads', google_ads_search_terms: 'Google Ads search terms',
      sitemap: 'Sitemap', meta: 'Meta', linkedin: 'LinkedIn'
    };
  }
  /* full name, used in the title attribute */
  get SRC_FULL() {
    return {
      gsc: 'Google Search Console — Search Analytics',
      gsc_keywords: 'Google Search Console — query report',
      gsc_pages: 'Google Search Console — page report',
      url_inspection: 'Google Search Console — URL Inspection API',
      ga4: 'Google Analytics 4',
      pagespeed: 'Google PageSpeed Insights (Lighthouse)',
      dataforseo_serp: 'DataForSEO — SERP positions',
      dataforseo_keywords: 'DataForSEO — search volume & CPC',
      dataforseo_backlinks: 'DataForSEO — backlink profile',
      dataforseo_onpage: 'DataForSEO — OnPage crawl',
      dataforseo_labs_competitors: 'DataForSEO Labs — competitor domains',
      dataforseo_serp_competitors: 'DataForSEO — competitor SERP positions',
      dataforseo_ai_keywords: 'DataForSEO — AI keyword data',
      google_ads: 'Google Ads',
      google_ads_search_terms: 'Google Ads — search term report',
      sitemap: 'Sitemap crawl', meta: 'Meta', linkedin: 'LinkedIn'
    };
  }
  /* One generic threshold rather than a per-connector guess. It is a UI policy, not a claim
     about the data: "this has not been refreshed in over a fortnight". The exact timestamp is
     always in the title, so nothing is hidden behind the word. */
  get SRC_STALE_DAYS() { return 14; }

  srcStyle(state) {
    const base = {
      display: 'inline-flex', alignItems: 'center', gap: '5px', flexShrink: 0,
      fontSize: '10.5px', fontWeight: 600, letterSpacing: '0.02em',
      padding: '2px 7px', borderRadius: '4px', whiteSpace: 'nowrap',
      border: '1px solid #e2e8f0', background: '#f8fafc', color: '#64748b',
      /* NOT `pointer`: a11ySweep() promotes every pointer-cursor leaf to role="button", and
         this badge is not a control. `help` signals the title tooltip without doing that. */
      cursor: 'help'
    };
    if (state === 'stale') return Object.assign(base, { border: '1px solid #fef3c7', background: '#fffbeb', color: '#b45309' });
    if (state === 'failed') return Object.assign(base, { border: '1px solid #fecaca', background: '#fef2f2', color: '#b91c1c' });
    if (state === 'never') return Object.assign(base, { border: '1px solid #e2e8f0', background: '#f1f5f9', color: '#94a3b8' });
    if (state === 'running') return Object.assign(base, { border: '1px solid #bfdbfe', background: '#eff6ff', color: '#1d4ed8' });
    if (state === 'live') return Object.assign(base, { border: '1px solid #bfdbfe', background: '#eff6ff', color: '#1d4ed8' });
    return base;
  }

  /* `note` (optional) is appended to the tooltip for a surface that needs one sentence of
     provenance the connector list alone cannot carry — e.g. "this half only appears once the
     Ads connector has run". It never changes the visible text or the state. */
  srcBadge(connectors, note) {
    /* Every branch returns a fully-populated object: a template reading {{ x.src.text }} must
       never be able to print `undefined`. `show:false` hides it via its own <sc-if>. */
    const hidden = { show: false, state: 'none', text: '', title: '', aria: '', style: { display: 'none' } };
    if (!connectors || !connectors.length) return hidden;
    const st = this.state;
    /* No rows yet (first paint, or the read failed) — no badge, rather than a made-up date. */
    if (!st.syncLog || !st.syncLog.length || st.syncLogFor !== st.projectId) return hidden;

    const by = {};
    for (let i = 0; i < st.syncLog.length; i++) by[st.syncLog[i].name] = st.syncLog[i];

    const LBL = this.SRC_LABEL, PART = this.SRC_PART, FULL = this.SRC_FULL;
    const labels = [], failed = [], never = [], running = [], detail = [];
    let oldestMs = null, okCount = 0;

    for (let i = 0; i < connectors.length; i++) {
      const nm = connectors[i];
      const lbl = LBL[nm] || nm, part = PART[nm] || nm, full = FULL[nm] || nm;
      if (labels.indexOf(lbl) < 0) labels.push(lbl);
      const row = by[nm];
      if (row && row.status === 'running') {
        if (running.indexOf(part) < 0) running.push(part);
        detail.push(full + ': refreshing now');
        continue;
      }
      if (!row || !row.last_sync) {
        if (never.indexOf(part) < 0) never.push(part);
        detail.push(full + ': never synced');
        continue;
      }
      const raw = String(row.last_sync);
      const stamp = raw.slice(0, 10) + ' ' + raw.slice(11, 16);
      if (row.status === 'error') {
        if (failed.indexOf(part) < 0) failed.push(part);
        detail.push(full + ': last run ' + stamp + ' FAILED' + (row.error ? ' (' + row.error + ')' : '')
          + ' — the figures shown are older than this date');
      } else {
        okCount++;
        detail.push(full + ': last synced ' + stamp
          + (row.records == null ? '' : ' · ' + row.records + ' records'));
        const t = new Date(raw).getTime();
        if (!isNaN(t) && (oldestMs === null || t < oldestMs)) oldestMs = t;
      }
    }

    const name = labels.join(' + ');
    const total = connectors.length;
    let state, tail;
    if (failed.length) {
      /* Worst first: a failed run means the number is older than any date we could print. */
      state = 'failed';
      tail = failed.length === total ? 'last refresh failed' : failed.join(' + ') + ' refresh failed';
    } else if (never.length === total) {
      state = 'never'; tail = 'never synced';
    } else if (never.length) {
      state = 'never'; tail = never.join(' + ') + ' never synced';
    } else if (running.length) {
      state = 'running'; tail = running.length === total ? 'refreshing now' : running.join(' + ') + ' refreshing';
    } else if (!okCount || oldestMs === null) {
      state = 'never'; tail = 'never synced';
    } else {
      const ageDays = Math.floor((Date.now() - oldestMs) / 86400000);
      state = ageDays > this.SRC_STALE_DAYS ? 'stale' : 'fresh';
      /* relTime() is the app's existing "how old" vocabulary ("3d ago", "6w ago") — a plain
         date does not tell a non-expert that 40-day-old data is a problem. */
      tail = this.relTime(new Date(oldestMs).toISOString());
      if (state === 'stale') tail = tail + ' · stale';
    }

    const many = labels.length > 1;
    return {
      show: true, state: state,
      text: name + ' · ' + tail,
      title: (many ? 'This card is built from ' + total + ' sources and is only as fresh as the oldest. ' : '')
        + detail.join('  ·  ') + (note ? '  ·  ' + note : ''),
      aria: 'Data source: ' + name + ', ' + tail,
      style: this.srcStyle(state)
    };
  }

  /* The three sanctioned live lookups (/api/research, /api/domain-overview, /api/live-serp)
     have no SyncLog row by construction — they ran because the user pressed a button, so
     "how old is it" is answered by the press itself, not by a sync date. */
  srcLive(label, what) {
    return {
      show: true, state: 'live',
      text: label + ' · live',
      title: 'Fetched live from ' + label + ' when you ran this ' + (what || 'lookup')
        + '. Nothing here is stored or scheduled, so it is as of this moment.',
      aria: 'Data source: ' + label + ', fetched live just now',
      style: this.srcStyle('live')
    };
  }
  mkSortHandler(stateKey, keyName, resetKey) {
    return () => this.setState(s => {
      const cur = s[stateKey];
      const next = { [stateKey]: { key: keyName, dir: cur.key === keyName ? -cur.dir : -1 } };
      // Paginated tables pass the name of their page-index state so re-sorting returns to page 1.
      if (resetKey) next[resetKey] = 0;
      return next;
    });
  }

  /* ---------- AI Optimization actions ---------- */
  aiPost(action, body) { return window.FuseAPI.post('/api/projects/' + this.state.projectId + '/ai/' + action, body || {}); }
  /* Deliberately silent. Every caller is a mutation that has already succeeded and already
     told the user so; this is only the re-read that pulls the new server state into the cache.
     A second, contradictory toast for a failed background refresh would be noise the user did
     not ask for, and the database-first contract already says a stale screen is acceptable —
     the AI tab keeps showing the last saved data until the next visit or refresh. */
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
      .catch(err => {
        if (!this._alive) return;
        /* clears the spinner AND says why — the wizard used to just come back to life with no
           explanation, looking like the user had mis-clicked Finish */
        this.setState({ aiWizBusy: false });
        this.notify(this.errText(err, 'Could not save your AI tracking setup'));
      });
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
      }).catch(err => {
        if (!this._alive) return;
        /* the targets drawer stays open with the user's edits intact so they can retry */
        this.notify(this.errText(err, 'Could not save the tracked targets'));
      });
  }
  aiAddPrompts(texts, listId, after) {
    if (!texts.length) return;
    this.aiPost('prompts', { texts, listId })
      .then(r => {
        if (!this._alive) return;
        this.aiReload();
        this.notify(r.added + ' prompt' + (r.added === 1 ? '' : 's') + ' added — first run on the weekly schedule');
        if (after) after();
      }).catch(err => {
        if (!this._alive) return;
        /* `after` is deliberately NOT run: it clears the composer / closes the picker, which
           would throw away text the user now has to re-type */
        this.notify(this.errText(err, 'Could not add ' + (texts.length === 1 ? 'that prompt' : 'those prompts')));
      });
  }
  aiRun(body) {
    this.aiPost('run', body)
      .then(r => {
        if (!this._alive) return;
        this.aiReload();
        this.notify('Ran ' + r.ran + ' prompt' + (r.ran === 1 ? '' : 's') + ' across LLMs · ' + this.money(r.cost));
      }).catch(err => {
        if (!this._alive) return;
        /* a run costs money and takes time — silence here reads as "nothing happened yet",
           and the user presses it again */
        this.notify(this.errText(err, 'Could not run the prompts'));
      });
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
      .catch(err => {
        if (!this._alive) return;
        this.setState({ aiInspecting: false });
        this.notify(this.errText(err, 'Could not run that inspection'));
      });
  }
  aiExplore() {
    const q = this.state.aiExpQ.trim();
    if (!q || this.state.aiExploring) return;
    this.setState({ aiExploring: true, aiExpSel: [], aiExpAddOpen: false });
    window.FuseAPI.post('/api/prompt-research', { project: this.state.projectId, seeds: q.split(',') })
      .then(r => { if (this._alive) this.setState({ aiExploring: false, aiExp: r }); })
      .catch(err => {
        if (!this._alive) return;
        this.setState({ aiExploring: false });
        this.notify(this.errText(err, 'Could not explore prompt ideas'));
      });
  }
  aiRemovePrompts(ids) {
    if (!ids.length) return;
    this.aiPost('prompts-remove', { ids })
      .then(() => {
        if (!this._alive) return;
        this.setState({ aiPromptSel: [] });
        this.aiReload();
        this.notify(ids.length === 1 ? 'Prompt removed' : ids.length + ' prompts removed');
      }).catch(err => {
        if (!this._alive) return;
        this.notify(this.errText(err, 'Could not remove ' + (ids.length === 1 ? 'that prompt' : 'those prompts')));
      });
  }
  aiListOp(op, id, name, after) {
    this.aiPost('lists', { op, id, name })
      .then(() => { if (!this._alive) return; this.aiReload(); if (after) after(); })
      .catch(err => {
        if (!this._alive) return;
        /* op is 'create' | 'rename' | 'delete'; naming it tells the user which of the three
           list controls did nothing. `after` is skipped so the name they typed survives. */
        this.notify(this.errText(err, 'Could not ' + op + ' the prompt list'));
      });
  }

  /* ---------- renderVals ---------- */
  renderVals() {
    const s = this.state;
    const tab = s.tab;
    /* Empty, not a stand-in domain. This ran before /api/projects answers on every boot, so
       the hardcoded {domain:'fusehealth.com', name:'FuseHealth'} it used to fall back to
       labelled the topbar, the page title and every CSV export filename with a site the
       viewer may have no connection to. A blank label for the fraction of a second the list
       is in flight is honest; a confident wrong one is not. */
    const project = (s.projects.find(p => p.id === s.projectId)) || { domain: '', name: '' };

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
      domain_overview: ['Domain Overview', 'Deep-dive organic traffic and keywords for any domain'],
      keywords: ['Keyword Research', 'Your organic keyword portfolio — powered by DataForSEO'],
      positioning: ['Position Tracking', 'Weekly SERP snapshots, competitors, and movement'],
      backlinks: ['Backlinks', 'Live and lost links with referring domain quality'],
      offsite: ['Off-site SEO', 'Off-site organic interactions from GA4 — referral, social & video'],
      pages: ['Site Audit', 'Crawl health, indexing, and page speed — merged view'],
      ai: ['AI Optimization', 'Brand visibility in AI Overviews & ChatGPT · prompt checks across ChatGPT, Claude, Gemini & Perplexity'],
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
    /* What the progress banner calls the run in flight. Keyed on the SCOPE, not on the tab:
       the label used to be `tabToLabel[tab]`, so any narrow scope started from a card on the
       Site Audit page announced itself as "Syncing Site Audit" — which reads as "this is
       refreshing the whole page" and is how a cheap, targeted refresh gets mistaken for the
       expensive one. Unlisted scopes fall back to the scope name itself rather than to the
       tab, so a new scope is never mislabelled as an existing one. */
    const scopeToLabel = {
      overview: 'Overview', keywords: 'Keywords', positions: 'Positions',
      positions_new: 'new keywords', backlinks: 'Backlinks', audit: 'Site Audit',
      domain_checks: 'Domain Checks', ai: 'AI Data', ads: 'Ads',
    };
    const pageScope = tabToScope[tab];

    const data = s.cache[this.key(tab)];
    const alertsData = s.cache[this.key('alerts')];
    /* The single definition of "unread" in this app: unacknowledged and not merely
       informational. The sidebar's Alerts badge (vals.hasUnacked / vals.unackedCount),
       the topbar bell badge and the notification centre's list all derive from this one
       array — there must never be a second, subtly different predicate. */
    const unackedFeed = alertsData ? alertsData.feed.filter(f => !f.acknowledged && f.severity !== 'info') : [];
    const unacked = unackedFeed.length;

    const h = {
      logout: () => { try { localStorage.clear(); sessionStorage.clear(); } catch (e) {} window.location.href = '/logout/'; },
      navOverview: () => this.go('overview'), navSeo: () => this.go('seo'),
      navDomainOverview: () => this.go('domain_overview'), navKeywords: () => this.go('keywords'), navPositioning: () => this.go('positioning'),
      navBacklinks: () => this.go('backlinks'), navOffsite: () => this.go('offsite'), navPages: () => this.go('pages'), navAi: () => this.go('ai'),
      navAds: () => this.go('ads'), navCampaigns: () => this.go('campaigns'), navTerms: () => this.go('terms'), navAttribution: () => this.go('attribution'),
      doInput: e => this.setState({ doQuery: e.target.value }),
      doKey: e => { if (e.key === 'Enter') this.runDomainOverview(); },
      runDomainOverview: () => this.runDomainOverview(),
      doToggleRow: kw => this.setState(st => {
        const sel = st.doSel || [];
        return { doSel: sel.indexOf(kw) >= 0 ? sel.filter(k => k !== kw) : sel.concat([kw]) };
      }),
      doToggleAll: () => {
        const vis = ((this.state.doData && this.state.doData.keywords) || []).map(k => k.keyword);
        const sel = this.state.doSel || [];
        const allOn = vis.length > 0 && vis.every(k => sel.indexOf(k) >= 0);
        this.setState({ doSel: allOn ? [] : vis });
      },
      doClearSel: () => this.setState({ doSel: [] }),
      doPickCancel: () => this.doPickCancel(),
      doPickConfirm: () => this.doPickConfirm(),
      doTrackSelected: () => this.trackDomainOverviewKws(this.doSelectedRows()),
      fetchLiveSerp: (kw, loc) => this.fetchLiveSerp(kw, loc),
      analyzeUrlInDomainOverview: url => this.analyzeUrlInDomainOverview(url), navAlerts: () => this.go('alerts'), navSettings: () => { if (this.state.userRole !== 'Analyst') this.go('settings'); else this.notify('Settings require Owner or Admin access.'); },
      goConnections: () => { if (this.state.userRole === 'Analyst') { this.notify('Connecting social platforms requires Owner or Admin access.'); } else { this.setState({ tab: 'settings', settingsSub: 'connections' }); this.pushNav({ tab: 'settings', settingsSub: 'connections' }); } },
      cmpSearch: e => this.setState({ cmpSearch: e.target.value }),
      exportCampaigns: () => { const d = s.cache[this.key(s.tab)]; if (d) this.downloadCsv(project.domain + '-campaigns.csv', [['campaign', 'name'], ['platform', 'platform'], ['type', 'type'], ['status', 'status'], ['budget_daily', 'budget_daily'], ['spend', 'spend'], ['impressions', 'impressions'], ['clicks', 'clicks'], ['ctr', 'ctr'], ['cpc', 'cpc'], ['conversions', 'conversions'], ['cpa', 'cpa'], ['roas', 'roas'], ['lost_is_budget', 'lost_is_budget']], d.campaigns); },
      exportTerms: () => { const d = s.cache[this.key(s.tab)]; if (d) this.downloadCsv(project.domain + '-search-terms.csv', [['term', 'term'], ['matched_keyword', 'matchedKeyword'], ['match_type', 'matchType'], ['campaign', 'campaign'], ['impressions', 'impressions'], ['clicks', 'clicks'], ['cost', 'cost'], ['conversions', 'conversions'], ['status', 'status']], d.searchTerms); },
      setProject: e => this.setProject(e.target.value),
      toggleAddSite: () => this.toggleAddSite(),
      addSiteDomainSet: e => this.setState({ addSiteDomain: e.target.value, addSiteError: null }),
      addSiteNameSet: e => this.setState({ addSiteName: e.target.value }),
      addSiteKeyDown: e => { if (e.key === 'Enter' && s.addSiteStep === 1) this.addSiteNext(); if (e.key === 'Escape') this.toggleAddSite(); },
      addSiteNext: () => this.addSiteNext(),
      addSiteBack: () => this.addSiteBack(),
      addSiteGscSet: e => this.setState({ addSiteGsc: e.target.value }),
      addSiteGa4Set: e => this.setState({ addSiteGa4: e.target.value }),
      addSiteDataforseoSet: e => this.setState({ addSiteDataforseo: e.target.value }),
      addSiteCheck: () => this.addSiteCheck(),
      addSiteSubmit: () => this.addSiteSubmit(),
      addSiteSkip: () => this.addSiteSkip(),
      range7: () => this.setRange('7d'), range28: () => this.setRange('28d'), range90: () => this.setRange('90d'),
      refreshPage: () => { if (pageScope) this.startSync(pageScope); },
      /* Incremental positions refresh. The full 'positions' scope re-queries EVERY tracked
         keyword against every competitor, which is what makes picking up a handful of newly
         tracked keywords take minutes and cost DataForSEO credits. 'positions_new' runs the
         same connectors narrowed to keywords that have never been measured. If none are
         outstanding the backend finishes immediately rather than falling through to a full
         run -- 'nothing new' and 'everything' must not be the same outcome. */
      refreshNewKeywords: () => this.startSync('positions_new'),

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
      credDataforseo: e => this.setState({ creds: Object.assign({}, s.creds, { dataforseo: e.target.value }) }),
      saveCreds: () => this.saveCreds(),
      testCreds: () => this.testConnections(),
      syncPanelToggle: () => this.setState({ syncPanelOpen: !s.syncPanelOpen }),
      syncStop: () => this.cancelSync(),
      prefEmail: () => this.togglePref('email_alerts'),
      prefDigest: () => this.togglePref('weekly_digest'),
      syncAudit: () => this.startSync('audit'),
      /* The Domain Checks card only needs its six probes (SSL, sitemap.xml, robots.txt,
         HTTP/2, www redirect, llms.txt) — about four seconds of plain HTTPS requests against
         the site itself, no credentials and no metered call. It used to call syncAudit, so
         filling in one card cost the whole 20-30 minute crawl including the billable
         DataForSEO OnPage job. A full 'audit' still refreshes these checks; this scope is the
         cheap way to refresh only them. */
      syncDomainChecks: () => this.startSync('domain_checks'),
      syncAi: () => this.startSync('ai'),
      copyKws: () => this.copySelectedKws(),
      copySummary: () => this.copySummary(),
      ackAll: () => this.ackAllAlerts(),
      /* notification centre (topbar bell) — in-dashboard only, no Slack, no email */
      ncToggle: () => this.setState(st => ({ ncOpen: !st.ncOpen, addSiteOpen: false })),
      ncAckAll: () => this.ackAllAlerts(),
      ncViewAll: () => { this.setState({ ncOpen: false }); this.go('alerts'); },
      exportTopPages: () => { const d = s.cache[this.key('overview')]; if (d) this.downloadCsv(project.domain + '-top-pages.csv', [['page', 'url'], ['clicks', 'clicks'], ['impressions', 'impressions'], ['ctr', 'ctr']], d.topPages); },
      exportKeywords: () => { const d = s.cache[this.key('keywords')]; if (d) this.downloadCsv(project.domain + '-keywords.csv', [['keyword', 'kw'], ['intent', 'intent'], ['position', 'pos'], ['volume', 'volume'], ['kd', 'kd'], ['cpc', 'cpc'], ['clicks', 'clicks'], ['url', 'url']], d.keywords); },
      exportBacklinks: () => { const d = s.cache[this.key('backlinks')]; if (d) this.downloadCsv(project.domain + '-backlinks.csv', [['domain', 'domain'], ['url_from', 'url_from'], ['anchor', 'anchor'], ['status', 'status'], ['dofollow', 'dofollow'], ['domain_rank', 'rank'], ['page_rank', 'page_rank'], ['spam_score', 'spam_score'], ['first_seen', 'firstSeen'], ['target', 'target']], d.links); },
      exportReferrers: () => { const d = s.cache[this.key('offsite')]; if (d) this.downloadCsv(project.domain + '-referring-domains.csv', [['domain', 'domain'], ['domain_rank', 'rank'], ['sessions', 'sessions'], ['engaged_sessions', 'engagedSessions'], ['engagement_rate', 'engagedRate'], ['key_events', 'keyEvents'], ['revenue', 'revenue'], ['tracked_as_backlink', 'tracked']], d.referrers); },
      exportSocial: () => { const d = s.cache[this.key('offsite')]; if (d) this.downloadCsv(project.domain + '-off-site-social.csv', [['platform', 'platform'], ['source', 'source'], ['channel', 'channel'], ['impressions', 'impressions'], ['sessions', 'sessions'], ['engagement_rate', 'engagedRate'], ['key_events', 'keyEvents'], ['revenue', 'revenue']], d.social); },
      exportPages: () => { const d = s.cache[this.key('pages')]; if (d) this.downloadCsv(project.domain + '-crawled-pages.csv', [['url', 'url'], ['score', 'score'], ['status', 'statusCode'], ['errors', 'errors'], ['warnings', 'warnings'], ['notices', 'notices'], ['depth', 'depth'], ['in_links', 'inLinks'], ['load_ms', 'loadTimeMs']], d.crawledPages); },
      auGoIssues: () => { this.setState({ auSub: 'issues', auSev: 'all', auCat: 'all' }); this.pushNav({ auSub: 'issues' }); },
      auSearch: e => this.setState({ auSearch: e.target.value }),
      /* Back to page 1 on every filter change: typing a filter while on page 12 of the
         unfiltered list would otherwise land you past the end of a 3-page result and show an
         empty table that looks like "no matches". */
      auPgSearch: e => this.setState({ auPgSearch: e.target.value, auPgPage: 0 }),
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
      /* Was a stub: it toasted "Type the workspace name to confirm deletion" and did nothing
         -- there was no field to type into and no endpoint behind it. Scoped to the CURRENT
         project (2026-07-28, product owner's decision): the old "removes all projects" label
         promised a workspace-wide wipe that no endpoint implements, and building an
         irreversible delete-everything button was not wanted. */
      deleteProjectOpen: () => this.setState({ delProjOpen: true, delProjText: '' }),
      deleteProjectClose: () => this.setState({ delProjOpen: false, delProjText: '' }),
      deleteProjectType: e => this.setState({ delProjText: e.target.value }),
      deleteProjectConfirm: () => {
        const pid = this.state.projectId;
        const proj = (this.state.projects || []).find(p => p.id === pid);
        const domain = (proj && proj.domain) || '';
        /* Typed name must match exactly. This is the only guard on an irreversible action,
           so it is checked here against the REAL domain, not against whatever the field
           happened to be seeded with. */
        if (!domain || (this.state.delProjText || '').trim().toLowerCase() !== domain.toLowerCase()) {
          this.notify('Type ' + (domain || 'the project domain') + ' exactly to confirm');
          return;
        }
        if (this.state.delProjBusy) return;
        this.setState({ delProjBusy: true });
        /* Data first, then the project row. If the second call fails the analytics are gone
           but the project remains -- recoverable by re-syncing. The reverse order would
           orphan every analytics row under a site_id nothing can reach. */
        window.FuseAPI.del('/api/projects/' + pid + '/data')
          .then(() => window.FuseAPI.del('/api/projects/' + pid))
          .then(() => {
            if (!this._alive) return;
            const left = (this.state.projects || []).filter(p => p.id !== pid);
            this.setState({ delProjOpen: false, delProjBusy: false, delProjText: '', projects: left, cache: {} });
            this.notify(domain + ' deleted');
            if (left.length) this.setProject(left[0].id); else window.location.reload();
          })
          .catch(err => {
            if (!this._alive) return;
            this.setState({ delProjBusy: false });
            this.notify(this.errText(err, 'Could not delete ' + domain));
          });
      },
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
      cpwSave: () => this.changePassword(),
      openCpwModal: () => this.setState({ cpwOpen: true, cpwOld: '', cpwNew: '', cpwNew2: '', cpwErr: false, cpwMsg: '' }),
      closeCpwModal: () => this.setState({ cpwOpen: false })
    };

    const uCfg = (window.FuseAPI && window.FuseAPI.config && window.FuseAPI.config.user) || { username: 'founder', initials: 'FO', role: 'Internal' };
    const canManageSettings = uCfg.role !== 'Analyst';

    let syncEtaText = '';
    if (s.sync.startTime && s.sync.progress > 0 && s.sync.progress < 1) {
        const elapsed = Date.now() - s.sync.startTime;
        let remainingSec = 0;
        if (s.sync.progress < 0.05 || elapsed < 3000) {
            remainingSec = (activeScope === 'audit' || activeScope === 'pages' || activeScope === 'all') ? 300 : 60;
        } else {
            const totalEst = elapsed / s.sync.progress;
            remainingSec = Math.max(0, Math.round((totalEst - elapsed) / 1000));
        }
        if (remainingSec > 60) syncEtaText = Math.ceil(remainingSec / 60) + 'm remaining';
        else syncEtaText = remainingSec + 's remaining';
    }

    /* Step checklist under the progress bar. Fed entirely by task_status()'s `steps[]` — no
       new table, just RefreshRun/SyncLog fields that already existed (see
       sync_api_service._step_details). Answers "what is it doing right now" and "did step N
       actually run" without anyone needing to open a terminal or a log file. */
    const SYNC_STEP_ICON = {
      done: { text: '✓', bg: '#d1fae5', fg: '#047857' },
      running: { text: '⟳', bg: '#e0e7ff', fg: '#4338ca' },
      pending: { text: '·', bg: '#f1f5f9', fg: '#94a3b8' },
      error: { text: '✗', bg: '#fee2e2', fg: '#b91c1c' },
      skipped: { text: '⊘', bg: '#fef3c7', fg: '#b45309' },
    };
    const syncSteps = (s.sync.steps || []).map(st2 => {
      const ic = SYNC_STEP_ICON[st2.state] || SYNC_STEP_ICON.pending;
      return {
        name: st2.name,
        detail: st2.detail || '',
        dotStyle: { display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '16px', height: '16px', borderRadius: '50%', background: ic.bg, color: ic.fg, fontSize: '10px', fontWeight: 700, flexShrink: 0, animation: st2.state === 'running' ? 'fuseSpin 1s linear infinite' : 'none' },
        dotText: ic.text,
        nameStyle: { fontSize: '12.5px', fontWeight: st2.state === 'running' ? 700 : 500, color: st2.state === 'running' ? '#0f172a' : '#475569' },
      };
    });
    const syncElapsedText = s.sync.elapsed ? (s.sync.elapsed >= 60 ? Math.floor(s.sync.elapsed / 60) + 'm ' + (s.sync.elapsed % 60) + 's' : s.sync.elapsed + 's') : '';

    const vals = {
      cpwOpen: s.cpwOpen, cpwOld: s.cpwOld, cpwNew: s.cpwNew, cpwNew2: s.cpwNew2, cpwErr: s.cpwErr, cpwMsg: s.cpwMsg, cpwBusy: s.cpwBusy,
      acceptInvite: s.acceptInviteToken ? {
        token: s.acceptInviteToken,
        email: s.acceptEmail || 'Loading...',
        role: s.acceptRole || '',
        invitedBy: s.acceptInvitedBy || 'Owner',
        username: s.acceptUsername || '',
        password: s.acceptPassword || '',
        error: s.acceptError || null,
        success: s.acceptSuccess || null,
        /* Pre-computed: the modal used `{{ !acceptInvite.error && !acceptInvite.success }}`,
           and the dc-runtime resolver has no `&&` (support.js resolve() handles parens,
           ===/!==/==/!=, a leading `!`, true/false and paths -- nothing else). It parsed
           that as `!resolve("acceptInvite.error && !acceptInvite.success")`, which is an
           unknown path, so `!undefined` -> TRUE. The signup form therefore rendered even
           on an invalid-token error and after a successful activation. */
        showForm: !s.acceptError && !s.acceptSuccess
      } : null,
      userInitials: uCfg.initials, userName: uCfg.username, userRole: uCfg.role, canManageSettings,
      brandName: project.name || 'FuseHealth',
      projectDomain: project.domain || '',
      h,
      navStyle: { overview: mk('overview'), seo: mk('seo'), domain_overview: sub('domain_overview'), keywords: sub('keywords'), positioning: sub('positioning'), backlinks: sub('backlinks'), offsite: sub('offsite'), pages: sub('pages'), ai: sub('ai'), ads: mk('ads'), campaigns: sub('campaigns'), terms: sub('terms'), attribution: sub('attribution'), alerts: mk('alerts'), settings: mk('settings') },
      dotStyle: { overview: dot('overview'), seo: dot('seo'), ads: dot('ads'), campaigns: sdot('campaigns'), terms: sdot('terms'), attribution: sdot('attribution'), alerts: dot('alerts'), settings: dot('settings'), domain_overview: sdot('domain_overview'), keywords: sdot('keywords'), positioning: sdot('positioning'), backlinks: sdot('backlinks'), offsite: sdot('offsite'), pages: sdot('pages'), ai: sdot('ai') },
      seoOpen: s.seoOpen, adsOpen: s.adsOpen,
      title: titles[tab][0], subtitle: titles[tab][1] + ' · ' + project.domain,
      projects: s.projects.length ? s.projects : [{ id: s.projectId, domain: project.domain }],
      projectId: s.projectId, projectDomain: project.domain,
      addSiteOpen: s.addSiteOpen, addSiteDomain: s.addSiteDomain, addSiteName: s.addSiteName, addSiteError: s.addSiteError,
      addSite: this.addSiteVals(s),
      rangeStyle: { d7: s.range === '7d' ? rActive : rBase, d28: s.range === '28d' ? rActive : rBase, d90: s.range === '90d' ? rActive : rBase },
      hasPageRefresh: !!pageScope,
      refreshPageLabel: isPageSyncing ? 'Syncing…' : (tabToLabel[tab] || 'Fetch page'),
      refreshPageBtnStyle: { display: 'inline-flex', alignItems: 'center', gap: '8px', borderRadius: '8px', background: isPageSyncing ? '#6ee7b7' : '#10b981', color: 'white', fontSize: '14px', fontWeight: 500, padding: '8px 16px', boxShadow: '0 1px 2px rgba(0,0,0,0.05)', cursor: isPageSyncing ? 'default' : 'pointer' },
      refreshPageIconStyle: isPageSyncing ? { animation: 'fuseSpin 1s linear infinite' } : {},
      refreshLabel: isAllSyncing ? 'Syncing all…' : 'Refresh all',
      refreshBtnStyle: { display: 'inline-flex', alignItems: 'center', gap: '8px', borderRadius: '8px', background: isAllSyncing ? '#818cf8' : '#4f46e5', color: 'white', fontSize: '14px', fontWeight: 500, padding: '8px 16px', boxShadow: '0 1px 2px rgba(0,0,0,0.05)', cursor: isAllSyncing ? 'default' : 'pointer' },
      refreshIconStyle: isAllSyncing ? { animation: 'fuseSpin 1s linear infinite' } : {},
      freshness: s.freshness,
      syncing, syncScopeLabel: activeScope === 'all' ? 'all modules' : (scopeToLabel[activeScope] || activeScope || ''), syncStep: s.sync.step, syncPct: Math.round(s.sync.progress * 100),
      syncPctText: Math.round(s.sync.progress * 100) + '%', syncCostText: this.money(s.sync.cost), syncEtaText,
      syncElapsedText, syncSteps, syncStepsCount: syncSteps.length,
      syncPanelOpen: s.syncPanelOpen,
      syncPanelToggleLabel: s.syncPanelOpen ? 'Hide details ▲' : 'Show details ▼',
      syncStopLabel: s.sync.stopping ? 'Stopping…' : 'Stop',
      /* True while Phase 1 is deployed: the sync now runs as its own OS process
         (manage.py run_sync), not a thread inside the web worker, so it survives navigating
         to another page, switching tabs, or even a normal page reload (resumeActiveSync in
         boot() re-attaches to it). This is the reassurance note the user asked for. */
      syncSurviveNote: 'Running in the background — you can keep using the dashboard, and this will keep going even if you navigate away or reload the page.',
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
      /* Re-sorting reshuffles which rows live on which page, so staying on page 7 would show an
         arbitrary slice of the new order. `resetKey` sends the table back to the top. */
      auSort: { score: this.mkSortHandler('auPgSort', 'score', 'auPgPage'), issues: this.mkSortHandler('auPgSort', 'issues', 'auPgPage'), depth: this.mkSortHandler('auPgSort', 'depth', 'auPgPage'), inLinks: this.mkSortHandler('auPgSort', 'inLinks', 'auPgPage'), loadTimeMs: this.mkSortHandler('auPgSort', 'loadTimeMs', 'auPgPage') },
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
        keywords: l.keywords.map(k => { const kw = k.kw || k; return { kw, onRemove: () => this.removeKwFromList(l.id, kw) }; })
      }));
    }

    /* ---------- notification centre (topbar bell) ----------
       In-dashboard only: no Slack, no email. Reads the alerts tab's already-prefetched
       cache (boot() and every completed sync refresh it), so opening the bell never
       touches the network — the database-first contract holds. Computed here, above the
       `if (s.loading || s.error || !data) return vals` guard, because the topbar renders
       on every screen including the loading and error states. */
    {
      const NC_LIMIT = 8;
      /* Mirrors overview_service._KIND_MODULE_MAP exactly (same six kinds, same
         General/alerts fallback) so a row in the bell lands on the same screen as the
         identical row in Overview's priority feed. Labels double as keys into the fixed
         module colours in design.md §4 — do not re-word them. */
      const ncKindModule = {
        anomaly: { label: 'SEO', target: 'seo' },
        ranking: { label: 'Positions', target: 'positioning' },
        backlink: { label: 'Backlinks', target: 'backlinks' },
        technical: { label: 'Site Audit', target: 'pages' },
        ads: { label: 'Ads', target: 'ads' },
        system: { label: 'System', target: 'alerts' }
      };
      const ncModColor = { SEO: '#4f46e5', Positions: '#0891b2', Backlinks: '#7c3aed', 'Site Audit': '#dc2626', Ads: '#059669', System: '#64748b', General: '#64748b' };
      const ncSevColor = { high: '#dc2626', medium: '#d97706', info: '#94a3b8' };
      const ncSevRank = { high: 0, medium: 1, info: 2, low: 3 };
      const ncRank = f => (ncSevRank[f.severity] == null ? 9 : ncSevRank[f.severity]);
      /* Same order the server builds Overview's priority feed with (overview_service
         .build_priority_feed): two stable passes — newest ts first, then highest
         severity first — so the two lists never disagree about what matters most. */
      const ncSorted = unackedFeed.slice()
        .sort((a, b) => (a.ts < b.ts ? 1 : (a.ts > b.ts ? -1 : 0)))
        .sort((a, b) => ncRank(a) - ncRank(b));
      const ncShown = ncSorted.slice(0, NC_LIMIT);
      const ncOn = s.ncOpen;

      vals.ncOpen = ncOn;
      vals.ncTriggerStyle = {
        position: 'relative', display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
        width: '32px', height: '32px', borderRadius: '8px',
        border: '1px solid ' + (ncOn ? '#c7d2fe' : '#e2e8f0'),
        background: ncOn ? '#eef2ff' : 'white',
        color: ncOn ? '#4338ca' : '#475569',
        cursor: 'pointer'
      };
      vals.ncBadgeStyle = { position: 'absolute', top: '-6px', right: '-6px', minWidth: '16px', height: '16px', padding: '0 4px', borderRadius: '9999px', background: '#dc2626', color: 'white', fontSize: '10px', fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center', border: '2px solid white' };
      vals.ncBadgeText = unacked > 99 ? '99+' : String(unacked);
      /* The badge digits are aria-hidden, so the count has to live in the label. */
      vals.ncAria = unacked === 0
        ? 'Notifications — no unread alerts'
        : 'Notifications — ' + unacked + ' unread alert' + (unacked === 1 ? '' : 's');
      vals.ncCountText = unacked === 0 ? 'Nothing unread' : unacked + ' unread';
      vals.ncEmpty = ncShown.length === 0;
      vals.ncCanAckAll = ncShown.length > 0;
      vals.ncHasMore = ncSorted.length > ncShown.length;
      vals.ncMoreText = 'Showing ' + ncShown.length + ' of ' + ncSorted.length;
      vals.ncItems = ncShown.map((f, i) => {
        const mod = ncKindModule[f.kind] || { label: 'General', target: 'alerts' };
        const modC = ncModColor[mod.label] || '#64748b';
        const rel = this.relTime(f.ts);
        return {
          title: f.title, timeFmt: rel, moduleLabel: mod.label,
          aria: f.title + ' — ' + mod.label + ', ' + rel,
          sevDotStyle: { width: '8px', height: '8px', borderRadius: '9999px', background: ncSevColor[f.severity] || '#94a3b8', marginTop: '5px', flexShrink: 0 },
          moduleStyle: { fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em', color: modC, background: modC + '14', padding: '2px 7px', borderRadius: '4px' },
          rowStyle: { display: 'flex', gap: '10px', alignItems: 'flex-start', padding: '11px 14px', cursor: 'pointer', borderTop: i === 0 ? 'none' : '1px solid #f1f5f9' },
          onClick: () => { this.setState({ ncOpen: false }); this.go(mod.target); }
        };
      });
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
        questions: { ep: 'keyword_ideas + question filters', desc: 'Questions people ask in this topic (how / what / is / can\u2026), filtered server-side by DataForSEO' },
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
          serpHref: 'https://www.google.com/search?q=' + encodeURIComponent(drRow.kw) + this.googleSerpLocationParam(s.research.location),
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

    /* #include "js/pages/domain_overview.js" */

    if (s.loading || s.error || !data) return vals;

    /* #include "js/pages/overview.js" */
    /* #include "js/pages/seo.js" */
    /* #include "js/pages/keywords.js" */
    /* #include "js/pages/positioning.js" */
    /* #include "js/pages/backlinks.js" */
    /* #include "js/pages/offsite.js" */
    /* #include "js/pages/site_audit.js" */
    /* #include "js/pages/ai_optimization.js" */
    /* #include "js/pages/ads.js" */
    /* #include "js/pages/alerts.js" */
    /* #include "js/pages/settings.js" */
