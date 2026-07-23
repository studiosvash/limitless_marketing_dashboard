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
