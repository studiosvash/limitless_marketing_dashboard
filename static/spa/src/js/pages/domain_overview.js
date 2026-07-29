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
        /* the market this analysis is read in — the project's own location, i.e. the
           same value the Position Tracking live-SERP drawer uses (see doLocation()) */
        location: this.doLocation(),
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
            onTrack: () => this.trackDomainOverviewKws([trackRow])
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
