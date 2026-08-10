    /* ============ POSITIONING ============ */
    if (tab === 'positioning') {
      vals.showPositioning = true;
      vals.ptIsList = s.ptView !== 'workspace';
      vals.ptIsWorkspace = s.ptView === 'workspace';
      vals.ptWizOpen = s.ptWizOpen;
      vals.ptEditOpen = s.ptEditOpen;
      vals.ptEditBusy = s.ptEditBusy;
      /* The template engine's {{ }} resolver (vendor/support.js resolve/resolvePath) handles
         paths, literals and ==/!= only — it has no ternary. `{{ ptEditBusy ? 'Saving...' :
         'Save Settings' }}` fell through to resolvePath, hit the space after the identifier,
         returned undefined, and rendered as an empty button. Labels are computed here instead,
         same as ptWiz.nextLabel below. */
      vals.ptEditSaveLabel = s.ptEditBusy ? 'Saving...' : 'Save Settings';
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
      vals.ptEditLoc = s.ptEditLoc || '';
      vals.ptEditLocFn = e => this.setState({ ptEditLoc: e.target.value });
      vals.ptEditClose = () => this.setState({ ptEditOpen: false, ptEditBusy: false });
      vals.ptEditSave = () => {
        if (s.ptEditBusy) return;
        this.setState({ ptEditBusy: true });
        const kwLines = (s.ptEditKws || '').split(/\r?\n/).map(l => l.trim()).filter(Boolean);
        /* NAMES ONLY. This used to send `{volume: 0, kd: null, cpc: null, intent:
           'Informational'}` for every row, and the endpoint cleared the list and rewrote it —
           so each save overwrote every keyword's real search volume with a fabricated 0 and
           wiped its difficulty, CPC and intent. The endpoint now reconciles by name and leaves
           surviving rows alone; sending blanks here would have nothing to write over, but this
           states the intent rather than relying on that. */
        const kwsToSend = kwLines.map(kw => ({ kw: kw }));
        const comps = s.ptWizComps || [];

        /* Clearing the whole list is legal but destructive, and a stray Ctrl+A in the textarea
           looks identical to meaning it. Confirm when the save would empty a non-empty list. */
        const hadKeywords = ((s.ptEditKwsInitial || '').split(/\r?\n/).filter(l => l.trim())).length;
        if (!kwLines.length && hadKeywords) {
          if (!window.confirm('Remove all ' + hadKeywords + ' tracked keywords from this project?')) {
            this.setState({ ptEditBusy: false });
            return;
          }
        }

        /* Search engine / device / language travel with the save. They used to be
           collected by the three selects above and then dropped on the floor — the PUT
           body carried only competitors/name/location, and Site had no column for them.
           apply_settings_update reads them out of body.project, same as the others. */

        /* Both halves are reported, and a failure is never silent. Each PUT used to end in
           `.catch(() => {})` INSIDE the Promise.all, so a refused save resolved as success:
           the modal closed, a "Project updated" toast fired, a sync started, and nothing had
           been stored. `settle` keeps both requests independent (Promise.all would otherwise
           abandon the second the moment the first rejects) without needing Promise.allSettled,
           which is ES2020 and this bundle is ES2017. A rejection resolves to the error; a
           success resolves to null. */
        const settle = (p) => p.then(() => null, err => err || new Error('request failed'));
        /* SEQUENCED, not raced. These used to run inside one Promise.all, and the keywords
           endpoint stamps new rows with `request.location or site.location` — so whether a
           newly added keyword was filed under the old or the new location depended on which
           request committed first. Settings lands the location, then the keyword reconcile
           runs against it. */
        settle(window.FuseAPI.put('/api/projects/' + s.projectId + '/settings', { project: { competitors: comps, name: s.ptEditName, location: s.ptEditLoc, search_engine: s.ptEditEngine, device: s.ptEditDevice, language: s.ptEditLang } }))
          .then(settingsErr => settle(
            window.FuseAPI.put('/api/projects/' + s.projectId + '/keywords', { keywords: kwsToSend })
          ).then(kwErr => [settingsErr, kwErr]))
          .then(results => {
          if (!this._alive) return;
          const settingsErr = results[0];
          const kwErr = results[1];
          if (settingsErr || kwErr) {
            /* Revert the optimistic "Saving..." label and LEAVE THE MODAL OPEN, so the user
               keeps their edits and can retry. Both PUTs are idempotent, so retrying after a
               partial failure re-sends the half that already landed harmlessly. The message
               names which half failed rather than implying both did. */
            this.setState({ ptEditBusy: false });
            const fallback = (settingsErr && kwErr)
              ? 'Could not save your project changes'
              : (settingsErr
                ? 'Could not save the project settings — your keyword list was saved'
                : 'Could not save the tracked keywords — your project settings were saved');
            if (this.notify) this.notify(this.errText(settingsErr || kwErr, fallback));
            return;
          }
          this.setState({ ptEditBusy: false, ptEditOpen: false });
          /* The project list carries name, location and the visibility figure, and it is only
             fetched at boot and after create/delete — so without this the switcher and the
             list kept showing the pre-edit values for the rest of the session while the
             workspace showed the new ones. */
          window.FuseAPI.get('/api/projects').then(ps => { if (this._alive) this.setState({ projects: ps }); }).catch(() => {});
          this.startSync('positions');
          if (this.notify) this.notify('Project updated. Refreshing positions...');
        });
      };

      /* The wizard's keyword textarea is labelled "(comma-separated)" in
         positioning.html, but ptCreateAndSend fills the same field by joining
         selected rows with newlines — so both separators legitimately arrive
         here. One splitter feeds BOTH the on-screen counter and the submit
         payload, so the count the user sees can never disagree with the number
         of keywords actually created. */
      const ptSplitKws = (txt) => (txt || '').split(/[\n,]+/).map(k => k.trim()).filter(Boolean);

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

        // Position Tracking allows adding the same domain again as a second, independent
        // project (its own tracking-area settings, keyword list and competitors) — the
        // client-side block that used to sit here (and the backend's own duplicate-domain
        // guard) are bypassed for this one path via allow_duplicate. Every other project
        // creation path (topbar "+", Settings) still rejects a duplicate domain.
        this.setState({ ptWizBusy: true });
        window.FuseAPI.post('/api/projects', { domain: domainStr, name: (this.state.ptWizName || '').trim() || undefined, location: this.state.ptWizLoc, allow_duplicate: true })
          .then(p => {
            if (!this._alive) return;
            this.setState({ ptWizBusy: false, ptWizOpen: false, ptView: 'workspace', ptTab: 'landscape', projectId: p.id });

            // Save the tracking-area choices and the competitors. apply_settings_update
            // only reads body["project"]; a top-level key is dropped on the floor, so this
            // must match the shape ptEditSave sends.
            //
            // WHY A SECOND CALL rather than putting them in the POST above: POST
            // /api/projects is validated by ProjectCreateSerializer, which accepts only
            // domain/name/vertical/location. Sending more there is silently discarded.
            // This PUT now always fires — it used to be skipped whenever no competitor was
            // entered, which is exactly when the engine/device/language picks would have
            // been lost. Step 2 of the wizard collects all three and, until now, nothing
            // ever sent them anywhere.
            const wizComps = this.state.ptWizComps || [];
            window.FuseAPI.put('/api/projects/' + p.id + '/settings', {
              project: {
                competitors: wizComps,
                search_engine: this.state.ptWizEngine,
                device: this.state.ptWizDevice,
                language: this.state.ptWizLang
              }
            }).catch(err => {
              /* Not silent: the project itself was created (the POST above resolved), but
                 the wizard's step-2 and step-4 answers were not stored. Saying so is the
                 only way the user learns to re-enter them in Edit Project — a swallowed
                 rejection here reads as "everything saved" and the settings are simply gone. */
              if (!this._alive) return;
              if (this.notify) this.notify(this.errText(err, 'Project created, but its tracking area and competitors could not be saved — set them in Edit Project'));
            });

            let kwsToSend = [];
            const mkRow = kw => ({ kw: kw, volume: 0, kd: null, cpc: null, intent: 'Informational' });
            if (this._pendingSendRows && this._pendingSendRows.length) {
              kwsToSend = this._pendingSendRows;
              this._pendingSendRows = null;
            } else if (this.state.ptWizKwMode === 'list') {
              /* "Choose a list" mode stores only the list id — resolve it against
                 kwLists here, or the project is created with zero keywords. */
              const picked = (this.state.kwLists || []).find(l => l.id === this.state.ptWizListId);
              const listKws = (picked && picked.keywords) || [];
              kwsToSend = listKws
                .map(k => (typeof k === 'string' ? k : (k && k.kw) || '').trim())
                .filter(Boolean)
                .map(mkRow);
            } else if (this.state.ptWizKwText && this.state.ptWizKwText.trim()) {
              kwsToSend = ptSplitKws(this.state.ptWizKwText).map(mkRow);
            }
            if (kwsToSend.length > 0) {
              this.sendKwsToTracking(p.id, kwsToSend);
            } else {
              /* Silent on purpose: a post-success re-read of the project switcher, not a
                 mutation. The create already succeeded and the user has already been told;
                 a second toast contradicting that to report a stale switcher count would be
                 worse than the stale count, which the next render fixes anyway. */
              window.FuseAPI.get('/api/projects').then(ps => { if (this._alive) this.setState({ projects: ps }); }).catch(() => {});
              this.fetchTab('positioning', p.id, this.state.range, true);
              if (this.notify) this.notify('SEO project created for ' + p.domain);
            }
          })
          /* Reverts the optimistic "Creating…" button label and leaves the wizard open on
             its last step so the entered domain/keywords/competitors survive a retry. */
          .catch(err => { if (this._alive) { this.setState({ ptWizBusy: false }); if (this.notify) this.notify(this.errText(err, 'Could not create project')); } });
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
      /* Visibility is the backend's Semrush-style score (`visibility` on the project
         payload): CTR-curve points for each tracked keyword's position — the same curve as
         buildVisibilityScores below — over a perfect #1-on-every-keyword, with keywords that
         rank nowhere still counted in the denominator. The previous (100 - avg_position)/1.2
         mapping averaged RANKED keywords only, so one branded keyword at #2 out of 48
         tracked read 82% when the honest CTR-weighted reading was ~1%. null means "never
         captured" → "—"; 0 means "captured, ranks nowhere" — a real 0%.

         NO BAR, deliberately. The cell used to pair this percentage with a track and a fill,
         and the fill was an inline <span>: CSS gives a non-replaced inline box no width and no
         height, so every width this function computed was applied to a box that could not use
         it. The bar has never rendered for any project since the column shipped — just an
         empty grey track beside the number. Removed rather than repaired: the coloured
         percentage already carries the whole reading, and the 1.5% minimum "sliver" this used
         to compute would not have been legible even if the box had accepted a width.
         Self-contained so tests/project_list_visibility.test.js can brace-match it. */
      const listVisibility = p => {
        const v = typeof p.visibility === 'number' ? p.visibility : null;
        if (v == null) return { hasVis: false, vis: 0, label: '—', color: '#cbd5e1' };
        return {
          hasVis: true, vis: v,
          label: parseFloat(v.toFixed(1)) + '%',
          color: v >= 30 ? '#059669' : v >= 10 ? '#0891b2' : '#d97706'
        };
      };
      vals.ptProjects = projList.map(p => {
        const isCur = p.id === s.projectId;
        const tracked = p.tracked_keywords_count || 0;
        const lv = listVisibility(p);
        const improved = p.improved_count || 0;
        const declined = p.declined_count || 0;
        /* Row subtitle. `device` used to be the literal 'Desktop' for every project,
           regardless of what the wizard collected. The projects LIST endpoint
           (ProjectSerializer) does not expose the stored device/engine/language yet, so
           this prints the parts it actually has and omits the ones it does not, rather
           than asserting a default as though it were the user's choice. The keys stay
           present so the template needs no change when the serializer catches up. */
        const subParts = [p.domain, p.device, p.location].filter(Boolean);
        return {
          id: p.id, name: p.name || p.domain, domain: p.domain, location: p.location || '', device: p.device || '',
          sub: subParts.join(' · '),
          tracked: this.fmt(tracked), improved, declined,
          visLabel: lv.label, visColor: lv.color,
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
      
      vals.ptLocSearchOpen = !!s.ptLocSearchOpen;
      vals.ptLocSearchTarget = s.ptLocSearchTarget;
      
      vals.ptLocFocusWiz = () => this.setState({ ptLocSearchOpen: true, ptLocSearchTarget: 'wiz' });
      vals.ptLocFocusEdit = () => this.setState({ ptLocSearchOpen: true, ptLocSearchTarget: 'edit' });
      vals.ptLocBlur = () => this.setState({ ptLocSearchOpen: false });
      
      let searchResults = [];
      if (s.ptLocSearchOpen && s.allUsCities) {
        const q = ((s.ptLocSearchTarget === 'wiz' ? s.ptWizLoc : s.ptEditLoc) || '').toLowerCase();
        searchResults = q ? s.allUsCities.filter(c => c.toLowerCase().includes(q)).slice(0, 100) : ['United States', 'Canada', 'United Kingdom', 'Australia'].concat(s.allUsCities.slice(0, 96));
      }
      vals.ptLocSearchResults = searchResults.map(c => {
        let label = c;
        if (c.startsWith("United States - ")) {
          label = c.substring(16) + ", United States";
        }
        return {
          val: c,
          label: label,
          onPick: () => {
            if (s.ptLocSearchTarget === 'wiz') {
              this.setState({ ptWizLoc: c, ptLocSearchOpen: false });
            } else if (s.ptLocSearchTarget === 'edit') {
              this.setState({ ptEditLoc: c, ptLocSearchOpen: false });
            }
          }
        };
      });

      vals.ptWiz = {
        stepItems: wizSteps.map((nm, i2) => { const n = i2 + 1; const st2 = n < s.ptWizStep ? 'done' : n === s.ptWizStep ? 'active' : 'todo'; return { label: nm, n, circleStyle: { width: '26px', height: '26px', borderRadius: '9999px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px', fontWeight: 600, background: st2 === 'todo' ? '#f1f5f9' : '#4f46e5', color: st2 === 'todo' ? '#94a3b8' : 'white', flexShrink: 0 }, labelStyle: { fontSize: '13px', fontWeight: st2 === 'active' ? 600 : 400, color: st2 === 'todo' ? '#94a3b8' : '#334155', whiteSpace: 'nowrap' } }; }),
        isStep1: s.ptWizStep === 1, isStep2: s.ptWizStep === 2, isStep3: s.ptWizStep === 3, isStep4: s.ptWizStep === 4,
        domain: s.ptWizDomain, name: s.ptWizName,
        engine: s.ptWizEngine, language: s.ptWizLang, location: s.ptWizLoc, device: s.ptWizDevice,
        engineOpts: ['Google', 'Bing'], langOpts: ['English', 'Spanish', 'French'], 
        deviceOpts: ['Desktop', 'Mobile'],
        kwMode: s.ptWizKwMode, kwPaste: s.ptWizKwMode === 'paste', kwList: s.ptWizKwMode === 'list',
        kwText: s.ptWizKwText, kwCount: ptSplitKws(s.ptWizKwText).length,
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
        /* The project's stored tracking-area choices, from /api/positions' `project` key.
           The header used to print a hardcoded 'Desktop'; it now prints what the user
           picked in the wizard. Defaults only cover the moment before `data` arrives —
           the server sends the same defaults for a row whose column is NULL. */
        const ptPrefs = (data && data.project) || {};
        const wsEngine = ptPrefs.search_engine || 'Google';
        const wsDevice = ptPrefs.device || 'Desktop';
        const wsLang = ptPrefs.language || 'English';
        const wsLoc = ptPrefs.location || proj.location || 'United States';
        vals.ptWs = {
          name: proj.name || proj.domain || 'Project',
          domain: proj.domain || '',
          engine: wsEngine,
          device: wsDevice,
          language: wsLang,
          location: wsLoc,
          meta: [proj.domain || '', wsEngine, wsDevice, wsLang, wsLoc].filter(Boolean).join(' · '),
          onEdit: () => {
            this.setState({
              ptEditOpen: true, ptEditBusy: false, ptEditKws: '', ptEditKwsInitial: '',
              ptWizComps: [], ptWizCompInput: '',
              ptEditDomain: proj.domain || '',
              ptEditName: proj.name || '',
              ptEditEngine: wsEngine,
              ptEditDevice: wsDevice,
              ptEditLang: wsLang,
              ptEditLoc: ptPrefs.location || proj.location || ''
            });
            window.FuseAPI.get('/api/projects/' + proj.id + '/settings').then(res => {
              if (this.state.ptEditOpen && res && res.project) {
                /* The settings response is the authoritative read of the stored row —
                   seed the three selects from it so the modal opens on what is saved,
                   not on what the header happened to have cached. */
                this.setState({
                  ptEditKws: (res.project.tracked_keywords || []).join('\n'),
                  /* What the modal opened with, so Save can tell "user cleared the box" from
                     "the box never loaded" before it removes anyone's tracked list. */
                  ptEditKwsInitial: (res.project.tracked_keywords || []).join('\n'),
                  ptWizComps: (res.project.competitors || []),
                  ptEditEngine: res.project.search_engine || wsEngine,
                  ptEditDevice: res.project.device || wsDevice,
                  ptEditLang: res.project.language || wsLang,
                  ptEditLoc: res.project.location || ''
                });
              }
            }).catch(err => {
              /* This is a read, but a swallowed one is DESTRUCTIVE here: the keyword
                 textarea would stay empty and Save replaces the tracked keyword list
                 wholesale — so a silent failure turns "open Edit, hit Save" into "delete
                 every tracked keyword". Close the modal and say why, rather than presenting
                 a form whose blank fields are indistinguishable from real emptiness. */
              if (!this._alive) return;
              this.setState({ ptEditOpen: false, ptEditBusy: false });
              if (this.notify) this.notify(this.errText(err, "Could not load this project's settings — nothing was changed"));
            });
          },
          onDelete: () => {
            if (confirm('Are you sure you want to delete this project?')) {
              /* FuseAPI exports { config, get, post, put, del } — `delete` is a
                 reserved word and is not on the transport. */
              window.FuseAPI.del('/api/projects/' + proj.id).then(() => {
                if (!this._alive) return;
                this.setState({ ptView: 'list', projectId: null });
                /* Silent on purpose: a post-success re-read of the project switcher, not a
                   mutation. The delete already succeeded; a failure toast here would
                   contradict it to report nothing worse than a stale list. */
                window.FuseAPI.get('/api/projects').then(ps => { if (this._alive) this.setState({ projects: ps }); }).catch(() => {});
              }).catch(err => { if (this._alive && this.notify) this.notify(this.errText(err, 'Could not delete project')); });
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

      /* ---- Keyword Opportunities ----
         Every figure is server-computed and server-explained (`rationale`); nothing is
         derived here beyond the colours. `estimated_traffic_gain` is null for every row
         and renders "—": turning a position change into a click count needs a
         position→CTR curve, and this project has no real one. See the footnote below,
         which states that on screen rather than leaving a silent dash. */
      const oppTint = {
        quick_win: ['#d1fae5', '#047857'],
        rising: ['#dbeafe', '#1d4ed8'],
        striking_distance: ['#e0e7ff', '#4338ca'],
        content_gap: ['#fef3c7', '#b45309']
      };
      const buildOpps = (list) => (list || []).map(o => {
        const tint = oppTint[o.type] || ['#f1f5f9', '#64748b'];
        const sc = o.score != null ? Number(o.score) : null;
        return {
          kw: o.keyword,
          pos: o.position != null ? o.position : '—',
          posStyle: this.posBadge(o.position != null ? o.position : null),
          typeLabel: o.type_label || '—',
          typeStyle: { display: 'inline-flex', alignItems: 'center', padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 600, background: tint[0], color: tint[1] },
          volume: this.fmt(o.volume),
          kd: o.kd != null ? Math.round(o.kd) : '—',
          kdStyle: { fontSize: '13px', color: o.kd != null ? (o.kd < 30 ? '#10b981' : (o.kd < 60 ? '#f59e0b' : '#ef4444')) : '#cbd5e1' },
          gain: o.estimated_traffic_gain != null ? this.fmt(o.estimated_traffic_gain) : '—',
          gainStyle: { fontSize: '13px', fontWeight: 600, color: o.estimated_traffic_gain != null ? '#059669' : '#cbd5e1' },
          score: sc != null ? sc.toFixed(1) : '—',
          scoreStyle: { fontSize: '13px', fontWeight: 700, color: sc == null ? '#94a3b8' : (sc >= 60 ? '#059669' : (sc >= 35 ? '#d97706' : '#64748b')) },
          rationale: o.rationale || ''
        };
      });

      /* ---- Competitor Map ----
         An aggregate of the SAME captured rows the per-keyword grid renders — never an
         estimate. A competitor with no captured row for a keyword contributes nothing to
         its own position statistics; with no captured rows at all the map renders its
         empty state instead of a picture. */
      const buildMap = (mp) => {
        mp = mp || {};
        const doms = (mp.domains || []).filter(d => d && d.avg_position != null);
        const palette = ['#a855f7', '#f59e0b', '#ef4444', '#10b981', '#06b6d4', '#7c3aed'];
        const hasPoints = mp.status === 'ok' && doms.length > 0;
        const worst = doms.reduce((m, d) => Math.max(m, d.avg_position), 0);
        const yMax = Math.max(20, Math.ceil(worst / 10) * 10);
        const X0 = 70, X1 = 700, Y0 = 22, Y1 = 208;
        const cxOf = pct => X0 + (Math.max(0, Math.min(100, pct)) / 100) * (X1 - X0);
        const cyOf = pos => Y0 + ((Math.max(1, Math.min(yMax, pos)) - 1) / (yMax - 1)) * (Y1 - Y0);
        let compIdx = 0;
        const points = doms.map(d => {
          const color = d.is_you ? '#4f46e5' : palette[(compIdx++) % palette.length];
          return {
            name: d.domain, color: color,
            cx: Math.round(cxOf(Number(d.coverage_pct) || 0) * 10) / 10,
            cy: Math.round(cyOf(Number(d.avg_position)) * 10) / 10,
            r: Math.round((7 + Math.min(13, Math.sqrt(Number(d.top10) || 0) * 4)) * 10) / 10,
            labelDy: -12,
            labelStyle: { fontSize: '11px', fontWeight: d.is_you ? 700 : 500 }
          };
        });
        const gridY = [1, Math.round(yMax / 4), Math.round(yMax / 2), yMax].map(p => ({ y: Math.round(cyOf(p) * 10) / 10, label: '#' + p }));
        const gridX = [0, 25, 50, 75, 100].map(p => ({ x: Math.round(cxOf(p) * 10) / 10, label: p + '%' }));
        let caption = '';
        if (mp.status === 'ok') {
          caption = 'Captured ' + (mp.captured_date || '—') +
            (mp.your_date && mp.your_date !== mp.captured_date ? ' · your ranks from ' + mp.your_date : '') +
            ' · ' + mp.keywords_captured + ' of ' + mp.tracked_total + ' tracked keywords have a capture' +
            (mp.volume_weighted ? ' · visibility is volume-weighted' : ' · no search volume on record, so visibility weights every keyword equally');
        }
        return {
          hasPoints: hasPoints,
          noCompetitors: mp.status === 'no_competitors',
          noData: mp.status !== 'ok' && mp.status !== 'no_competitors',
          emptyFiltered: mp.status === 'ok' && doms.length === 0,
          caption: caption,
          chart: { viewBox: '0 0 720 240', gridY: gridY, gridX: gridX, x0: X0, x1: X1, y0: Y0, y1: Y1, xLabelY: 226, points: points },
          gridCols: 'minmax(160px, 1.6fr) 90px 90px 80px 80px 110px 90px',
          rows: (mp.domains || []).map(d => ({
            domain: d.domain,
            isYou: !!d.is_you,
            nameStyle: { fontSize: '13px', fontWeight: d.is_you ? 700 : 500, color: d.is_you ? '#4338ca' : '#334155', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' },
            keywords: d.keywords_ranked,
            coverage: d.coverage_pct + '%',
            avgPos: d.avg_position != null ? d.avg_position : '—',
            avgPosStyle: this.posBadge(d.avg_position != null ? Math.round(d.avg_position) : null),
            top10: d.top10,
            /* Head-to-head is only counted where BOTH sides have a real position on the
               same capture — never inferred from a missing cell. */
            h2h: d.is_you ? '—' : (d.head_to_head ? (d.beats_you + ' / ' + d.head_to_head) : '—'),
            h2hStyle: { fontSize: '13px', color: d.is_you ? '#cbd5e1' : (d.head_to_head && d.beats_you > d.you_beat ? '#dc2626' : '#475569') },
            vis: d.visibility != null ? d.visibility + '%' : '—',
            rowStyle: { display: 'grid', gridTemplateColumns: 'minmax(160px, 1.6fr) 90px 90px 80px 80px 110px 90px', alignItems: 'center', padding: '11px 20px', borderTop: '1px solid #f1f5f9', background: d.is_you ? '#f5f7ff' : 'white' }
          }))
        };
      };

      const ptSetup = !data || !data.kpis || data.kpis.state === 'setup' || (data.kpis.tracked === 0 && (!data.movers || !data.movers.length) && (!data.competitors || !data.competitors.rows || !data.competitors.rows.length) && (!data.rankings || !data.rankings.length));
      if (ptSetup) {
        /* Setup state: nothing measured on screen, so nothing to attribute. */
        vals.pt = { setup: true, tracked: 0, avgPos: 0, traffic: 0, impressions: 0, distSegs: [], distLegend: [], improved: 0, declined: 0, added: 0, lost: 0, movers: [], compDomains: [], compGridCols: '', compRows: [], rankings: [], filteredRankings: [], trackedCount: 0, newRows: [], hasNewRows: false,
          srcKpis: this.srcBadge(null), srcDist: this.srcBadge(null), srcMovers: this.srcBadge(null),
          srcRankings: this.srcBadge(null), srcOpps: this.srcBadge(null), srcVisibility: this.srcBadge(null),
          volCoverage: { show: false, text: '', title: '' } };
        vals.ptOpp = { rows: [], isEmpty: true, gridCols: '' };
        vals.ptMap = buildMap(null);
        return vals;
      }
      const oppRows = buildOpps(data.opportunities);
      vals.ptOpp = {
        rows: oppRows,
        isEmpty: oppRows.length === 0,
        gridCols: 'minmax(200px, 2fr) 90px 150px 100px 80px 100px 80px'
      };
      vals.ptMap = buildMap(data.competitor_map);
      const dist = data.distribution;
      const total = Math.max(1, dist.top3 + dist.p4_10 + dist.p11_20 + dist.p21_100);
      const distDefs = [
        ['Top 3', dist.top3, '#10b981'], ['4–10', dist.p4_10, '#3b82f6'],
        ['11–20', dist.p11_20, '#f59e0b'], ['21–100', dist.p21_100, '#cbd5e1']
      ];
      /* Provenance. This page's positions come from dataforseo_serp — the connector its own
         Refresh button actually runs. gsc_keywords used to be named here too (it also writes
         into keyword_rankings), but it left the positioning scope on 2026-08-06: naming a
         connector this page's refresh can no longer run meant a stale gsc_keywords error kept
         the badge red forever, telling the user to fix something this page cannot fix. Its
         clicks/impressions enrichment is still credited where it is shown (the Keywords page,
         whose scope runs it). Competitor surfaces are a different lineage entirely --
         competitor_keyword_rankings comes from dataforseo_serp_competitors and the discovered
         domain list from dataforseo_labs_competitors -- so they carry their own badge rather
         than inheriting the page's. Opportunities are scored from the merged rows, so they
         name every input. */
      const POS_SRC = ['dataforseo_serp'];
      const COMP_SRC = ['dataforseo_serp_competitors', 'dataforseo_labs_competitors'];
      vals.pt = {
        srcKpis: this.srcBadge(POS_SRC),
        srcDist: this.srcBadge(POS_SRC),
        srcMovers: this.srcBadge(POS_SRC),
        srcRankings: this.srcBadge(POS_SRC.concat(['dataforseo_keywords']).concat(COMP_SRC)),
        /* Data-quality note the API has always sent and the UI never rendered: how many
           tracked keywords still have no stored search volume, and why. Shown only when
           there IS a gap — full coverage needs no banner. */
        volCoverage: (data.volume_coverage && data.volume_coverage.missing_volume > 0) ? {
          show: true,
          text: data.volume_coverage.with_volume + ' of ' + data.volume_coverage.tracked + ' keywords have search volume',
          title: data.volume_coverage.note || ''
        } : { show: false, text: '', title: '' },
        srcOpps: this.srcBadge(POS_SRC.concat(['dataforseo_keywords'])),
        srcVisibility: this.srcBadge(POS_SRC.concat(['dataforseo_keywords'])),
        /* The Competitor Map view was removed, but its source is still shown: the Rankings
           Overview table below carries a column per competitor, and those cells come from
           dataforseo_serp_competitors -- a different connector from your own positions. So
           srcRankings names both lineages and reports whichever ran longest ago. */
        tracked: data.kpis.tracked, avgPos: data.kpis.avg_pos != null ? Math.round(data.kpis.avg_pos) : 0,
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
          const d = k.prevPos != null && k.pos != null ? Math.round(k.prevPos - k.pos) : null;
          const posVal = k.pos != null ? Math.round(k.pos) : null;
          const prevVal = k.prevPos != null ? Math.round(k.prevPos) : null;
          return {
            kw: k.kw, was: prevVal != null ? '#' + prevVal : '—', now: posVal != null ? posVal : '—', posStyle: this.posBadge(posVal),
            change: d != null ? ((d > 0 ? '▲ +' : '▼ −') + Math.abs(d)) : '—',
            chipStyle: { padding: '3px 8px', borderRadius: '4px', fontSize: '12px', fontWeight: 600, background: d > 0 ? '#d1fae5' : '#fee2e2', color: d > 0 ? '#047857' : '#b91c1c' },
            volFmt: this.fmt(k.volume)
          };
        }),
        compDomains: data.competitors.domains,
        compGridCols: 'minmax(180px, 1.4fr) repeat(' + (1 + data.competitors.domains.length) + ', 1fr)',
        /* Same rule as the main table: hide only the keywords NOBODY HAS MEASURED YET, not
           the ones measured and found outside the top 30. Filtering on `row.you.pos != null`
           dropped exactly the rows a user most wants here — a keyword where a competitor
           ranks and you do not is the gap this grid exists to show, and it was invisible. */
        compRows: data.competitors.rows.filter(row => row.you && row.you.measured).map(row => {
          const mapCell = c => {
            if (c == null || c.pos == null) return { text: '—', style: { color: '#cbd5e1' }, diff: '', diffStyle: {}, url: '', domain: (c && c.domain) || '' };
            const pos = Math.round(c.pos);
            const d = c.diff;
            const dir = c.direction;
            let diffStr = '';
            let diffSty = { fontSize: '11px', fontWeight: 600, marginLeft: '4px' };
            if (d && dir === 'up') { diffStr = '▲' + d; diffSty.color = '#059669'; }
            else if (d && dir === 'down') { diffStr = '▼' + d; diffSty.color = '#dc2626'; }
            /* Carry the cell's OWN ranking URL through. It used to be dropped here, so the
               table below fell back to your row-level URL and every competitor cell popped up
               one of YOUR pages. */
            return { text: pos, style: this.posBadge(pos), diff: diffStr, diffStyle: diffSty, url: c.url || '', domain: c.domain || '' };
          };
          return {
            kw: row.kw,
            cells: [mapCell(row.you)].concat((row.comps || []).map(mapCell))
          };
        }),
        rankings: (data.rankings || data.keywords || []).map(k => {
          const d = k.prevPos != null && k.pos != null ? Math.round(k.prevPos - k.pos) : null;
          const posVal = k.pos != null ? Math.round(k.pos) : null;
          const prevVal = k.prevPos != null ? Math.round(k.prevPos) : null;
          const iLower = (k.intent || '').toLowerCase();
          return {
            /* Raw numerics travel alongside the display strings. The Pages tab has to do
               arithmetic on these, and `this.fmt` renders 120000 as "120K" — which
               parseInt reads back as 120. Never re-parse a formatted value. */
            posNum: posVal, prevNum: prevVal,
            volNum: k.volume != null ? Number(k.volume) || 0 : 0,
            clicksNum: k.clicks != null ? Number(k.clicks) || 0 : 0,
            intentKey: iLower,
            kw: k.kw,
            pos: posVal != null ? posVal : '—',
            posBadgeStyle: this.posBadge(posVal),
            deltaText: d != null ? (d > 0 ? '▲ +' + d : (d < 0 ? '▼ −' + Math.abs(d) : '—')) : (posVal != null ? 'NEW' : '—'),
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
        /* SPLIT ON `measured`, NOT ON `pos`.
           `pos == null` conflates two different facts and this table used to split on it:
             measured:true,  pos:null  -> checked today, the domain is not in the top 30.
                                          A REAL RESULT. Belongs in Rankings Overview with an
                                          em dash in the Pos column.
             measured:false, pos:null  -> no rank connector has ever looked. Belongs in
                                          "Newly Added Keywords — Not Tracked Yet".
           Splitting on `pos` sent every just-measured non-ranking keyword straight back into
           the "Not Tracked Yet" card, under copy reading "no captured position yet" — so a
           user who ran Fetch Positions, watched it succeed and paid for it was told it had
           not happened, and offered a button to buy it again. `measured` comes from
           keyword_rankings.rank_checked_at; see the column comment in pipeline/db/schema.py. */
        trackedCount: (data.rankings || data.keywords || []).filter(k => k.measured).length,
        // Precomputed, not `pt.newRows.length > 0` in the template: this DSL's {{ }} resolver
        // (support.js resolve()) only handles ==/===/!=/!== and dot-paths, no `>`/`<` at all --
        // an unsupported operator falls through to resolvePath(), hits the space before `>`,
        // and returns undefined (falsy) silently. The sc-if rendered null every time, no error.
        hasNewRows: (data.rankings || data.keywords || []).some(k => !k.measured),
        newRows: (data.rankings || data.keywords || []).filter(k => !k.measured).map(k => {
          const iLower = (k.intent || '').toLowerCase();
          return {
            kw: k.kw,
            volume: this.fmt(k.volume),
            kd: k.kd != null ? Math.round(k.kd) : '—',
            kdWidth: k.kd != null ? Math.min(100, Math.max(5, Math.round(k.kd))) + '%' : '0%',
            kdColor: k.kd != null ? (k.kd < 30 ? '#10b981' : (k.kd < 60 ? '#f59e0b' : '#ef4444')) : '#e2e8f0',
            cpc: k.cpc != null ? '$' + Number(k.cpc).toFixed(2) : '—',
            intent: k.intent || '—',
            intentStyle: { padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', background: iLower.includes('comm') ? '#d1fae5' : (iLower.includes('info') ? '#dbeafe' : (iLower.includes('trans') ? '#ffedd5' : '#f1f5f9')), color: iLower.includes('comm') ? '#047857' : (iLower.includes('info') ? '#1d4ed8' : (iLower.includes('trans') ? '#c2410c' : '#475569')) }
          };
        }),
        filteredRankings: (data.rankings || data.keywords || []).filter(k => {
          /* Measured, not ranked, is a row — with an em dash in Pos. Only the never-checked
             keywords are held back for the "Not Tracked Yet" card above. */
          if (!k.measured) return false;
          const st = s.ptRankingsSubTab || 'all';
          if (st === 'top10') return k.pos != null && k.pos <= 10;
          if (st === 'improved') return k.prevPos != null && k.pos != null && (k.prevPos - k.pos) >= 2;
          if (st === 'declined') return k.prevPos != null && k.pos != null && (k.prevPos - k.pos) <= -2;
          return true;
        }).map(k => {
          const d = k.prevPos != null && k.pos != null ? Math.round(k.prevPos - k.pos) : null;
          const posVal = k.pos != null ? Math.round(k.pos) : null;
          const iLower = (k.intent || '').toLowerCase();
          return {
            kw: k.kw,
            pos: posVal != null ? posVal : '—',
            posBadgeStyle: this.posBadge(posVal),
            deltaText: d != null ? (d > 0 ? '▲ +' + d : (d < 0 ? '▼ −' + Math.abs(d) : '—')) : (posVal != null ? 'NEW' : '—'),
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
        const allDomains = [vals.ptWs.domain].concat((data.competitors && data.competitors.domains) || []);
        const colors = ['#4f46e5', '#a855f7', '#f59e0b', '#ef4444', '#10b981', '#06b6d4'];
        
        /* VISIBILITY — two readings per domain, from ONE set of real inputs (the
           domain's actual SERP position on each tracked keyword; nothing estimated,
           a domain with no measurable keyword shows "—").

           1. SHARE OF VOICE (the big number, primary since 2026-08-05 at the product
              lead's direction): the domain's CTR-curve points as a % of all points
              earned by the domains shown, so the cards total 100% and read like the
              market-share panels users know from Semrush. An absolute index alone
              ("100 = #1 on everything") does not read as market share.
           2. VISIBILITY INDEX (the sub-line): the same points against a perfect board
              (#1 on every keyword = 100). Kept because a share hides absolute
              strength — a field of weak boards still splits 100% between them — and
              because a share necessarily moves when a competitor is added or removed,
              which the index does not.

           Position -> credit follows an organic click-through curve, so a position is
           worth what it is actually worth: #1 = 31.7 points, #2 = 24.7, #5 = 9.5,
           #10 = 1.8, past #20 almost nothing.

           Two earlier formulas were wrong here, both worth not repeating:
             1. `(100 - pos)/100` per domain — paid 55% credit for sitting at #45, so
                five domains totalled 264% and a domain nobody can find on Google looked
                healthy.
             2. The same curve weighted by SEARCH VOLUME — four keywords carry 81% of
                this project's volume, which inverted the ranking outright:
                atneventstaffing.com (avg position 7.7, the strongest board) scored 2.21
                while eventstaff.com (avg 18.7) scored 12.09, purely because of where the
                volume happened to sit.

           Hence EQUAL weight per keyword. Every tracked keyword is one the user chose to
           track, so each counts once and both readings measure ranking strength rather
           than traffic potential. A keyword a domain does not rank on scores 0 but still
           counts in the index denominator — that is what makes coverage matter, and it
           keeps the denominator identical for every domain, which is what makes the
           cards comparable at all.

           Self-contained (curve and credit live inside) so tests/visibility_scores.test.js
           can extract and run the real function by brace-matching, same as sortRows.
           `domains[0]` is "you" (read from r.you), the rest match inside r.comps. */
        const buildVisibilityScores = (domains, rows) => {
          const CTR_CURVE = [31.7, 24.7, 18.7, 13.3, 9.5, 6.8, 4.9, 3.5, 2.5, 1.8,
                             1.4, 1.2, 1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.45, 0.4];
          const PERFECT = CTR_CURVE[0];
          const posCredit = pos => {
            const p = Number(pos);
            if (!isFinite(p) || p < 1 || p > 100) return 0;
            /* Positions arrive as 1-dp averages (8.4, 24.5 — every service rounds to 1 dp),
               and an array will not interpolate: CTR_CURVE[8.4 - 1] is CTR_CURVE[7.4] =
               undefined, one undefined poisons the whole earned-points sum, and the card
               printed "index NaN". Round to the nearest whole position for the curve
               lookup — the curve is only defined at whole positions anyway. */
            const r = Math.round(p);
            return r <= 20 ? CTR_CURVE[r - 1] : (r <= 50 ? 0.05 : 0.02);
          };
          const perDomain = domains.map((dom, idx) => {
            let earned = 0;
            let posSum = 0;
            const ranked = [];
            rows.forEach(r => {
              let pos = null;
              if (idx === 0) {
                pos = r.you ? r.you.pos : null;
              } else {
                const compCell = (r.comps || []).find(c => c && c.domain === dom);
                pos = compCell ? compCell.pos : null;
              }
              if (pos != null) { ranked.push(pos); posSum += pos; }
              earned += posCredit(pos);
            });
            /* Having no captured rows at all is the only null. A domain that IS
               measured but ranks nowhere scores a real 0 — that is information, not a
               missing value. */
            const visScore = rows.length ? (earned / (rows.length * PERFECT)) * 100 : null;
            const avgPos = ranked.length ? Math.round(posSum / ranked.length) : null;
            return { dom: dom, earned: earned, visScore: visScore, avgPos: avgPos,
                     rankedCount: ranked.length, sov: null };
          });
          /* Share denominator = points earned by the domains SHOWN, so the set totals
             exactly 100. When nobody ranks anywhere there is no field to split — the
             share stays null while the index reports its honest 0. */
          const totalEarned = perDomain.reduce((t, d) => t + d.earned, 0);
          perDomain.forEach(d => {
            d.sov = (d.visScore != null && totalEarned > 0)
              ? (d.earned / totalEarned) * 100 : null;
          });
          return perDomain;
        };

        const compRows = (data.competitors && data.competitors.rows) || [];
        const scMap = buildVisibilityScores(allDomains, compRows).map((d, idx) => ({
          k: d.dom, name: d.dom, color: colors[idx % colors.length],
          val: d.sov != null ? d.sov.toFixed(1) + '%' : '—',
          /* Coverage, average position AND the absolute index printed under the share.
             The share alone cannot distinguish "ranks everywhere, mid-table" from
             "ranks on three keywords, all at #1", nor a strong field from a weak one —
             the sub-line is what makes the big number auditable instead of something
             the user has to trust. */
          sub: d.visScore == null ? ''
               : (d.rankedCount
                  ? 'index ' + d.visScore.toFixed(1) + ' · ' + d.rankedCount + '/' + compRows.length + ' keywords · avg #' + d.avgPos
                  : 'no positions on ' + compRows.length + ' keywords'),
          rawVal: d.sov != null ? d.sov : (d.visScore != null ? 0 : null)
        }));
        const hiddenOv = s.ptOvHidden || [];
        /* YOUR VISIBILITY IS THE SERVER'S NUMBER, NOT A SECOND OPINION.
           `data.kpis.visibility` is `_get_ranking_distribution`'s CTR-credit score over the
           requested window — the same field, from the same function, that the projects list
           renders in its Visibility column. It is shown here as its own labelled figure so the
           two screens cannot disagree.
           buildVisibilityScores above stays, but only as SHARE OF VOICE: it is computed from
           `competitors.rows`, a single latest capture date with integer-rounded positions and
           no reference to the range, and its whole point is the split BETWEEN domains. Two
           different questions now carry two different labels.
           null = nothing measured in this window -> em dash. 0 = measured, ranks nowhere. */
        const ownVis = (data.kpis && typeof data.kpis.visibility === 'number')
          ? data.kpis.visibility : null;
        vals.ptOv = {
          visLabel: ownVis == null ? '—' : parseFloat(ownVis.toFixed(1)) + '%',
          visStyle: {
            fontSize: '24px', fontWeight: 700,
            color: ownVis == null ? '#cbd5e1'
                   : (ownVis >= 30 ? '#059669' : ownVis >= 10 ? '#0891b2' : '#d97706')
          },
          visNote: ownVis == null
            ? 'No ranking measured in this window yet'
            : 'CTR-weighted across all ' + (data.kpis.tracked || 0) + ' tracked keywords',
          /* /api/positions returns no snapshot dates, so the Δ caption names the
             comparison instead of printing invented calendar dates ("Jun 20 → Jul 20"
             was hardcoded). Keys kept for when the API starts returning them. */
          prevDate: '', curDate: '',
          /* Sorted strongest-first so "who is winning" is the reading order of the row,
             not something the user has to work out by scanning five numbers. Domains with
             no measurable keyword sort last rather than to the top on a null. Your own
             domain is NOT pinned first — its rank among the competitors is the answer the
             user came for, and pinning it would hide a last place. */
          scoreCards: scMap.slice().sort((a, b) => (b.rawVal == null ? -1 : b.rawVal) - (a.rawVal == null ? -1 : a.rawVal)).map(item => {
            const off = hiddenOv.includes(item.k);
            return {
              name: item.name, valLabel: item.val, sub: item.sub,
              swatch: { width: '8px', height: '8px', borderRadius: '2px', background: item.color, display: 'inline-block' },
              subStyle: { fontSize: '11px', color: '#94a3b8', marginTop: '2px', whiteSpace: 'nowrap' },
              cardValStyle: { fontSize: '24px', fontWeight: 700, color: (off || item.rawVal == null) ? '#cbd5e1' : '#0f172a' },
              legendStyle: { display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: off ? '#94a3b8' : item.color, cursor: 'pointer', userSelect: 'none', fontWeight: 600 },
              checkStyle: { width: '14px', height: '14px', borderRadius: '3px', border: '1px solid ' + (off ? '#cbd5e1' : item.color), background: off ? 'white' : item.color, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontSize: '10px', fontWeight: 700 },
              check: off ? '' : '✓',
              onToggle: () => {
                const nh = off ? hiddenOv.filter(x => x !== item.k) : hiddenOv.concat([item.k]);
                this.setState({ ptOvHidden: nh });
              }
            };
          }),
          /* A trend line needs visibility HISTORY, and nothing in the pipeline stores a
             visibility snapshot per date — there is no table, no API field, no series.
             The old code manufactured six points per domain from a random number
             generator, which re-rolled on every render, so the "trend" visibly changed
             whenever the user touched anything. The chart now renders an honest empty
             state; the SVG and its geometry stay behind `hasHistory` so it lights up
             unchanged the day a real series exists. `xTicks` starts empty because the
             Feb–Jul month labels were invented too. */
          hasHistory: false,
          noHistory: true,
          emptyTitleStyle: { fontSize: '15px', fontWeight: 600, color: '#0f172a', marginBottom: '6px' },
          emptyBodyStyle: { fontSize: '13px', color: '#64748b', maxWidth: '420px', margin: '0 auto', lineHeight: 1.5 },
          chart: {
            viewBox: '0 0 720 210', lineX1: 50, lineX2: 700, labelX: 42, xLabelY: 200,
            grid: [{ y: 30, label: '80' }, { y: 68, label: '60' }, { y: 105, label: '40' }, { y: 143, label: '20' }, { y: 180, label: '0' }],
            xTicks: [],
            series: []
          },
          domains: allDomains.filter(d => !hiddenOv.includes(d)).map(d => ({ name: d, style: { textAlign: 'center', color: d === vals.ptWs.domain ? '#4338ca' : '#64748b', fontSize: '9.5px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' } })),
          gridCols: 'minmax(180px, 1.4fr) 90px 88px repeat(' + allDomains.filter(d => !hiddenOv.includes(d)).length + ', 1fr)',
          /* Same grid shape as `rows` below (Keyword/Volume/KD%/one column per domain), for
             keywords with no captured position anywhere yet -- source: none of them have a
             `you` cell, since `pt.compRows` already excludes exactly these. Rendered as its
             own card directly above Rankings Overview so a keyword just sent from the Keyword
             Explorer visibly moves DOWN into the real grid once "Track New Keywords" measures
             it, instead of appearing as an all-dash row mixed into the real data. */
          // Precomputed for the same reason as pt.hasNewRows above: this DSL's {{ }} resolver
          // has no `>`/`<` operator support, so `ptOv.newRows.length > 0` silently resolved to
          // undefined (falsy) and the card never rendered, with no console error either.
          hasNewRows: (data.rankings || data.keywords || []).some(k => !k.measured),
          newRows: (data.rankings || data.keywords || []).filter(k => !k.measured).map(k => ({
            kw: k.kw,
            volFmt: (k.volume === 0 || k.volume) ? this.fmt(k.volume) : '—',
            kd: k.kd != null ? Math.round(k.kd) : '—',
            kdStyle: { display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '5px', paddingLeft: '10px', fontSize: '13px', color: k.kd != null ? '#475569' : '#94a3b8' },
            hasKd: k.kd != null,
            kdDotStyle: { width: '8px', height: '8px', borderRadius: '50%', flexShrink: 0, background: k.kd != null ? (k.kd < 30 ? '#10b981' : (k.kd < 60 ? '#f59e0b' : '#ef4444')) : '#cbd5e1' },
            cells: allDomains.filter(d => !hiddenOv.includes(d)).map(() => ({
              pos: '—', diff: '', cellStyle: { textAlign: 'center', padding: '6px', borderRadius: '6px' },
              posStyle: { color: '#cbd5e1' }, diffStyle: {}
            }))
          })),
          rows: vals.pt.compRows.map(row => {
            const rInfo = (vals.pt.rankings || []).find(r => (r.kw || '').toLowerCase() === (row.kw || '').toLowerCase()) || {};
            return {
              kw: row.kw,
              /* `rInfo.volume || '0'` printed a literal 0 for every keyword whose volume is
                 simply not stored yet -- a keyword just sent from the Explorer has no
                 dataforseo_keywords row until the next volume sync. Zero searches a month and
                 "we have not looked it up yet" are different facts, and showing 0 for the
                 second is the fabrication this codebase forbids. Absent reads as an em dash. */
              volFmt: (rInfo.volume === 0 || rInfo.volume) ? rInfo.volume : '—',
              kd: rInfo.kd != null ? rInfo.kd : '—',
              /* Right-aligned to match the Volume column beside it. Left-aligned, the KD dot
                 butted straight against the right-aligned volume figure and the two columns
                 read as one run-together value ("0● —"). */
              kdStyle: { display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '5px', paddingLeft: '10px', fontSize: '13px', color: rInfo.kd != null ? '#475569' : '#94a3b8' },
              /* No dot when there is no score — a grey dot beside an em dash looked like a
                 real reading in a neutral band rather than an absent one. */
              hasKd: rInfo.kd != null,
              kdDotStyle: { width: '8px', height: '8px', borderRadius: '50%', flexShrink: 0, background: rInfo.kdColor || '#cbd5e1' },
              onSerp: () => vals.h.fetchLiveSerp(row.kw, vals.ptWs.location),
              cells: row.cells.filter((_, i) => !hiddenOv.includes(allDomains[i])).map(c => {
                const pos = c.text;
                return {
                  pos: pos, diff: c.diff || '', cellStyle: { textAlign: 'center', padding: '6px', borderRadius: '6px', cursor: 'pointer', transition: 'background 0.15s' },
                  posStyle: c.style, diffStyle: c.diffStyle || { fontSize: '11px', color: '#94a3b8', marginLeft: '4px' },
                  /* The ranking URL is whatever the SERP snapshot recorded. Synthesising
                     'https://<domain>/<keyword-slug>' when it is missing produced a link
                     to a page that does not exist — and offered to open it. */
                  /* `c.url` is this domain's ranking URL for this keyword. It was
                     `rInfo.url` -- your own row-level URL -- which is why clicking any
                     competitor's cell showed a premierstaff.com page. */
                  onCell: () => this.setState({ ptOvUrlPop: { open: true, url: c.url || '', kw: row.kw, domain: c.domain || '' } })
                };
              })
            };
          }),
          urlPopOpen: !!(s.ptOvUrlPop && s.ptOvUrlPop.open),
          urlPop: s.ptOvUrlPop && s.ptOvUrlPop.open ? {
            hasUrl: !!s.ptOvUrlPop.url,
            /* Naming the domain is not decoration. Every cell used to pop up YOUR url, so a
               popover that states whose page it is makes that class of mix-up visible. */
            who: s.ptOvUrlPop.domain
              ? (s.ptOvUrlPop.domain + ' — "' + (s.ptOvUrlPop.kw || '') + '"')
              : ('Your ranking URL — "' + (s.ptOvUrlPop.kw || '') + '"'),
            url: s.ptOvUrlPop.url || 'No ranking URL was recorded for this domain on this keyword in the latest SERP snapshot.',
            href: s.ptOvUrlPop.url || '',
            style: { position: 'fixed', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', zIndex: 90, background: 'white', borderRadius: '12px', padding: '20px', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04)', border: '1px solid #e2e8f0', width: '360px', maxWidth: '90vw' },
            onClose: () => this.setState({ ptOvUrlPop: null }),
            /* Was: writeText(...).catch(() => {}) followed by an unconditional "copied"
               toast — so a blocked or unavailable clipboard still claimed success and the
               user pasted whatever was there before. this.copyText is the existing helper:
               it falls back to a hidden textarea + execCommand and only then reports. */
            onCopy: () => { this.copyText(s.ptOvUrlPop.url, 'URL copied to clipboard'); this.setState({ ptOvUrlPop: null }); }
          } : {}
        };

        const openPages = s.ptOpenPages || [];
        /* Group by the REAL ranking URL only. The old code fell back to
           'https://<domain>/<keyword-slug>', which conjured up pages that do not exist
           on the site. A keyword whose snapshot carries no URL simply cannot be
           attributed to a page — it is counted out and the count is reported, so the
           gap is visible rather than papered over. */
        const pagesMap = {};
        let ptUnattributed = 0;
        (vals.pt.rankings || []).forEach(r => {
          const u = r.url || '';
          if (!u) { ptUnattributed += 1; return; }
          if (!pagesMap[u]) pagesMap[u] = { url: u, kws: [] };
          pagesMap[u].kws.push(r);
        });
        const pageList = Object.keys(pagesMap).map(u => pagesMap[u]);
        /* Fixed order so the intent bar's segments do not reshuffle between renders.
           Colours are the design-system intent accents (design.md §4). */
        const intentDefs = [
          ['info', '#3b82f6'], ['comm', '#10b981'], ['trans', '#f97316'],
          ['nav', '#a855f7'], ['', '#cbd5e1']
        ];
        const intentBucket = (key) => {
          for (let ii = 0; ii < intentDefs.length - 1; ii++) {
            if (key && key.indexOf(intentDefs[ii][0]) !== -1) return intentDefs[ii][0];
          }
          return '';
        };
        const arrowOf = (delta, size) => {
          /* Lower position number is better, so `delta` is prev − current. */
          if (delta > 0) return { text: '▲ ' + delta, style: { fontSize: size, color: '#059669', marginLeft: '4px' } };
          if (delta < 0) return { text: '▼ ' + Math.abs(delta), style: { fontSize: size, color: '#dc2626', marginLeft: '4px' } };
          return { text: '', style: {} };
        };
        vals.ptPages = {
          gridCols: 'minmax(240px, 2fr) 100px 120px 100px 100px 100px',
          noPages: pageList.length === 0,
          hasUnattributed: ptUnattributed > 0,
          unattributedNote: ptUnattributed === 1
            ? '1 tracked keyword has no ranking URL in the latest snapshot, so it is not attributed to a page below.'
            : ptUnattributed + ' tracked keywords have no ranking URL in the latest snapshot, so they are not attributed to a page below.',
          rows: pageList.map(p => {
            const isOpen = openPages.includes(p.url);
            /* Average over the keywords that actually rank. The old code substituted
               position 20 for every unranked keyword, inventing the average. */
            const ranked = p.kws.filter(k => k.posNum != null);
            const avgPos = ranked.length ? Math.round(ranked.reduce((acc, k) => acc + k.posNum, 0) / ranked.length) : null;
            /* Direction of travel IS real: average only over the keywords that have both
               a current and a previous position, so the two sides of the comparison
               cover the same keywords. No prior data → no arrow at all. */
            const bothPos = p.kws.filter(k => k.posNum != null && k.prevNum != null);
            let moved = 0;
            if (bothPos.length) {
              const curAvg = bothPos.reduce((acc, k) => acc + k.posNum, 0) / bothPos.length;
              const prevAvg = bothPos.reduce((acc, k) => acc + k.prevNum, 0) / bothPos.length;
              moved = Math.round((prevAvg - curAvg) * 10) / 10;
            }
            const pageArrow = arrowOf(moved, '11px');
            const totVol = p.kws.reduce((acc, k) => acc + k.volNum, 0);
            /* Est. traffic is now the real Search Console click count for this page's
               tracked keywords — the same definition the Landscape KPI already uses —
               instead of the `volume * 0.15` heuristic. */
            const clicks = p.kws.reduce((acc, k) => acc + k.clicksNum, 0);
            /* Intent mix built from the actual distribution of this page's keywords. */
            const counts = {};
            p.kws.forEach(k => { const b = intentBucket(k.intentKey); counts[b] = (counts[b] || 0) + 1; });
            const intentSegs = intentDefs
              .filter(def => counts[def[0]] > 0)
              .map(def => ({ style: { background: def[1], flex: counts[def[0]] } }));
            return {
              url: p.url.replace(/^https?:\/\/[^\/]+/, '') || '/', href: p.url,
              kwCount: p.kws.length,
              intentSegs: intentSegs,
              etVal: this.fmt(clicks),
              avgPos: avgPos != null ? avgPos : '—',
              posArrow: pageArrow.text, posArrowStyle: pageArrow.style,
              totVol: this.fmt(totVol), open: isOpen,
              chevStyle: { display: 'inline-block', width: '16px', fontWeight: 700, color: '#94a3b8', transform: isOpen ? 'rotate(90deg)' : 'none', transition: 'transform 0.15s' },
              onToggle: () => {
                const next = isOpen ? openPages.filter(u => u !== p.url) : openPages.concat([p.url]);
                this.setState({ ptOpenPages: next });
              },
              onLinkClick: (e) => e.stopPropagation(),
              kws: p.kws.map(k => {
                const kwArrow = arrowOf(k.posNum != null && k.prevNum != null ? k.prevNum - k.posNum : 0, '11px');
                return {
                  kw: k.kw,
                  hasIntent: !!(k.intent && k.intent !== '—'),
                  intentLabel: k.intent || '', intentStyle: k.intentStyle,
                  etVal: this.fmt(k.clicksNum),
                  pos: k.pos, posStyle: k.posBadgeStyle,
                  posArrow: kwArrow.text, posArrowStyle: kwArrow.style,
                  vol: k.volume
                };
              })
            };
          })
        };

        const ptSerpVals = this.serpDrawerVals(vals.ptWs.domain, vals.ptWs.location);
        vals.ptSerpOpen = ptSerpVals.open;
        vals.ptSerpCloseFn = ptSerpVals.closeFn;
        vals.ptSerp = ptSerpVals.serp;
      }

    }

