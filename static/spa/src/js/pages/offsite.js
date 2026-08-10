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

      /* trend — stacked area by channel.
         query_offsite_trend_raw has always grouped by (date, channel) and then summed the
         channel away, so the chart drew one undifferentiated line over data that already knew
         whether a spike was a link, a LinkedIn post or a YouTube video. Each point now carries
         `channels`, zero-filled with the same keys on every day so a band cannot appear and
         vanish mid-series. The bands always sum to `sessions` — the service guarantees it —
         so the stack and the KPI above it cannot disagree.

         Chart furniture (a y-axis, gridlines, hover values) follows the Overview trend's
         pattern: labels live in HTML outside the SVG, because the SVG uses
         preserveAspectRatio="none" and would stretch any text inside it. */
      const tr = data.trend || [], W = 600, H = 220;
      const chColorsTrend = { 'Referral': '#4f46e5', 'Organic Social': '#0a66c2', 'Social': '#0a66c2', 'Organic Video': '#dc2626', 'Video': '#dc2626' };
      const chOrder = tr.length ? Object.keys(tr[0].channels || {}) : [];
      /* A band that is zero across the whole window is a legend entry for something that did
         not happen. Drop it from the chart; the channel-mix panel below still lists it. */
      const bands = chOrder.filter(ch => tr.some(d => ((d.channels || {})[ch] || 0) > 0));
      off.trendEmpty = !tr.length || !bands.length;
      const dayTotal = d => bands.reduce((a, ch) => a + ((d.channels || {})[ch] || 0), 0);
      const rawMax = Math.max.apply(null, tr.map(dayTotal).concat([0]));
      /* Round the axis up to a readable number so the gridlines land on values a human would
         write down, rather than on 1/4 of whatever the tallest day happened to be. */
      const niceMax = v => {
        if (!(v > 0)) return 4;
        const p = Math.pow(10, Math.floor(Math.log10(v)));
        const n = v / p;
        return (n <= 1 ? 1 : n <= 2 ? 2 : n <= 5 ? 5 : 10) * p;
      };
      const yMax = niceMax(rawMax);
      const xs = i => (tr.length > 1 ? i * (W / (tr.length - 1)) : W / 2);
      const yOf = v => H - (v / yMax) * H;
      off.gridLines = [0, 0.25, 0.5, 0.75, 1].map(f => ({ y: (H * (1 - f)).toFixed(1) }));
      off.yTicks = [1, 0.75, 0.5, 0.25, 0].map(f => this.fmt(Math.round(yMax * f)));
      /* Lower edge of each band = the sum of every band below it. Drawn bottom-up so the
         earlier bands sit at the base of the stack, in the service's channel order. */
      const lower = tr.map(() => 0);
      off.bands = bands.map(ch => {
        const upper = tr.map((d, i) => lower[i] + ((d.channels || {})[ch] || 0));
        const top = tr.map((d, i) => xs(i).toFixed(1) + ',' + yOf(upper[i]).toFixed(1));
        const bottom = tr.map((d, i) => xs(i).toFixed(1) + ',' + yOf(lower[i]).toFixed(1)).reverse();
        const path = tr.length ? 'M' + top.join(' L') + ' L' + bottom.join(' L') + ' Z' : '';
        const col = chColorsTrend[ch] || '#64748b';
        for (let i = 0; i < tr.length; i++) lower[i] = upper[i];
        return { channel: ch, path, fill: col, line: top.join(' '), stroke: col };
      });
      off.legend = off.bands.map(b => ({
        channel: b.channel,
        swatchStyle: { width: '10px', height: '10px', borderRadius: '2px', background: b.fill, flexShrink: 0 }
      }));
      off.xTicks = (() => {
        if (!tr.length) return [];
        const n = Math.min(6, tr.length);
        const out = [];
        for (let i = 0; i < n; i++) {
          const idx = n === 1 ? 0 : Math.round(i * (tr.length - 1) / (n - 1));
          const d = new Date(tr[idx].date);
          out.push({ label: (d.getMonth() + 1) + '/' + d.getDate(), pct: (n === 1 ? 50 : i * (100 / (n - 1))).toFixed(3) });
        }
        return out;
      })();
      /* Hover lives on its own state key rather than the shared `chartHoverIndex` the
         Overview trend uses, so two charts can never read each other's hovered index. */
      const hIdx = (s.offHoverIdx == null || !tr[s.offHoverIdx]) ? null : s.offHoverIdx;
      off.hoverZones = tr.map((d, i) => {
        const w = W / Math.max(1, tr.length);
        return { x: (xs(i) - w / 2).toFixed(1), w: w.toFixed(1), onEnter: () => this.setState({ offHoverIdx: i }) };
      });
      off.hoverOut = () => this.setState({ offHoverIdx: null });
      off.hasHover = hIdx !== null;
      off.hoverX = hIdx === null ? 0 : xs(hIdx).toFixed(1);
      off.ttX = hIdx === null ? 0 : (xs(hIdx) < 300 ? xs(hIdx) + 14 : xs(hIdx) - 174);
      off.ttDate = hIdx === null ? '' : tr[hIdx].date;
      off.ttRows = hIdx === null ? [] : bands.map(ch => ({
        label: ch, value: this.fmt((tr[hIdx].channels || {})[ch] || 0),
        dotStyle: { width: '8px', height: '8px', borderRadius: '2px', background: chColorsTrend[ch] || '#64748b', flexShrink: 0 }
      }));
      off.ttTotal = hIdx === null ? '' : this.fmt(tr[hIdx].sessions);
      off.ttEngaged = hIdx === null ? '' : this.fmt(tr[hIdx].engagedSessions);
      off.ttH = 64 + (bands.length + 1) * 18;

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

      /* Social & video table — the sources GA4 actually measured, LinkedIn pinned first.
         It used to be a fixed LinkedIn/Reddit/YouTube/X roster that printed whether or not
         GA4 had ever seen those platforms and discarded every other source, so a project whose
         off-site traffic came from Hacker News and a Substack saw four rows of zeroes and none
         of its real traffic.
         Keys must match offsite_service.PLATFORM_LABELS exactly — 'X (Twitter)' never matched
         the 'X / Twitter' the service emits, so that row silently fell back to grey. */
      const socColors = { 'LinkedIn': '#0a66c2', 'Reddit': '#ff4500', 'YouTube': '#dc2626', 'X / Twitter': '#0f172a', 'Facebook': '#1877f2', 'Instagram': '#c13584' };
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
        badge: (r.platform || '?').slice(0, 1).toUpperCase(),
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
      /* "Links driving traffic" vs "links only". Both facts were already in every row — the
         distinction was just a 0 in the sessions column, which reads as a rounding artefact
         rather than as the two different things a backlink can be. The counts are over EVERY
         linking domain, not the 20 rows shown, so they answer the same question as the
         "Referring domains" KPI directly above. */
      const split = data.referrerSplit || { total: 0, driving: 0, linkOnly: 0 };
      off.splitLabel = split.total
        ? (this.fmt(split.driving) + ' driving traffic · ' + this.fmt(split.linkOnly) + ' links only')
        : '';
      off.hasSplit = !!split.total;
      const drivingBadge = { fontSize: '10px', fontWeight: 600, color: '#047857', background: '#ecfdf5', padding: '2px 7px', borderRadius: '9999px', whiteSpace: 'nowrap' };
      const linkOnlyBadge = { fontSize: '10px', fontWeight: 600, color: '#64748b', background: '#f1f5f9', padding: '2px 7px', borderRadius: '9999px', whiteSpace: 'nowrap' };
      off.referrers = refRows.map(r => ({
        domain: r.domain, rank: r.authorityScore,
        kindLabel: r.drivesTraffic ? 'driving traffic' : 'link only',
        kindStyle: r.drivesTraffic ? drivingBadge : linkOnlyBadge,
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

