    /* ============ DOMAIN OVERVIEW ============ */
    if (tab === 'domain_overview') {
      vals.showDomainOverview = true;

      const doSelSet = new Set(s.doSel || []);
      const doTrackedSet = new Set(s.doTracked || []);
      const doChk = on => ({ width: '15px', height: '15px', borderRadius: '4px', border: '1.5px solid ' + (on ? '#4f46e5' : '#cbd5e1'), background: on ? '#4f46e5' : 'white', display: 'flex', alignItems: 'center', justifyContent: 'center' });

      /* ---- destination picker ------------------------------------------------------
         Shown when the user sends keywords to Position Tracking and more than one project
         exists. The looked-up domain is usually a competitor's, so the right destination is
         often NOT the active project -- the picker makes that an explicit choice instead of
         a silent default. `pickCount` is stated in the confirm button so the user can see
         exactly how many keywords are about to move, and where. */
      const pickRows = s.doPickRows || [];
      const pickPid = s.doPickPid;
      const pickProjects = (s.projects || []).map(p => {
        const on = p.id === pickPid;
        return {
          name: p.name || p.domain,
          domain: p.domain,
          isActive: p.id === s.projectId,
          activeLabel: p.id === s.projectId ? 'Currently open' : '',
          kwLabel: (p.tracked_keywords_count || 0) + ' tracked',
          select: () => this.doPickSet(p.id),
          rowStyle: {
            display: 'flex', alignItems: 'center', gap: '10px', padding: '11px 14px',
            border: '1px solid ' + (on ? '#c7d2fe' : '#e2e8f0'),
            background: on ? '#f5f7ff' : 'white',
            borderRadius: '10px', cursor: 'pointer', marginBottom: '8px'
          },
          radioStyle: {
            width: '16px', height: '16px', borderRadius: '9999px', flexShrink: 0,
            border: '2px solid ' + (on ? '#4f46e5' : '#cbd5e1'),
            background: on ? '#4f46e5' : 'white',
            boxShadow: on ? 'inset 0 0 0 3px white' : 'none'
          },
          activeStyle: { fontSize: '10.5px', fontWeight: 600, color: '#4338ca', background: '#eef2ff', padding: '2px 7px', borderRadius: '9999px' }
        };
      });

      /* ---- market picker --------------------------------------------------------------
         Countries only — DataForSEO Labs cannot answer at any finer scope (see
         App#doCountryOptions). The current value is guaranteed to appear in the list even if
         it is a country the built-in set does not name, so the select can never render blank
         on a project configured for, say, Poland. */
      const doCurrentCountry = this.doLocation();
      const doCountries = this.doCountryOptions();
      const doLocOptions = (doCountries.indexOf(doCurrentCountry) === -1
        ? [doCurrentCountry].concat(doCountries)
        : doCountries).map(c => ({ value: c, label: c }));

      vals.do = {
        /* One of the three sanctioned live lookups: it calls DataForSEO because the user
           pressed a button, so there is no SyncLog row and no staleness to report. */
        src: this.srcLive('DataForSEO', 'domain lookup'),
        pickOpen: !!s.doPickOpen,
        pickProjects: pickProjects,
        pickCount: pickRows.length,
        pickTitle: 'Send ' + pickRows.length + ' keyword' + (pickRows.length === 1 ? '' : 's') + ' to Position Tracking',
        pickSubtitle: 'These came from a lookup of ' + (s.doQuery || 'another domain')
          + '. Choose which project should start tracking them.',
        pickConfirmLabel: 'Send to this project',
        pickDisabled: !pickPid,
        pickConfirmStyle: {
          display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '9px 18px',
          borderRadius: '8px', fontSize: '13px', fontWeight: 600, color: 'white',
          background: pickPid ? '#4f46e5' : '#c7d2fe',
          cursor: pickPid ? 'pointer' : 'default'
        },
        query: s.doQuery || '',
        data: s.doData || null,
        loading: s.doLoading || false,
        error: s.doError || null,
        /* The market this analysis is read in. Editable: it defaults to the project's own
           location but the user can inspect any URL in another market without leaving the
           page (see App#doLocation). */
        location: this.doLocation(),
        /* A real country, never a "same as project" placeholder — it starts on the active
           project's country and the user can switch it to any other. */
        locValue: doCurrentCountry,
        locOptions: doLocOptions,
        locChange: e => this.setState({ doLoc: e.target.value }, () => {
          /* Re-run only when a result is already on screen — changing the market on an empty
             page should not spend a DataForSEO call the user never asked for. */
          if (this.state.doData || this.state.doError) this.runDomainOverview();
        }),
        /* True when the project tracks a city but this page had to query its country,
           because DataForSEO Labs supports country locations only. Surfaced rather than
           hidden: these are national figures and the header must not imply otherwise. */
        locDowngraded: !!(s.doData && s.doData.location_downgraded),
        locDowngradeNote: (s.doData && s.doData.location_downgraded)
          ? 'Showing ' + s.doData.location + ' — DataForSEO’s domain database is country-level, '
            + 'so ' + s.doData.requested_location + ' was read at country scope. '
            + 'Position Tracking still measures the exact city.'
          : '',
        rows: [],
        hasRows: false,
        noRows: false,
        anySelected: false,
        noneSelected: true,
        selectedCount: 0,
        allChecked: false,
        allCheckStyle: doChk(false),
        toolbarBg: '#f8fafc',
        rowsMeta: '',
        trackSelLabel: 'Track selected'
      };

      /* ---- backlinks / anchors / spam score -------------------------------------------
         A SECOND, deliberate press. The default Analyze buys one DataForSEO Labs call; this
         buys three Backlinks API calls (summary + 100 backlinks + 60 anchors), so it has its
         own button and its own 24h cache. That cache is keyed by DOMAIN ONLY -- the Backlinks
         API has no location parameter at all -- which is why the card says out loud that the
         market selector above does not apply to it.

         Computed outside the `status === 'ok'` branch: the backlink sections are their own
         fetch with their own lifecycle, and a keywords lookup that errored must not take the
         backlink card's state down with it. */
      const blSt = (s.doBl && s.doBl.target === (s.doQuery || '').trim()) ? s.doBl : {};
      const bl = blSt.data || null;
      const blBand = {
        low:     { fg: '#059669', bg: '#ecfdf5', bd: '#a7f3d0', label: 'Low' },
        medium:  { fg: '#b45309', bg: '#fffbeb', bd: '#fde68a', label: 'Medium' },
        high:    { fg: '#dc2626', bg: '#fef2f2', bd: '#fecaca', label: 'High' },
        unknown: { fg: '#64748b', bg: '#f8fafc', bd: '#e2e8f0', label: 'Not scored' }
      };
      const blPill = band => {
        const t = blBand[band] || blBand.unknown;
        return { display: 'inline-flex', alignItems: 'center', gap: '5px', padding: '3px 9px',
                 fontSize: '11.5px', fontWeight: 600, color: t.fg, background: t.bg,
                 border: '1px solid ' + t.bd, borderRadius: '9999px', whiteSpace: 'nowrap' };
      };

      vals.do.bl = {
        /* Four honest states, plus "never pressed". `state` comes from the server:
           ok · empty (DataForSEO indexes no backlinks) · setup (no credentials) ·
           budget (the monthly cap refused the spend) · error. */
        loaded: !!bl,
        showLinks: !!(bl && bl.state === 'ok'),
        loading: !!blSt.loading,
        error: blSt.error || null,
        /* The label tells the user what the NEXT press costs. Once loaded, a press inside
           24h is served from cache and free; after that it bills again. */
        btnLabel: blSt.loading ? 'Loading backlinks…' : (bl ? 'Loaded · refresh' : 'Load backlinks'),
        btnStyle: {
          display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '9px 16px',
          fontSize: '13px', fontWeight: 600, borderRadius: '8px',
          color: bl ? '#334155' : 'white', background: bl ? '#f1f5f9' : '#0f172a',
          border: '1px solid ' + (bl ? '#e2e8f0' : '#0f172a'),
          cursor: blSt.loading ? 'default' : 'pointer', opacity: blSt.loading ? 0.7 : 1
        },
        load: () => {
          const q = (this.state.doQuery || '').trim();
          if (!q || (this.state.doBl && this.state.doBl.loading)) return;
          this.setState({ doBl: { target: q, loading: true, data: null, error: null } });
          window.FuseAPI.post('/api/domain-overview', {
            target: q, location: this.doLocation(), project: this.state.projectId,
            include: ['backlinks']
          })
            .then(r => {
              if (!this._alive) return;
              const b = r && r.backlinks;
              this.setState({ doBl: { target: q, loading: false, data: b || null,
                                      error: (b && b.state === 'error') ? b.note : (r && r.error) || null } });
            })
            .catch(e => {
              if (!this._alive) return;
              this.setState({ doBl: { target: q, loading: false, data: null,
                                      error: 'Failed to load backlinks: ' + e } });
            });
        },
        /* Non-ok states render their own message rather than an empty card. A hidden
           section is indistinguishable from a section with nothing in it. */
        showNote: !!(bl && bl.state !== 'ok'),
        note: (bl && bl.note) || '',
        isEmpty: !!(bl && bl.state === 'empty'),
        target: (bl && bl.target) || '',
        summary: {
          backlinks: bl && bl.summary ? this.fmt(bl.summary.backlinks || 0) : '—',
          refDomains: bl && bl.summary ? this.fmt(bl.summary.refDomains || 0) : '—',
          dofollowPct: bl && bl.summary ? (bl.summary.dofollowPct || 0) + '%' : '—',
          authority: bl && bl.summary ? String(bl.summary.authorityScore || 0) : '—'
        },
        /* SPAM SCORE. Costs zero extra API calls: `backlink_spam_score` already rides on
           every row of the backlinks call and `backlinks_spam_score` on the summary --
           both were being paid for and neither was ever read. */
        spam: (() => {
          const sp = (bl && bl.spam) || {};
          const known = sp.targetScore !== null && sp.targetScore !== undefined;
          const band = known ? (sp.targetScore <= 30 ? 'low' : (sp.targetScore <= 60 ? 'medium' : 'high')) : 'unknown';
          const t = blBand[band];
          return {
            /* An em dash, never a 0: an unreported score is not a clean profile. */
            scoreText: known ? String(sp.targetScore) : '—',
            scoreStyle: { fontSize: '30px', fontWeight: 700, color: t.fg },
            bandLabel: t.label,
            bandStyle: blPill(band),
            high: sp.highSpamLinks || 0,
            medium: sp.mediumSpamLinks || 0,
            scored: sp.scoredLinks || 0,
            unknown: sp.unknownLinks || 0,
            /* Says exactly which population each number is about. The target score is
               profile-wide; the counts are over the sampled links only. */
            sampleNote: 'Counted across the ' + (sp.scoredLinks || 0) + ' scored link'
              + ((sp.scoredLinks === 1) ? '' : 's') + ' in the sample below'
              + ((sp.unknownLinks || 0) ? ' · ' + sp.unknownLinks + ' not scored by DataForSEO' : '')
          };
        })(),
        anchors: ((bl && bl.anchors) || []).map(a => ({
          anchor: a.anchor,
          type: a.type,
          typeStyle: { fontSize: '11px', fontWeight: 600, color: '#475569',
                       background: '#f1f5f9', padding: '2px 8px', borderRadius: '9999px' },
          backlinks: this.fmt(a.backlinks || 0),
          refDomains: this.fmt(a.refDomains || 0),
          dofollowPct: (a.dofollowPct || 0) + '%'
        })),
        noAnchors: !((bl && bl.anchors) || []).length,
        links: ((bl && bl.links) || []).map(l => ({
          urlFrom: l.urlFrom || l.referringDomain,
          referringDomain: l.referringDomain,
          anchor: l.anchor || '(empty)',
          /* domainRank/pageRank are passed through as returned; null renders as an em
             dash rather than a fabricated 0. */
          domainRank: (l.domainRank === null || l.domainRank === undefined) ? '—' : String(l.domainRank),
          follow: l.dofollow ? 'dofollow' : 'nofollow',
          followStyle: { fontSize: '11px', fontWeight: 600,
                         color: l.dofollow ? '#059669' : '#64748b',
                         background: l.dofollow ? '#ecfdf5' : '#f1f5f9',
                         padding: '2px 8px', borderRadius: '9999px' },
          spamText: (l.spamScore === null || l.spamScore === undefined) ? '—' : String(l.spamScore),
          spamStyle: blPill(l.spamBand)
        })),
        countLabel: bl && bl.links
          ? this.fmt(bl.links.length) + ' of the highest-authority backlinks · limit ' + (bl.limit || 100)
          : '',
        cachedLabel: (bl && bl.cached) ? 'Served from the 24-hour cache — this press cost nothing' : ''
      };

      /* Same shared drawer Position Tracking uses (see App#serpDrawerVals) -- "you" here
         is the domain currently being looked up, since that's usually what a Domain
         Overview visitor wants highlighted in the live SERP, not the active project. */
      const doSerpVals = this.serpDrawerVals(this._normalizeDomain(s.doQuery), vals.do.location);
      vals.ptSerpOpen = doSerpVals.open;
      vals.ptSerpCloseFn = doSerpVals.closeFn;
      vals.ptSerp = doSerpVals.serp;

      if (s.doData && s.doData.status === 'ok') {
        const metrics = s.doData.metrics || {};
        vals.do.metrics = {
          organicTraffic: this.fmt(metrics.organic_traffic || 0),
          trafficValue: this.money(metrics.traffic_value || 0),
          rankedKeywords: this.fmt(metrics.ranked_keywords || 0)
        };

        vals.do.rows = (s.doData.keywords || []).map(k => {
          const iv = this.intentView(k.intent);
          const on = doSelSet.has(k.keyword);
          /* shape sendKwsToTracking expects; `kd` is absent because the ranked-keywords
             response carries no keyword-difficulty figure — we do not invent one */
          const trackRow = { kw: k.keyword, volume: k.volume, cpc: k.cpc, intent: k.intent };
          /* Two sources, both real: `k.tracked` comes from the API, which now joins the
             returned keywords against this project's SavedKeyword rows, so keywords tracked
             in an earlier session are recognised. doTrackedSet covers rows sent during THIS
             render pass, before the next fetch has echoed them back. */
          const tracked = k.tracked === true || doTrackedSet.has(this.doTrackKey(s.projectId, k.keyword));
          /* A keyword can now be sent to a project OTHER than the one currently open, so
             "tracked" and "tracked HERE" are different facts. Without this, sending to
             another project left the row still showing "+ Track" right after a success
             toast, which reads as a failure. `sentElsewhere` names the destination instead. */
          var SEP = String.fromCharCode(0);   /* doTrackKey joins pid + NUL + keyword */
          const elsewhereKey = tracked ? null : (s.doTracked || []).filter(function (key) {
            return key.slice(key.indexOf(SEP) + 1) === k.keyword;
          })[0];
          const elsewherePid = elsewhereKey ? elsewhereKey.slice(0, elsewhereKey.indexOf(SEP)) : null;
          const elsewhereProj = elsewherePid
            ? (s.projects || []).filter(function (p) { return p.id === elsewherePid; })[0]
            : null;
          return {
            kw: k.keyword,
            url: k.url,
            intentLabel: iv.label,
            intentStyle: iv.style,
            posText: k.position,
            posStyle: this.posBadge(k.position),
            volFmt: this.fmt(k.volume),
            cpcFmt: this.money(k.cpc),
            trafficFmt: this.fmt(k.traffic),
            checked: on,
            rowBg: on ? '#f5f7ff' : 'white',
            checkStyle: doChk(on),
            onToggle: () => vals.h.doToggleRow(k.keyword),
            tracked: tracked,
            /* Three states, not two: tracked here · sent to another project this session ·
               not tracked anywhere. Only the last one still offers the Track button. */
            sentElsewhere: !tracked && !!elsewhereProj,
            elsewhereLabel: elsewhereProj ? ('Tracked in ' + (elsewhereProj.name || elsewhereProj.domain)) : '',
            elsewhereStyle: { fontSize: '10.5px', fontWeight: 600, color: '#0369a1', background: '#e0f2fe', padding: '3px 8px', borderRadius: '9999px', whiteSpace: 'nowrap' },
            notTracked: !tracked && !elsewhereProj,
            onTrack: () => this.trackDomainOverviewKws([trackRow]),
            onSerp: () => vals.h.fetchLiveSerp(k.keyword, vals.do.location)
          };
        });

        const visKws = vals.do.rows.map(r => r.kw);
        const selCount = visKws.filter(kw => doSelSet.has(kw)).length;
        const allOn = visKws.length > 0 && visKws.every(kw => doSelSet.has(kw));
        vals.do.hasRows = visKws.length > 0;
        vals.do.noRows = visKws.length === 0;
        vals.do.selectedCount = selCount;
        vals.do.anySelected = selCount > 0;
        vals.do.noneSelected = selCount === 0;
        vals.do.allChecked = allOn;
        vals.do.allCheckStyle = doChk(allOn);
        vals.do.toolbarBg = selCount > 0 ? '#f5f7ff' : '#f8fafc';
        vals.do.rowsMeta = this.fmt(visKws.length) + ' keywords · ' + vals.do.location;
        vals.do.trackSelLabel = 'Track selected (' + selCount + ')';
      }
    }
