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

      /* ---- PDF report -----------------------------------------------------------------
         The existing `downloadCsv` helper builds a Blob from a string it was handed; this
         needs the OPPOSITE shape -- a Blob that comes back from the server -- so the
         download half lives here rather than in app.js. Same createObjectURL / a.download /
         revokeObjectURL dance, different source.

         window.FuseAPI.post parses JSON, which would corrupt PDF bytes, so this is a raw
         fetch carrying the same Bearer token the transport uses. Generation takes seconds
         (the server renders the whole document), hence the explicit spinner state.

         Cost: this reads the same 24-hour caches the page fills. Straight after a lookup it
         is free; it NEVER buys backlinks; and if even the keyword cache has expired it makes
         the one Labs call Analyze would have made and says so in the PDF. */
      const downloadBlob = (name, blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = name;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      };

      vals.do.pdf = {
        busy: !!s.doPdfBusy,
        label: s.doPdfBusy ? 'Preparing PDF…' : 'Download PDF',
        error: s.doPdfError || null,
        /* Only offered once there is something to report on. A report of nothing is not a
           useful artefact, and generating one could cost a Labs call. */
        show: !!(s.doData && s.doData.status === 'ok'),
        style: {
          display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '9px 16px',
          fontSize: '13px', fontWeight: 600, borderRadius: '8px', color: '#334155',
          background: 'white', border: '1px solid #e2e8f0',
          cursor: s.doPdfBusy ? 'default' : 'pointer', opacity: s.doPdfBusy ? 0.6 : 1
        },
        run: () => {
          const q = (this.state.doQuery || '').trim();
          if (!q || this.state.doPdfBusy) return;
          this.setState({ doPdfBusy: true, doPdfError: null });
          const cfg = (window.FuseAPI && window.FuseAPI.config) || {};
          const headers = { 'Content-Type': 'application/json' };
          if (cfg.authToken) headers['Authorization'] = 'Bearer ' + cfg.authToken;
          fetch(String(cfg.baseUrl || '/').replace(/\/$/, '') + '/api/domain-overview/report', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({ target: q, location: this.doLocation(), project: this.state.projectId })
          })
            .then(r => {
              /* A 501 (no PDF engine on this server) and a 400 both answer JSON, not a PDF.
                 Reading the body as a blob regardless would download a file containing an
                 error message, which is worse than saying what went wrong. */
              if (!r.ok) {
                return r.json().catch(() => ({}))
                  .then(j => { throw new Error(j.detail || ('Report failed (' + r.status + ')')); });
              }
              const cd = r.headers.get('Content-Disposition') || '';
              const match = /filename="([^"]+)"/.exec(cd);
              const name = match ? match[1] : 'domain-overview.pdf';
              return r.blob().then(b => ({ name: name, blob: b }));
            })
            .then(out => {
              if (!this._alive) return;
              downloadBlob(out.name, out.blob);
              this.setState({ doPdfBusy: false });
            })
            .catch(e => {
              if (!this._alive) return;
              this.setState({ doPdfBusy: false, doPdfError: String(e.message || e) });
            });
        }
      };

      /* ---- backlinks / anchors / spam score -------------------------------------------
         A SECOND, deliberate press. The default Analyze buys one DataForSEO Labs call; this
         buys three Backlinks API calls (summary + 100 backlinks + 60 anchors), so it has its
         own button and its own 24h cache. That cache is keyed by DOMAIN ONLY -- the Backlinks
         API has no location parameter at all -- which is why the card says out loud that the
         market selector above does not apply to it.

         Computed outside the `status === 'ok'` branch: the backlink sections are their own
         fetch with their own lifecycle, and a keywords lookup that errored must not take the
         backlink card's state down with it.

         TWO sources, in priority order. `doBl` is this session's fetch. Behind it sits the
         localStorage copy (App#doBlCache*), which is what makes a restored search -- or a
         reload, or a server restart -- show the links that were already paid for instead of
         asking to buy them again. The saved copy is never passed off as a fresh one: the
         button says "Saved 3h ago · refresh" and the card repeats it, so the user can still
         see exactly what has been bought and what the next press would cost. */
      const blSt = (s.doBl && s.doBl.target === (s.doQuery || '').trim()) ? s.doBl : {};
      const blCached = blSt.data ? null : this.doBlCacheGet(s.doQuery);
      const bl = blSt.data || (blCached && blCached.data) || null;
      const blCacheAge = blCached ? this.relTime(new Date(blCached.ts).toISOString()) : '';
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
        /* The label tells the user what the NEXT press costs, and never hides where what is
           on screen came from. Three readings: nothing bought yet · bought this session ·
           restored from a saved copy, with its age. The third is the one that has to stay
           explicit -- a saved copy rendered under a plain "Loaded" would be indistinguishable
           from a fresh measurement. */
        btnLabel: blSt.loading
          ? 'Loading backlinks…'
          : (blCached ? 'Saved ' + blCacheAge + ' · refresh' : (bl ? 'Loaded · refresh' : 'Load backlinks')),
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
              /* Save before the render so a reload, a restored search, or a server restart
                 finds these three calls already bought. doBlCachePut ignores anything that
                 is not a real answer. */
              this.doBlCachePut(q, b);
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
        /* Which of the three free routes produced this, in the order they are checked. The
           browser copy is named separately from the server's because only one of them
           survives a restart, and the user is entitled to know which one they are relying
           on before they navigate away. */
        cachedLabel: blCached
          ? 'Saved on this browser ' + blCacheAge + ' — restored for free. Press refresh to re-buy it.'
          : ((bl && bl.cached) ? 'Served from the 24-hour cache — this press cost nothing' : '')
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

        /* ---- shared cell renderers -------------------------------------------------
           Each one exists to keep an honest null from being made friendly on the way to the
           screen: a 0 where we mean "unknown" reads as a measurement, and this page's whole
           job is to be trustworthy about what was actually looked up. */

        // Keyword difficulty. `null` is a dash in the neutral grey, NOT a green 0 — green on
        // an unknown reads as "trivial to rank for", the opposite of what we know.
        const kdView = (kd) => {
          if (kd === null || kd === undefined || kd === '') {
            return { label: '—', color: '#94a3b8', band: 'unknown', known: false };
          }
          const n = Number(kd);
          const band = n <= 20 ? 'easy' : n <= 45 ? 'medium' : n <= 70 ? 'hard' : 'very hard';
          const color = n <= 20 ? '#047857' : n <= 45 ? '#b45309' : n <= 70 ? '#c2410c' : '#b91c1c';
          return { label: String(n), color: color, band: band, known: true };
        };

        // Rank movement. Unknown renders NOTHING — "flat" would assert we compared two
        // captures when there may only ever have been one.
        const moveView = (mv) => {
          const map = { up: ['▲', '#047857'], down: ['▼', '#b91c1c'],
                        'new': ['new', '#4338ca'], lost: ['lost', '#b91c1c'] };
          const hit = map[mv];
          if (!hit) return { show: false, label: '', color: '' };
          return { show: true, label: hit[0], color: hit[1] };
        };

        /* 12-month sparkline. The x divisor is (len - 1), which is ZERO for a single month:
           0/0 is NaN and an SVG polyline carrying NaN draws nothing at all. The AI mentions
           trend shipped with exactly that bug — one point, empty chart, no explanation. */
        const sparkPoints = (series) => {
          const vals2 = (series || []).map(v => Number(v) || 0);
          if (!vals2.length) return '';
          const max = Math.max.apply(null, vals2) || 1;
          const w = 68, h = 18;
          if (vals2.length === 1) return (w / 2).toFixed(1) + ',' + (h - (vals2[0] / max) * h).toFixed(1);
          return vals2.map((v, k) =>
            ((k / (vals2.length - 1)) * w).toFixed(1) + ',' + (h - (v / max) * h).toFixed(1)
          ).join(' ');
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
            /* All four arrive in the SAME billed response the seven fields above come from —
               they were parsed and thrown away until 2026-08-11. */
            kd: kdView(k.kd),
            move: moveView(k.movement),
            spark: sparkPoints(k.monthly),
            hasSpark: !!(k.monthly && k.monthly.length),
            snippet: !!k.featuredSnippet,
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

      /* ---- result tabs ----------------------------------------------------------------
         One lookup's results, split three ways. Everything ABOVE the tabs (search box,
         market picker, Download PDF) stays shared, because it applies to all three.

         Counts are appended only where a count is a measured fact. Backlinks show none
         until they have actually been loaded: a "0" beside a section that has never been
         fetched asserts a measurement nobody paid for -- and here it would assert the
         opposite of the truth, since the whole point of that tab is that it holds data
         until you ask for it. */
      /* ---- AI Questions -------------------------------------------------------------
         Which questions does this URL turn up in when somebody asks an answer engine.

         `cited` and `seen` never collapse into one badge. Cited means the engine QUOTED the
         page in its reply; seen means it retrieved the page and quoted somebody else — and
         the second one is the actionable half, because it says the page is findable but not
         convincing. On the live account 116 rows were cited and 46 seen-only. */
      const questionRows = (rows) => {
       return (rows || []).map((r) => {
        const cited = !!r.cited;
        const months = r.monthly_searches || {};
        // Object key order is insertion order, which the API returns newest-first; a chart
        // reads left to right, so sort by the YYYY-MM key and drop it.
        const monthly = Object.keys(months).sort().map(k => Number(months[k]) || 0);
        const others = (r.cited_domains || []).filter(d => d && d !== (r.our_domain || ''));
        return {
          question: r.question || '',
          // None, not 0: "we were not told how often this is asked" is not "nobody asks it".
          volume: (r.ai_search_volume === null || r.ai_search_volume === undefined)
            ? '—' : this.fmt(r.ai_search_volume),
          badge: cited
            ? { label: 'Cited', color: '#047857', bg: '#d1fae5',
                title: 'The answer engine quoted this page in its reply.' }
            : { label: 'Seen', color: '#b45309', bg: '#fef3c7',
                title: 'The engine retrieved this page but quoted someone else — findable, not yet convincing.' },
          url: r.our_url || '',
          urlShort: (r.our_url || '').replace(/^https?:\/\//, '').slice(0, 60),
          platform: r.platform === 'google' ? 'AI Overviews' : 'ChatGPT',
          monthly: monthly,
          spark: monthly.length ? monthly : null,
          answer: r.answer || '',
          hasAnswer: !!(r.answer || '').trim(),
          fanOut: (r.fan_out_queries || []).join(' · '),
          hasFanOut: !!(r.fan_out_queries || []).length,
          // Who won the citation when we did not. Blank when we were the cited one.
          citedInstead: cited ? '' : (others[0] || ''),
        };
       });
      };

      const q = (s.doData && s.doData.questions) || null;
      vals.do.q = {
        loaded: !!(q && q.state === 'ok'),
        state: q ? q.state : 'idle',
        rows: q ? questionRows(q.rows) : [],
        total: q ? (q.total || 0) : 0,
        citedCount: q ? (q.citedCount || 0) : 0,
        seenCount: q ? (q.seenCount || 0) : 0,
        note: q ? (q.note || '') : '',
        // "as of" is shown whenever the answer came from the store rather than the wire, so a
        // month-old lookup is never presented as live.
        storedAt: (q && q.storedAt) ? String(q.storedAt).slice(0, 10) : '',
        fromStore: !!(q && q.fromStore),
        ageDays: (q && q.ageDays !== undefined) ? q.ageDays : null,
        /* Which engines to ask, chosen BEFORE the press. Each is a separate request with its
           own $0.10 base fee, so the price moves with the choice and the label says so
           rather than quoting one number for two different purchases. */
        engines: (s.doQPlat && s.doQPlat.length) ? s.doQPlat : ['chat_gpt'],
        engineOpts: [
          { id: 'chat_gpt', name: 'ChatGPT' },
          { id: 'google', name: 'Google AI Overviews' },
        ].map(function (e) {
          var on = ((s.doQPlat && s.doQPlat.length) ? s.doQPlat : ['chat_gpt']).indexOf(e.id) >= 0;
          return {
            name: e.name,
            checked: on,
            style: { display: 'inline-flex', alignItems: 'center', gap: '7px', padding: '6px 12px',
                     fontSize: '12.5px', fontWeight: on ? 600 : 500, cursor: 'pointer',
                     borderRadius: '999px', border: '1px solid ' + (on ? '#c7d2fe' : '#e2e8f0'),
                     background: on ? '#eef2ff' : 'white', color: on ? '#4338ca' : '#64748b' },
            boxStyle: { width: '14px', height: '14px', borderRadius: '3px', flexShrink: 0,
                        border: '1.5px solid ' + (on ? '#4f46e5' : '#cbd5e1'),
                        background: on ? '#4f46e5' : 'white' },
            toggle: () => this.doToggleQEngine(e.id),
          };
        }, this),
        // Stated before the click, like every other paid button on this page.
        loadLabel: s.doQLoading ? 'Finding questions…'
          : ('Find AI questions · ~$'
             + (0.20 * (((s.doQPlat && s.doQPlat.length) || 1))).toFixed(2)),
        load: () => this.doLoadQuestions(false),
        refresh: () => this.doLoadQuestions(true),
        busy: !!s.doQLoading,

        /* `sc-if` has no negate form — walkIf reads `value` alone — so the empty panel gets
           its own flag rather than a negated one, which would render always. */
        showEmpty: !(q && q.state === 'ok'),
        emptyTitle: !q ? 'Not looked up yet'
          : q.state === 'empty' ? 'No AI answers reference this URL'
          : q.state === 'budget' ? 'Monthly DataForSEO budget reached'
          : q.state === 'setup' ? 'DataForSEO is not configured'
          : q.state === 'not_loaded' ? 'Not loaded for this report'
          : 'Could not load AI questions',
        /* The service already distinguishes "this PAGE is not referenced, though the domain
           has N" from "nothing here is referenced" — two different findings, and the first
           one is the useful one. That sentence is passed straight through. */
        emptyNote: (q && q.note) ? q.note
          : 'One call asks DataForSEO which questions this domain turns up in when people ask '
            + 'ChatGPT. The answer is kept, so every page on this domain is free afterwards.',
      };

      const doTab = s.doTab || 'overview';
      const doTabBase = { padding: '7px 13px', fontSize: '13px', borderRadius: '8px', cursor: 'pointer',
                          border: '1px solid transparent', color: '#64748b', fontWeight: 500,
                          display: 'inline-flex', alignItems: 'center', gap: '7px' };
      const doTabOn = { padding: '7px 13px', fontSize: '13px', borderRadius: '8px', cursor: 'pointer',
                        border: '1px solid #c7d2fe', background: '#eef2ff', color: '#4338ca', fontWeight: 600,
                        display: 'inline-flex', alignItems: 'center', gap: '7px' };
      const blRefDomains = (bl && bl.state === 'ok' && bl.summary) ? bl.summary.refDomains : null;
      const doTabDefs = [
        ['overview', 'Overview', ''],
        ['keywords', 'Keywords', vals.do.hasRows ? this.fmt(vals.do.rows.length) : ''],
        ['backlinks', 'Backlinks',
         (blRefDomains === null || blRefDomains === undefined) ? '' : this.fmt(blRefDomains)],
        ['questions', 'AI Questions', vals.do.q.loaded ? this.fmt(vals.do.q.total) : '']
      ];
      vals.do.tabs = doTabDefs.map(d => ({
        label: d[1],
        count: d[2],
        hasCount: !!d[2],
        countStyle: { fontSize: '11px', fontWeight: 600, padding: '1px 6px', borderRadius: '9999px',
                      color: doTab === d[0] ? '#4338ca' : '#64748b',
                      background: doTab === d[0] ? '#e0e7ff' : '#f1f5f9' },
        onClick: () => vals.h.doSetTab(d[0]),
        style: doTab === d[0] ? doTabOn : doTabBase
      }));
      vals.do.showOverviewTab = doTab === 'overview';
      vals.do.showKeywordsTab = doTab === 'keywords';
      vals.do.showBacklinksTab = doTab === 'backlinks';
      vals.do.showQuestionsTab = doTab === 'questions';

      /* The Overview tab's backlink strip. Rendered ONLY from data that is already in hand
         -- it never triggers the three-call fetch, which stays behind the button on the
         Backlinks tab. When nothing has been loaded the strip is absent and a line points
         at the tab that can load it, rather than showing four em dashes that look like a
         domain with no backlinks. */
      vals.do.showBlSummaryOnOverview = !!(bl && bl.state === 'ok');
      vals.do.blSummaryHint = (bl && bl.state === 'ok')
        ? '' : 'Backlink metrics are on the Backlinks tab — they are a separate, paid lookup.';

      /* ---- recent searches (localStorage, per project) --------------------------------
         The chip states its own age and, crucially, whether clicking it will SPEND. Within
         24h the stored payload renders directly and costs nothing; past that the entry is
         stale and the chip re-runs the billed lookup. Saying which before the click is the
         whole contract -- see App#doHistOpen. */
      /* The server's list wins when it has one. localStorage held each entry's FULL payload,
         so the quota filled, doHistSave shed entries to recover, and a URL analysed a minute
         earlier could be missing from Recent after a refresh — silently, and starting with
         whichever lookups had the most data behind them. The database keeps the payload once
         and the list beside it. localStorage stays as the fallback for the moment before the
         first response lands, and because its entries carry the replayable payload. */
      const doServerHist = (s.doData && s.doData.recent) || [];
      const doLocalHist = this.doHistLoad(s.projectId);
      const doLocalById = {};
      doLocalHist.forEach(function (h) { if (h && h.id) doLocalById[h.id] = h; });
      const doHist = doServerHist.length
        ? doServerHist.map(function (r) {
            // Match the stored entry so a chip can still replay its payload for free.
            const id = this.doHistId(r.target, r.location);
            const local = doLocalById[id];
            // `stored` marks an entry the SERVER holds. Those are free to open at any age —
            // the lookup is read back out of domain_lookups — unlike the browser copy, which
            // expires after 24h and then costs a real call.
            return Object.assign({ id: id, query: r.target, location: r.location, data: null,
                                   ts: r.storedAt ? Date.parse(r.storedAt) : 0 },
                                 local || {}, { stored: true });
          }, this)
        : doLocalHist;
      const doNow = Date.now();
      vals.do.histItems = doHist.map(hEntry => {
        /* Free means "we already own this answer", which is now true at ANY age for a lookup
           the server stored — it is read back out of domain_lookups. Only a browser-only
           entry still expires, because only its copy does. */
        const fresh = hEntry.stored || (doNow - (hEntry.ts || 0)) < this.DO_HIST_TTL;
        const age = this.relTime(new Date(hEntry.ts || 0).toISOString());
        return {
          label: hEntry.query.length > 30 ? hEntry.query.slice(0, 28) + '…' : hEntry.query,
          title: hEntry.query + ' · ' + hEntry.location + ' · looked up ' + age
            + (fresh
               ? (hEntry.stored ? ' · saved, so opening it costs nothing'
                                : ' · saved on this browser, so opening it costs nothing')
               : ' · older than 24h, so opening it runs a new DataForSEO lookup'),
          age: age,
          fresh: fresh,
          stale: !fresh,
          onClick: () => this.doHistOpen(hEntry),
          style: {
            display: 'inline-flex', alignItems: 'center', gap: '7px', padding: '5px 11px',
            fontSize: '12px', borderRadius: '9999px', cursor: 'pointer',
            color: fresh ? '#334155' : '#64748b',
            background: fresh ? '#f8fafc' : 'white',
            border: '1px solid ' + (fresh ? '#e2e8f0' : '#e2e8f0')
          },
          ageStyle: { fontSize: '10.5px', color: fresh ? '#059669' : '#94a3b8', fontWeight: 600 }
        };
      });
      vals.do.histHasItems = doHist.length > 0;

      /* Says out loud that what is on screen is a replay, and how old. Without it a restored
         capture is indistinguishable from a fresh measurement -- and its Tracked marks are
         as of the capture, which is exactly the kind of quietly-stale number this codebase
         keeps getting bitten by. */
      vals.do.fromHist = !!s.doFromHist;
      vals.do.fromHistNote = s.doFromHist
        ? 'Saved result from ' + this.relTime(new Date(s.doFromHist).toISOString())
          + ' — restored from this browser, so it cost nothing. Tracked marks are as they were '
          + 'when it was captured. Press Analyze for a fresh lookup.'
        : '';
    }
