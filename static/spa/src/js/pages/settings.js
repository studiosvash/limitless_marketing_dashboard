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
      const rulesArr = (s.rules || data.alertRules || []);
      const cur = s.settingsSub || 'general';

      /* ---- sub-tab bar ---- */
      const invitedCount = team.filter(m => m.status === 'invited').length;
      const enabledRules = rulesArr.filter(r => r.on).length;
      /* A cap of 0 is "no cap set", not "a cap of zero dollars". Comparing against it flagged
         the "!" sub-tab badge and the over-budget warning on every project that had ever spent
         a cent, before the user had chosen any budget at all. `u.est_monthly` is also the one
         PROJECTED figure in this payload (settings_service._usage_raw) -- it is 0 whenever
         there is no recorded spend to project from, so this can never fire off a forecast
         built from nothing. */
      const capNum = Number(s.budgetCap) || 0;
      const hasCap = capNum > 0;
      const overCap = hasCap && u.est_monthly > capNum;
      /* Account-wide DataForSEO balance + hard $/month cap (see budget_service.py). Separate
         from capNum/hasCap/overCap above, which are this PROJECT's soft cap over its own
         spend -- `s.budget` is the whole account's shared cap, fetched once in boot() and
         refreshed after every sync, same object the topbar banner reads. Null until that
         first response lands. */
      const dfs = s.budget;
      const dfsCap = dfs ? dfs.cap : 100;
      const dfsSpent = dfs ? dfs.spent : 0;
      const dfsPct = dfs ? dfs.pct : 0;
      const dfsExceeded = !!(dfs && dfs.exceeded);
      const dfsRed = !!(dfs && dfs.red);
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

      /* ---- recorded spend -------------------------------------------------------------
         Every dollar figure below EXCEPT `projected` is a sum of `connector_costs` rows,
         i.e. charges a real billed DataForSEO / OpenAI response reported for itself
         (settings_service._usage_raw -> cost_service). `projected` is the single forecast
         on this screen and is never rendered without `u.est_monthly_basis` next to it.

         Three distinctions this code exists to preserve:

         1. "Nothing recorded" is not "$0.00". `u.has_recorded_spend` is derived from the
            COUNT of spend events, not the total -- which is 0.0 in both the never-synced and
            the genuinely-free case. A project that has never run a paid connector gets the
            empty state, not a measurement it does not have. Same rule per module row via
            `item.recorded`.
         2. `cost_per_unit` is null (never 0) when the denominator is unknown: a connector
            that metered no units, or a module row fed by several connectors that meter
            different things. `rate()` renders those as "—", never "$0.0000".
         3. this.money() is 2dp, which prints a real $0.0034 charge as "$0.00" -- the same
            lie as case 1 in a different disguise. `usd()` says "under $0.01" instead. It is
            worded, not "<$0.01", because a literal '<' in a rendered value is a tag start to
            anything that treats the output as markup. */
      const usd = v => (v > 0 && v < 0.01) ? 'under $0.01' : this.money(v);
      const plural = (n, word) => n + ' ' + word + (n === 1 ? '' : 's');
      /* Unit rates are genuinely sub-cent ($0.00125 per crawled page is DataForSEO's real
         OnPage price), so a fixed 2 or 4 dp would round the actual published rate away.
         Six dp then trimmed of trailing zeros keeps the exact recorded figure and still
         prints a normal $1.50 as $1.50. */
      const rate = v => {
        if (v == null) return '—';
        let str = Number(v).toFixed(6).replace(/0+$/, '');
        if (/\.$/.test(str)) str += '00';
        else if (/\.\d$/.test(str)) str += '0';
        return '$' + str;
      };
      const win = u.window || { total: 0, runs: 0, days: 90, start: '', end: '', by_connector: [] };
      const connCosts = win.by_connector || [];
      const monthCosts = u.by_month || [];
      const maxConnCost = connCosts.reduce((m, c) => (c.cost > m ? c.cost : m), 0) || 1;
      const maxMonthCost = monthCosts.reduce((m, c) => (c.cost > m ? c.cost : m), 0) || 1;
      // A zero-spend month/connector gets a zero-width bar, not a 2% sliver: a visible bar
      // where nothing was billed is a small fabrication of its own. The 2% floor exists only
      // so a real-but-tiny charge is still visible next to a large one.
      const costTrack = (value, max, color) => ({
        height: '100%', borderRadius: '9999px', background: color,
        width: (value > 0 ? Math.max(2, Math.round((value / max) * 100)) : 0) + '%'
      });

      /* Month-over-month, stated against the last COMPLETE month only. The current month is
         still accruing (cost_by_month marks it `partial`), so comparing a part-month against
         a whole one would read as a fall in spend that has not happened. */
      const fullMonths = monthCosts.filter(m => !m.partial);
      const lastFull = fullMonths.length ? fullMonths[fullMonths.length - 1] : null;
      const prevFull = fullMonths.length > 1 ? fullMonths[fullMonths.length - 2] : null;
      let trendLabel = 'Not enough history yet to compare months.';
      let trendColor = '#94a3b8';
      if (lastFull && prevFull && prevFull.cost > 0) {
        const delta = Math.round(((lastFull.cost - prevFull.cost) / prevFull.cost) * 100);
        trendLabel = lastFull.label + ' was ' + (delta >= 0 ? 'up ' : 'down ') + Math.abs(delta)
          + '% on ' + prevFull.label + ' (' + usd(prevFull.cost) + ' → ' + usd(lastFull.cost) + ').';
        trendColor = delta > 0 ? '#b45309' : '#15803d';
      } else if (lastFull && prevFull) {
        trendLabel = 'Nothing was billed in ' + prevFull.label + ', so there is no baseline to compare '
          + lastFull.label + ' against.';
      }

      /* ---- connections: Ads platforms (Google Ads / Meta Ads) -------------------------
         A real credential-entry form: fields are typed here, saved via
         PUT /settings {adsCredentials: {...}} (settings_service.apply_settings_update),
         and tested via this.testAdsCredential -> POST .../ads-credentials/test, either
         against the typed-in draft or (if nothing was edited) the already-saved value.
         See docs/superpowers/specs/2026-08-03-ads-credentials-design.md. */
      const adsSaved = data.adsCredentials || {};
      const adsDraft = s.adsCreds || { google_ads: {}, meta_ads: {} };
      const adsTesting = s.adsTesting || {};
      const adsSaving = s.adsSaving || {};
      const adsTestResult = s.adsTestResult || {};
      const SECRET_FIELD_BY_PLATFORM = { google_ads: 'developer_token', meta_ads: 'access_token' };
      const adsPill = tone => ({ fontSize: '11px', fontWeight: 600, padding: '2px 9px', borderRadius: '9999px', background: tone.pillBg, color: tone.pillFg });
      const adsBtn = (busy, bg) => ({ display: 'inline-flex', padding: '8px 16px', background: bg, color: 'white', fontSize: '13px', fontWeight: 600, borderRadius: '8px', cursor: busy ? 'default' : 'pointer', opacity: busy ? 0.6 : 1 });
      const adsResultBox = ok => ({ marginTop: '10px', fontSize: '12px', lineHeight: 1.5, padding: '8px 10px', borderRadius: '6px', color: ok ? '#15803d' : '#b91c1c', background: ok ? '#f0fdf4' : '#fff1f2', border: '1px solid ' + (ok ? '#bbf7d0' : '#fecaca') });

      const ADS_PLATFORMS = [
        {
          key: 'google_ads',
          name: 'Google Ads',
          fields: [
            { name: 'developer_token', label: 'Developer Token', placeholder: 'Issued in Google Ads → Tools → API Center' },
            { name: 'customer_id', label: 'Customer ID', placeholder: 'e.g. 1234567890' },
            { name: 'login_customer_id', label: 'Manager (MCC) Customer ID — optional', placeholder: 'Only if the account sits under a manager account' },
          ],
          instruction: 'Get your developer token from Google Ads → Tools → API Center. Customer ID is the 10-digit account number shown top-right in Google Ads.',
        },
        {
          key: 'meta_ads',
          name: 'Meta Ads',
          fields: [
            { name: 'access_token', label: 'Access Token', placeholder: 'System User token (Business Manager)' },
            { name: 'ad_account_id', label: 'Ad Account ID', placeholder: 'act_XXXXXXXXXX' },
          ],
          instruction: 'Create a System User token in Business Manager → System Users — a personal token will expire. Ad Account ID is in Business Manager → Ad Accounts, in the act_XXXXXXXXXX form.',
        },
      ];

      const adsCards = ADS_PLATFORMS.map(p => {
        const saved = adsSaved[p.key] || { configured: false, masked: null };
        const draft = adsDraft[p.key] || {};
        const testing = !!adsTesting[p.key];
        const saving = !!adsSaving[p.key];
        const result = adsTestResult[p.key];
        const tone = saved.configured
          ? { label: 'Credential saved', dot: '#22c55e', pillBg: '#ecfdf5', pillFg: '#059669' }
          : { label: 'Not connected', dot: '#cbd5e1', pillBg: '#f1f5f9', pillFg: '#94a3b8' };

        return {
          name: p.name,
          statusLabel: tone.label,
          statusStyle: adsPill(tone),
          dotStyle: { width: '9px', height: '9px', borderRadius: '9999px', background: tone.dot, flexShrink: 0 },
          fields: p.fields.map(f => {
            const isSecret = f.name === SECRET_FIELD_BY_PLATFORM[p.key];
            const placeholder = (isSecret && saved.configured)
              ? ('Saved: ' + saved.masked + ' — leave blank to keep it')
              : f.placeholder;
            return {
              label: f.label,
              value: draft[f.name] || '',
              placeholder: placeholder,
              onInput: e => this.setState(prev => ({
                adsCreds: Object.assign({}, prev.adsCreds, {
                  [p.key]: Object.assign({}, (prev.adsCreds || {})[p.key], { [f.name]: e.target.value }),
                }),
              })),
            };
          }),
          testLabel: testing ? 'Testing…' : 'Test connection',
          testBtnStyle: adsBtn(testing, '#4f46e5'),
          onTest: () => { if (!testing) this.testAdsCredential(p.key); },
          saveLabel: saving ? 'Saving…' : 'Save',
          saveBtnStyle: adsBtn(saving, '#10b981'),
          onSave: () => { if (!saving) this.saveAdsCredential(p.key); },
          hasTestResult: !!result,
          testResultText: result ? result.detail : '',
          testResultStyle: result ? adsResultBox(result.ok) : {},
          instruction: p.instruction,
        };
      });

      /* Delete-project confirmation. The typed value must equal the project's real domain;
         the button stays disabled until it does, so the destructive call cannot fire on a
         near-miss. */
      const delDomain = data.project.domain || '';
      const delTyped = (s.delProjText || '').trim();
      const delArmed = !!delDomain && delTyped.toLowerCase() === delDomain.toLowerCase();

      vals.st = {
        delOpen: !!s.delProjOpen,
        delDomain: delDomain,
        delTitle: 'Delete ' + delDomain,
        delBody: 'This permanently removes ' + delDomain + ', its tracked keywords, and every synced metric for it across 19 tables. Other projects are not affected. This cannot be undone.',
        delPrompt: 'Type ' + delDomain + ' to confirm',
        delText: s.delProjText || '',
        delArmed: delArmed,
        delBtnLabel: s.delProjBusy ? 'Deleting…' : 'Delete this project',
        delInputStyle: { width: '100%', boxSizing: 'border-box', fontSize: '14px', padding: '10px 12px', border: '1px solid ' + (delArmed ? '#fca5a5' : '#e2e8f0'), borderRadius: '8px', outline: 'none', fontFamily: 'monospace' },
        delBtnStyle: { padding: '9px 16px', borderRadius: '8px', fontSize: '13px', fontWeight: 600, color: 'white', background: (delArmed && !s.delProjBusy) ? '#dc2626' : '#fca5a5', cursor: (delArmed && !s.delProjBusy) ? 'pointer' : 'default' },

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
        gsc: s.creds.gsc, ga4: s.creds.ga4, dataforseo: s.creds.dataforseo,
        credsSaveLabel: s.credsSaved ? 'Saved \u2713' : 'Save credentials',
        credsTestLabel: s.credsTesting ? 'Checking\u2026' : 'Test connection',
        credsTestBusy: !!s.credsTesting,
        /* "Saved \u2713" only ever meant the write succeeded \u2014 GA4 had no access check at all, so a
           wrong-but-present property id looked fine until a sync failed 20 minutes later. This
           renders the same live probe the Add-domain modal uses, run against the current form. */
        credsTestRows: (s.credsTestResult ? s.credsTestResult.checks : []).map(c => {
          const tone = { ok: ['#d1fae5', '#047857', '\u2713'], fail: ['#fee2e2', '#b91c1c', '\u2717'],
                        absent: ['#f1f5f9', '#94a3b8', '\u2014'], unknown: ['#fef3c7', '#b45309', '?'] }[c.state]
                       || ['#f1f5f9', '#94a3b8', '\u2014'];
          return {
            label: c.label, detail: c.detail,
            dotStyle: { display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '18px', height: '18px', borderRadius: '50%', background: tone[0], color: tone[1], fontSize: '11px', fontWeight: 700, flexShrink: 0 },
            dotText: tone[2],
          };
        }),
        credsTestShown: !!s.credsTestResult,
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
          /* `stale_error` means: the last run really did fail, but its cause was a missing
             credential that IS configured now. Showing the old message as current made the
             card flatly contradict the value in the Site credentials form above it -- a user
             who had just saved their GA4 property ID kept reading "No GA4 property
             configured". Amber, not red: nothing is broken, it simply has not re-run. */
          const stale = c.status === 'stale_error';
          return {
            name: c.name, last: c.last_sync || 'never', records: this.fmt(c.records) + ' records',
            error: c.error,
            isStale: stale,
            staleNote: stale
              ? 'Fixed since the last run — the credential is saved now. Press Refresh to apply it. (Last run failed: ' + (c.error_was || '').slice(0, 90) + ')'
              : '',
            staleStyle: { fontSize: '11.5px', color: '#b45309', background: '#fffbeb', border: '1px solid #fde68a', borderRadius: '6px', padding: '7px 9px', marginTop: '8px', lineHeight: 1.45 },
            cardStyle: bad
              ? { padding: '14px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '10px' }
              : stale
                ? { padding: '14px', background: '#fffbeb', border: '1px solid #fde68a', borderRadius: '10px' }
                : { padding: '14px', background: ok ? '#f0fdf4' : '#f8fafc', border: '1px solid ' + (ok ? '#bbf7d0' : '#e2e8f0'), borderRadius: '10px' },
            dotStyle: { width: '8px', height: '8px', borderRadius: '9999px', background: bad ? '#dc2626' : stale ? '#f59e0b' : (ok ? '#22c55e' : '#cbd5e1') },
            recordsStyle: { fontSize: '12px', color: bad ? '#b91c1c' : stale ? '#b45309' : (ok ? '#15803d' : '#64748b'), marginTop: '2px' }
          };
        }),
        healthLabel: data.connectors.length === 0
          ? 'No sources synced yet.'
          : (data.connectors.some(c => c.status === 'error')
              ? 'Some sources need attention.'
              : (data.connectors.some(c => c.status === 'stale_error')
                  ? 'A credential was fixed since the last run — press Refresh to apply it.'
                  : 'All healthy.')),
        /* ---- connections: social & platform connectors ----------------------------------
           These were "Connect" buttons that authenticated nothing. `togglePlatform` flipped a
           boolean into ProjectSettings.data.platformConnectors and the row immediately read
           "Connected" -- no OAuth, no credential form, no verification, and no data. Off-site
           SEO's `impressions` is hardcoded None for every platform regardless of the toggle
           (apps/dashboard/services/offsite_service.py), so pressing Connect changed a green
           pill and nothing else. That is the "never fabricate data to fill a shape" rule
           applied to a control instead of a number: a switch that looks like a connection but
           is only a display preference is the same lie.

           Only two of the seven have connector code at all -- pipeline/connectors/linkedin.py
           and meta.py -- and neither is listed in PAGE_CONNECTORS or ALL_CONNECTORS
           (pipeline/services/sync_engine.py), so no refresh in this app runs them; LinkedIn's
           also writes ad_metrics, not off-site impressions. Reddit, YouTube, X, Instagram and
           Facebook have no connector module whatsoever.

           So the row is now inert and says so. When a connector is genuinely wired, replace
           this with a real credential flow -- not with the boolean. */
        platRows: PLAT.map(p => ({
          key: p[0], name: p[1], desc: p[2], connected: false,
          statusLabel: 'Not connected',
          statusStyle: { fontSize: '11px', fontWeight: 600, padding: '2px 9px', borderRadius: '9999px', background: '#f1f5f9', color: '#94a3b8' },
          actionLabel: 'Connector not built yet',
          // `default` cursor, muted palette, no hover, no handler: nothing about it should
          // read as pressable, because there is nothing behind it to press.
          actionStyle: { padding: '7px 14px', border: '1px dashed #e2e8f0', background: '#f8fafc', color: '#94a3b8', borderRadius: '8px', fontSize: '12.5px', fontWeight: 600, cursor: 'default' }
        })),
        platNote: 'None of these have a working connector yet, so there is deliberately no button here that would appear to connect one and do nothing. Off-site SEO already shows the GA4 sessions arriving from these platforms; what is missing is on-platform impressions & CTR, which only each platform’s own API can report.',
        adsCards: adsCards,
        adsIntro: 'Enter your Ads platform credentials, then test the connection.',

        /* ---- automation: sync + crawl ---- */
        // A scheduler DOES exist now (`manage.py run_scheduled_syncs`, driven hourly from the
        // OS task scheduler), and data.sync.next_run/.day come from the very same cadence +
        // run-history logic that command acts on -- so this date is what will actually happen,
        // not a parallel guess. They are still null in the two cases where no honest date can
        // be derived: every module set to `manual`, or no successful run yet to measure a
        // cadence from. The ternary also avoids the literal "null (null)" that string
        // concatenation would otherwise produce.
        nextRun: data.sync.next_run ? (data.sync.next_run + ' (' + data.sync.day + ')') : 'nothing due — every module is set to manual, or nothing has synced yet',
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

        /* ---- DataForSEO account: shared balance + hard monthly cap ---- */
        dfsBalance: (dfs && dfs.balance != null) ? this.money(dfs.balance) : 'Not checked yet',
        dfsBalanceStyle: { fontSize: '24px', fontWeight: 600, marginTop: '3px', color: (dfs && dfs.balance != null) ? (dfs.balance <= 10 ? '#dc2626' : '#0f172a') : '#cbd5e1' },
        dfsBalanceNote: (dfs && dfs.balance_checked_at)
          ? ('Checked ' + this.relTime(dfs.balance_checked_at) + ' — re-checked after every sync.')
          : 'Checked after each sync (free — does not spend credit); nothing has synced yet.',
        dfsSpentText: usd(dfsSpent), dfsCapText: usd(dfsCap), dfsPctText: dfsPct.toFixed(0) + '%',
        dfsCapBar: { height: '100%', borderRadius: '9999px', background: dfsExceeded ? '#dc2626' : (dfsRed ? '#f59e0b' : '#10b981'), width: Math.min(100, dfsPct) + '%' },
        dfsExceeded: dfsExceeded,
        // Answers "why did I get a $5 notification?" directly on the screen that shows the cap.
        dfsThresholdNote: 'Every DataForSEO call updates this figure. You get a notification each '
          + 'time total spend this month passes another $5, a specific one at $50, a red warning '
          + 'at 90% of the cap (' + usd(dfsCap * 0.9) + '), and syncs that call DataForSEO pause '
          + 'automatically once the ' + usd(dfsCap) + ' cap is reached.',

        /* ---- usage & budget ---- */
        // MEASURED. month_to_date is cost_since(1st of this month) -- billed rows only.
        // A project with NO recorded run anywhere shows an em dash, not $0.00: cost_service
        // returns 0.0 for "never recorded" and for "measured zero" alike, and printing the
        // second one's figure for the first would assert a measurement that was never taken.
        // The two are told apart by the RUN COUNT (u.has_recorded_spend / u.month_runs), which
        // is the only field that distinguishes them.
        mtd: u.has_recorded_spend ? usd(u.month_to_date) : '—',
        mtdStyle: { fontSize: '24px', fontWeight: 600, marginTop: '3px', color: u.has_recorded_spend ? '#0f172a' : '#cbd5e1' },
        budget: this.money(u.budget),
        budgetPct: hasCap ? Math.min(100, Math.round((u.month_to_date / capNum) * 100)) : 0,
        mtdNote: !u.has_recorded_spend
          ? 'No sync has ever recorded a charge for this project — nothing measured yet, which is not the same as $0.00.'
          : (u.month_runs
            ? (plural(u.month_runs, 'billed run') + ' so far in the '
               + plural(u.days_elapsed, 'day') + ' of this month')
            : 'Nothing has been billed this month — the spend recorded for this project is all from earlier months.'),
        // PROJECTED -- the only forecast on this screen. It is always rendered with projTag
        // and projBasis beside it, and _usage_raw returns 0 with is_projection false rather
        // than extrapolating from a month with no billed run.
        projected: usd(u.est_monthly),
        projIsForecast: !!u.est_monthly_is_projection,
        noProjection: !u.est_monthly_is_projection,
        projTag: 'PROJECTED',
        projTagStyle: { fontSize: '10px', fontWeight: 700, letterSpacing: '0.06em', padding: '2px 7px', borderRadius: '4px', background: '#fffbeb', color: '#b45309', border: '1px solid #fde68a' },
        projBasis: u.est_monthly_basis || '',
        projBasisStyle: { fontSize: '11.5px', color: u.est_monthly_is_projection ? '#b45309' : '#94a3b8', lineHeight: 1.5, marginTop: '9px' },
        budgetCap: s.budgetCap, savedBudget: s.savedBudget ? 'Saved \u2713' : '',
        enforceToggle: toggle(!!s.budgetEnforce),
        hasCap: hasCap, noCap: !hasCap,
        capNote: hasCap
          ? ('Bar shows the projected month against your $' + capNum + ' cap.')
          : 'No cap set, so nothing is being tracked against one. Enter a monthly figure below.',
        capBar: { height: '100%', borderRadius: '9999px', background: overCap ? '#f59e0b' : '#10b981', width: (hasCap ? Math.min(100, Math.round((u.est_monthly / capNum) * 100)) : 0) + '%' },
        overCap: overCap,
        quotaGa4: bar(q.ga4_tokens_used, q.ga4_tokens_limit, '#6366f1'),
        quotaGa4Label: this.fmt(q.ga4_tokens_used) + ' / ' + this.fmt(q.ga4_tokens_limit) + ' tokens today',
        quotaAds: bar(q.ads_ops_used, q.ads_ops_limit, '#0ea5e9'),
        quotaAdsLabel: q.ads_ops_used + ' / ' + this.fmt(q.ads_ops_limit) + ' ops/day',
        quotaGsc: bar(q.gsc_queries_used, q.gsc_queries_limit, '#8b5cf6'),
        quotaGscLabel: q.gsc_queries_used + ' / ' + this.fmt(q.gsc_queries_limit) + ' queries/day',

        /* ---- recorded spend: 90-day window ---- */
        hasCost: !!u.has_recorded_spend,
        noCost: !u.has_recorded_spend,
        costTotal: usd(win.total),
        costWindowLabel: 'Last ' + win.days + ' days \u00b7 ' + win.start + ' \u2192 ' + win.end,
        costRunsLabel: plural(win.runs, 'billed run') + ' across ' + plural(connCosts.length, 'connector'),
        // The empty state is deliberately NOT a row of $0.00 figures: no row recorded means
        // no measurement, which is a different fact from a measured zero.
        costEmptyTitle: 'No spend recorded yet',
        costEmptyBody: 'Every DataForSEO response reports what it charged, and each run is '
          + 'written to connector_costs. Nothing has been recorded for this project in the last '
          + win.days + ' days \u2014 so this is "not measured yet", not "$0.00". Run a sync and the '
          + 'real per-connector cost appears here.',
        costEmptyBtn: syncing ? 'Sync in progress\u2026' : '\u26a1 Run a full sync now',
        costEmptyBtnStyle: {
          display: 'inline-flex', marginTop: '18px', padding: '10px 18px', background: '#10b981',
          color: 'white', fontSize: '13px', fontWeight: 600, borderRadius: '8px',
          cursor: syncing ? 'default' : 'pointer', opacity: syncing ? 0.5 : 1
        },
        costEmptyRun: () => { if (!syncing) this.startSync('all'); },
        connectorRows: connCosts.map(c => ({
          name: c.connector,
          costFmt: usd(c.cost),
          runsLabel: plural(c.runs, 'run'),
          // units null => the connector metered nothing; 0 units is also not a denominator.
          unitsLabel: c.units == null ? 'units not metered'
            : (this.fmt(c.units) + (c.units === 1 ? ' unit' : ' units')),
          rateFmt: rate(c.cost_per_unit),
          rateStyle: { padding: '10px 0', textAlign: 'right', color: c.cost_per_unit == null ? '#cbd5e1' : '#475569' },
          barStyle: costTrack(c.cost, maxConnCost, '#4f46e5')
        })),
        hasUnattributed: (u.unattributed || []).length > 0,
        unattributedNote: 'Of that, ' + usd(u.unattributed_total) + ' came from connectors no '
          + 'sync module below owns \u2014 the explicit Domain overview / Live SERP lookups and AI '
          + 'visibility runs, which are billed when you press their button, not on a schedule. '
          + 'That is why the module rows sum to ' + usd(u.attributed_total) + ', not the total above.',

        /* ---- recorded spend: month over month ---- */
        monthRows: monthCosts.map(m => ({
          label: m.label,
          costFmt: m.runs ? usd(m.cost) : 'nothing recorded',
          costStyle: { fontSize: '13px', fontWeight: m.runs ? 600 : 400, color: m.runs ? '#0f172a' : '#cbd5e1' },
          runsLabel: m.runs ? plural(m.runs, 'run') : '',
          isPartial: !!m.partial,
          partialLabel: 'still accruing',
          barStyle: costTrack(m.cost, maxMonthCost, m.partial ? '#818cf8' : '#4f46e5')
        })),
        trendLabel: trendLabel,
        trendStyle: { fontSize: '12px', color: trendColor, marginTop: '12px', lineHeight: 1.5 },

        /* ---- cost by module ---- */
        // estFmt carries a MEASUREMENT (90-day recorded spend for that module) when there is
        // one, and the honest "not yet recorded" note when there is not -- never $0.00. The
        // column heading in settings.html says "Recorded \u00b7 90 days" for exactly that reason.
        usageRows: u.items.map(item => ({
          module: item.module, cadence: item.cadence,
          estFmt: item.est == null ? (item.note || '\u2014') : usd(item.est),
          estStyle: { padding: '10px 0', textAlign: 'right', fontWeight: item.recorded ? 600 : 400, color: item.recorded ? '#0f172a' : '#94a3b8' },
          runsLabel: item.recorded ? plural(item.runs, 'run') : '\u2014',
          unitsLabel: !item.recorded ? '\u2014'
            : (item.units == null ? 'units not metered'
              : (this.fmt(item.units) + (item.units === 1 ? ' unit' : ' units')
                 + (item.units_mixed ? ' (mixed)' : ''))),
          rateFmt: item.recorded ? rate(item.cost_per_unit) : '\u2014',
          rateStyle: { padding: '10px 0', textAlign: 'right', color: item.cost_per_unit == null ? '#cbd5e1' : '#475569' },
          rateTitle: item.units_mixed
            ? 'Several connectors feed this module and they meter different things, so a single cost-per-unit would not be a real rate. The per-connector rates are in the breakdown above.'
            : '',
          canSync: !!scopeFor[item.module] && !syncing,
          run: () => this.startSync(scopeFor[item.module])
        })),
        moduleTotalLabel: 'Measured from real billed runs \u00b7 attributed total ' + usd(u.attributed_total),

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
