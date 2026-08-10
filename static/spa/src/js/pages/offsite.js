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
      /* This banner used to read syncMeta.cadence, .ga4_tokens_used and .ga4_tokens_limit.
         build_offsite_response has never returned any of the three, so it rendered the literal
         "undefined · undefined / 0 GA4 tokens" on every load. GA4 API token quota is not
         tracked anywhere in this codebase, so there is no real number to print -- the token
         half is gone rather than replaced with an invented counter, and `tokensEmpty` stays
         true so its <sc-if> never opens.

         `lastUpdated` is now a real ISO timestamp of the last SUCCESSFUL ga4 sync (it used to
         be the engagement-rate percentage, under a key the UI renders as a date). Null means
         GA4 has genuinely never synced, and the banner says exactly that. */
      const ga4At = data.syncMeta.lastUpdated;
      const ga4Bad = data.syncMeta.lastStatus === 'error';
      off.cadence = ga4At
        ? ('GA4 data as of ' + ga4At.slice(0, 10) + ' ' + ga4At.slice(11, 16)
           + (ga4Bad ? ' — the last refresh failed, so this may be older than it looks' : ''))
        : 'GA4 has never synced for this project';
      off.tokens = '';
      off.tokensEmpty = true;
      /* The dot was hardcoded green, so "never synced" would have sat beside a healthy
         indicator. Grey it when there is nothing to be healthy about. */
      off.dotStyle = { width: '6px', height: '6px', borderRadius: '9999px', background: !ga4At ? '#cbd5e1' : ga4Bad ? '#dc2626' : '#10b981' };
      /* Off-site is genuinely mixed. Sessions/engagement/revenue are GA4; the referring-
         domain list is DataForSEO Backlinks. They sync on different schedules, so they get
         separate badges rather than one that would be wrong for half the page. */
      off.srcGa4 = this.srcBadge(['ga4']);
      off.srcRefDomains = this.srcBadge(['dataforseo_backlinks']);
      off.srcSocial = this.srcBadge(['ga4'],
        'Sessions are GA4. On-platform impressions need each platform own API and no platform connector is wired.');
      off.rangeLabel = s.range === '7d' ? 'last 7 days' : s.range === '90d' ? 'last 90 days' : 'last 30 days';
      off.kpis = [
        kpiCard('Off-site sessions', this.fmt(t.sessions), chip(pctD(t.sessions, pv.sessions)), 'vs. previous period'),
        /* null is "no sessions to divide by", not 0%. `null + '%'` printed the literal
           "null%"; the service's older `... else 0.0` printed a confident "0%" for a
           measurement nobody took. Same em-dash convention as every other unknown here. */
        kpiCard('Engagement rate', t.engagementRate == null ? '—' : t.engagementRate + '%', chip(null),
                t.engagementRate == null ? 'no off-site sessions in this period' : this.fmt(t.engagedSessions) + ' engaged'),
        kpiCard('Key events', this.fmt(Math.round(t.keyEvents)), chip(pctD(t.keyEvents, pv.keyEvents)), 'attributed conversions'),
        kpiCard('Attributed revenue', this.money(t.revenue), chip(pctD(t.revenue, pv.revenue)), 'GA4 totalRevenue'),
        /* Not "sites sending traffic". This count comes from the BACKLINKS table, is
           all-time rather than range-scoped, and most of the domains in it drove no measured
           GA4 session at all — the table below shows exactly how many did. */
        kpiCard('Referring domains', String(t.referringDomains), chip(null), 'domains linking to you (all-time)')
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

      /* channel mix — off-site channels only. This page reports on referral/social/video
         traffic, not organic search; Organic Search (and Direct/Paid/Unassigned) used to be
         listed too, just dimmed, which still showed a channel this page explicitly excludes.
         `chTotal` stays the sum across ALL channels (not just the ones listed below) so each
         row's % and the "of all sessions are off-site" stat both answer the same question:
         how much of the SITE's total traffic this off-site source drives. */
      const offCh = data.channels.filter(c => c.offsite);
      const chMax = Math.max.apply(null, offCh.map(c => c.sessions).concat([1]));
      const chTotal = data.channels.reduce((a, c) => a + c.sessions, 0) || 1;
      const chColors = { 'Referral': '#4f46e5', 'Organic Social': '#0a66c2', 'Social': '#0a66c2', 'Organic Video': '#dc2626', 'Video': '#dc2626' };
      off.channels = offCh.map(c => {
        const col = chColors[c.channel] || '#4f46e5';
        return {
          channel: c.channel, sessFmt: this.fmt(c.sessions),
          pctLabel: Math.round(c.sessions / chTotal * 100) + '%',
          labelColor: '#0f172a', labelWeight: 600,
          dotStyle: { width: '8px', height: '8px', borderRadius: '2px', background: col, flexShrink: 0 },
          barStyle: { height: '100%', width: Math.max(2, Math.round(c.sessions / chMax * 100)) + '%', background: col, borderRadius: '9999px', opacity: 1 }
        };
      });
      const offSess = offCh.reduce((a, c) => a + c.sessions, 0);
      off.offShareLabel = Math.round(offSess / chTotal * 100) + '%';
      off.offKeyEvents = this.fmt(Math.round(offCh.reduce((a, c) => a + c.keyEvents, 0)));

      /* LinkedIn spotlight */
      const li = data.social.find(x => x.platform === 'LinkedIn') || { impressions: null, sessions: 0, keyEvents: 0, revenue: 0 };
      const liConnected = !!(data.connectors && data.connectors.linkedin);
      // impressions === null means "no platform connector has ever reported this".
      // That is independent of `connected`, so the dash and the caption key off the
      // value itself — a connected flag must never turn a missing number into a
      // printed 0.
      const liImpr = li.impressions == null ? null : li.impressions;
      off.li = {
        impressions: liImpr == null ? '—' : this.fmt(liImpr), sessions: this.fmt(li.sessions),
        ctr: liImpr ? +(li.sessions / liImpr * 100).toFixed(1) + '%' : '—',
        keyEvents: this.fmt(Math.round(li.keyEvents)), revenue: this.money(li.revenue),
        connected: liConnected,
        badgeLabel: liConnected ? 'Connected' : 'No connector',
        badgeStyle: liConnected
          ? { marginLeft: 'auto', fontSize: '10px', fontWeight: 600, color: '#059669', background: '#ecfdf5', padding: '3px 8px', borderRadius: '9999px' }
          // Not underlined and not a pointer any more. The badge still opens Settings ->
          // Connections (that is where the explanation lives), but styling it as a link
          // promised a connect action that no longer exists there — the LinkedIn connector
          // is not wired into the sync engine, so there is nothing to press.
          : { marginLeft: 'auto', fontSize: '10px', fontWeight: 600, color: '#94a3b8', background: '#f1f5f9', padding: '3px 8px', borderRadius: '9999px', cursor: 'pointer' },
        subtitle: liConnected
          ? 'Connector live · impressions + click-throughs'
          : 'Sessions are GA4. Impressions & CTR need the LinkedIn API, which is not connected yet.',
        imprCaption: liImpr == null ? 'connector needed' : 'from LinkedIn API'
      };

      /* social table */
      const socColors = { 'LinkedIn': '#0a66c2', 'Reddit': '#ff4500', 'YouTube': '#dc2626', 'X (Twitter)': '#0f172a', 'Facebook': '#1877f2', 'Instagram': '#c13584' };
      off.social = data.social.map(r => ({
        platform: r.platform, source: r.source, channel: r.channel,
        connected: r.connected, notConnected: !r.connected,
        // Keyed off the value, not the toggle: a missing impression count stays a
        // dash even when the platform is marked connected in Settings.
        imprFmt: r.impressions != null ? this.fmt(r.impressions) : '—',
        sessFmt: this.fmt(r.sessions),
        // Same rule as imprFmt above: null is "undefined", not zero. A platform that drove
        // no sessions has no engagement rate to report — `Math.round(null * 100)` is 0, so
        // without this guard an unmeasured platform printed a confident "0%".
        engFmt: r.engagedRate == null ? '—' : Math.round(r.engagedRate * 100) + '%',
        keyFmt: this.fmt(Math.round(r.keyEvents)), revFmt: this.money(r.revenue),
        badge: r.platform.slice(0, 1),
        badgeStyle: { width: '26px', height: '26px', borderRadius: '6px', background: socColors[r.platform] || '#64748b', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '13px', fontWeight: 700, flexShrink: 0 }
      }));

      /* referring domains (sortable) */
      const refRows = this.sortRows(data.referrers.slice(), s.offSort);
      off.sort = { sessions: this.mkSortHandler('offSort', 'sessions'), keyEvents: this.mkSortHandler('offSort', 'keyEvents'), revenue: this.mkSortHandler('offSort', 'revenue') };
      off.arrow = { sessions: this.arrow(s.offSort, 'sessions'), keyEvents: this.arrow(s.offSort, 'keyEvents'), revenue: this.arrow(s.offSort, 'revenue') };
      /* No onTrack / canTrack / tracked. The "Track" control here fired
         notify('… added to backlink tracking on next sync') and wrote nothing; its
         companion "Tracked link" badge read `r.tracked`, which this service has never
         returned, so the badge could not light up even in the same render. Removed
         (control + badge + handler) on 2026-07-27 rather than rebuilt, because there is
         no honest thing for it to do:

           - It cannot mean "start collecting this domain". dataforseo_backlinks fetches
             the target's whole profile in one call (limit 1000, ordered by rank) and takes
             no per-domain input, so every row in this table is already synced every run.
             That is the opposite of SavedKeyword, where Track is real precisely because an
             untracked keyword is genuinely never sent to the paid per-keyword endpoints.
           - It cannot mean "add to tracked_competitors". That table drives the Positioning
             competitor grid (SERP rank share); a site that links to us is not a site we
             compete with, and filing it there would corrupt that page.
           - A ProjectSettings pin was the only remaining option, and a pin that merely
             reorders a 20-row table that is already sortable on sessions, key events and
             revenue is a bookmark wearing the word "Track" — a third, weaker meaning of
             "tracked" next to the two the product already defines. Quieter, still a lie.

         If a real need appears later it is a watchlist feeding a lost-link alert, which is
         an alerts_service feature, not a button on this table. */
      off.referrers = refRows.map(r => ({
        domain: r.domain, rank: r.authorityScore,
        rankStyle: { fontWeight: 600, color: r.authorityScore >= 70 ? '#059669' : r.authorityScore >= 40 ? '#2563eb' : '#64748b' },
        sessFmt: this.fmt(r.sessions),
        // Most referring domains drive no measured sessions — they are listed because they
        // LINK to us, not because GA4 saw traffic from them. `|| 0` turned every one of
        // those into "0% engaged", a number nobody measured, sitting next to real ones.
        engFmt: r.engagementRate == null ? '—' : r.engagementRate + '%',
        keyFmt: this.fmt(Math.round(r.keyEvents)), revFmt: this.money(r.revenue),
        href: 'https://' + r.domain
      }));

      /* Most-viewed pages — ALL traffic, not off-site traffic.
         seo_daily has no channel column (GA4 writes it from a date x country x device x
         pagePath report), so this list cannot be scoped to referral & social and never was:
         it included Organic Search and Direct the whole time it was headed "Where off-site
         traffic lands / Pages that referral & social visitors enter on". And `landing_page`
         is filled from `pagePath`, so these are page VIEWS, not entrances — `pageviews` is
         the additive metric at this grain. Both facts are now in the heading and the column
         labels. A real off-site landing-page table needs a new GA4 report on landingPage x
         sessionDefaultChannelGroup; there is no filter over this data that produces one. */
      off.landing = data.landingPages.map(r => ({
        // topSource is '' when the driving channel was never measured — show a dash,
        // not a guessed channel name.
        url: r.url, topSource: r.topSource || '—',
        viewsFmt: r.pageviews == null ? '—' : this.fmt(r.pageviews),
        sessFmt: this.fmt(r.sessions), engFmt: Math.round(r.engagedRate * 100) + '%',
        bounceFmt: r.bounceRate == null ? '—' : Math.round(r.bounceRate * 100) + '%',
        newUsersFmt: r.newUsers == null ? '—' : this.fmt(r.newUsers),
        keyFmt: this.fmt(Math.round(r.keyEvents))
      }));

      vals.off = off;
    }

