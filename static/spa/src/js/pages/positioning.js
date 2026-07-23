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

