    /* ============ AI OPTIMIZATION ============ */
    if (tab === 'ai') {
      vals.showAi = true;
      const d = data;
      const llm = d.llmPlatforms;
      /* 4 decimals under half a cent: a real $0.0008 check rendered "$0.000", which reads as
         free — the one thing a price label must never do here. */
      const money3 = c => '$' + Number(c || 0).toFixed(c > 0 && c < 0.005 ? 4 : c > 0 && c < 0.1 ? 3 : 2);
      /* d.costs.model is the REAL mean cost of one check, and it is null until a check has
         actually been billed. Multiplying null gave NaN, which money3 swallowed via
         Number(c || 0) and printed as "$0.00" — a paid action advertising itself as free on
         exactly the projects that have never paid for one. Unknown is now said out loud. */
      const perCheck = (d.costs && d.costs.model != null) ? d.costs.model : null;
      const costOf = n => perCheck == null ? 'cost unknown' : '~' + money3(perCheck * n);
      /* cfg.models is null on a prompt whose tracked_models was wiped; an unguarded read here
         blanked the ENTIRE SPA render (§10). One accessor, guarded once. */
      const modelsOf = pr => (pr.cfg && pr.cfg.models) || [];
      const unrunOf = pr => pr.unrun || [];
      /* The label must state the plan the server would actually execute — not the price of
         the whole grid, which is what every Run button used to quote while the run itself
         re-billed every cell. */
      const planLabel = (verb, n) => n === 0
        ? 'Everything is up to date'
        : verb + ' ' + n + ' unrun check' + (n === 1 ? '' : 's') + ' · ' + costOf(n);
      const inputStyle = { padding: '9px 12px', fontSize: '13px', border: '1px solid #cbd5e1', borderRadius: '8px', background: 'white', color: '#0f172a', width: '100%' };
      const redBtn = { display: 'inline-flex', alignItems: 'center', gap: '6px', cursor: 'pointer', padding: '7px 14px', fontSize: '12.5px', fontWeight: 600, color: '#dc2626', border: '1px solid #fecaca', borderRadius: '8px', background: '#fff5f5', whiteSpace: 'nowrap' };
      const priBtn = { display: 'inline-flex', alignItems: 'center', gap: '8px', cursor: 'pointer', padding: '9px 18px', fontSize: '13px', fontWeight: 600, color: 'white', background: '#4f46e5', borderRadius: '8px' };
      const ghostBtn = { display: 'inline-flex', alignItems: 'center', gap: '6px', cursor: 'pointer', padding: '8px 14px', fontSize: '13px', fontWeight: 600, color: '#334155', border: '1px solid #cbd5e1', borderRadius: '8px', background: 'white' };
      const chip = (bg, fg) => ({ fontSize: '10px', fontWeight: 700, background: bg, color: fg, padding: '1px 7px', borderRadius: '4px', flexShrink: 0 });
      const CATC = { recommendation: ['#d1fae5', '#047857'], comparison: ['#dbeafe', '#1d4ed8'], cost: ['#ffedd5', '#c2410c'], question: ['#f3e8ff', '#7e22ce'], local: ['#fef3c7', '#b45309'] };
      const catChip = c => { const m = CATC[c] || CATC.question; return { label: c, style: Object.assign(chip(m[0], m[1]), { textTransform: 'capitalize' }) }; };
      const verdictChip = v => v === 'cited' ? { label: 'Cited', style: chip('#d1fae5', '#047857') } : v === 'mentioned' ? { label: 'Mentioned', style: chip('#dbeafe', '#1d4ed8') } : { label: 'Absent', style: chip('#fee2e2', '#b91c1c') };
      const toggle2 = on => ({
        track: { width: '40px', height: '22px', borderRadius: '9999px', background: on ? '#4f46e5' : '#cbd5e1', position: 'relative', cursor: 'pointer', flexShrink: 0 },
        knob: { position: 'absolute', top: '2px', left: on ? '20px' : '2px', width: '18px', height: '18px', borderRadius: '9999px', background: 'white', transition: 'left 0.15s ease' }
      });
      const aiv = { domain: project.domain, showWizard: false, showMain: false };
      /* THE identity list — the exact needles the backend computed the verdict from
         (brand + aliases + this project's own normalised domain). The Inspector used to test
         "is this citation ours?" a THIRD way, hostname-matching project.domain, so it could
         paint a "You" chip on a citation sitting directly under a verdict saying you are not
         mentioned. Verdict, grid and chips now read one list. */
      const identity = (d.targets && d.targets.identity) || [];
      const isOurs = host => !!host && identity.some(n => host === n || host.endsWith('.' + n));

      /* shared target-editor drafts (wizard step 1-2 + edit-targets modal) */
      const wizBrand = s.aiWizBrand != null ? s.aiWizBrand : d.targets.brand;
      const wizAliases = s.aiWizAliases != null ? s.aiWizAliases : d.targets.aliases.join(', ');
      const comps = s.aiWizComps || d.targets.competitors;
      aiv.wizBrand = wizBrand;
      aiv.wizAliases = wizAliases;
      aiv.wizBrandSet = e => this.setState({ aiWizBrand: e.target.value });
      aiv.wizAliasesSet = e => this.setState({ aiWizAliases: e.target.value });
      aiv.wizComps = comps.map(c => ({ domain: c, remove: () => this.setState({ aiWizComps: comps.filter(x => x !== c) }) }));
      aiv.wizCompInput = s.aiWizCompInput;
      aiv.wizCompSet = e => this.setState({ aiWizCompInput: e.target.value });
      const compAdd = () => {
        const v = this.state.aiWizCompInput.trim().toLowerCase().replace(/^https?:\/\//, '').replace(/\/.*$/, '');
        if (!v || comps.includes(v) || comps.length >= 9) return;
        this.setState({ aiWizComps: comps.concat([v]), aiWizCompInput: '' });
      };
      aiv.wizCompAdd = compAdd;
      aiv.wizCompKey = e => { if (e.key === 'Enter') compAdd(); };
      aiv.wizCompNote = comps.length + ' of 9 competitors — you + competitors map to the 10 API target entities';

      /* ---------- FIRST-RUN WIZARD ---------- */
      if (!d.setupDone) {
        aiv.showWizard = true;
        const step = s.aiWiz || 1;
        const names = ['Your brand', 'Competitors', 'Starter prompts'];
        aiv.wizSteps = names.map((nm, i2) => {
          const n = i2 + 1;
          const on = n === step, done = n < step;
          return {
            label: n + '. ' + nm,
            style: { display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 14px', borderRadius: '999px', fontSize: '12.5px', fontWeight: 600, background: on ? '#eef2ff' : 'transparent', color: on ? '#4338ca' : done ? '#059669' : '#94a3b8', border: '1px solid ' + (on ? '#c7d2fe' : 'transparent') }
          };
        });
        aiv.wizShow1 = step === 1; aiv.wizShow2 = step === 2; aiv.wizShow3 = step === 3;
        const selArr = s.aiWizSel || d.suggestions.slice(0, 6).map(x => x.id);
        aiv.wizSugs = d.suggestions.map(x => {
          const on = selArr.includes(x.id);
          const cc = catChip(x.category);
          return {
            text: x.text, catLabel: cc.label, catStyle: cc.style, vol: this.fmt(x.aiVolume),
            rowStyle: { display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 14px', borderRadius: '8px', border: '1px solid ' + (on ? '#c7d2fe' : '#e2e8f0'), background: on ? '#f5f7ff' : 'white', cursor: 'pointer' },
            checkStyle: { width: '15px', height: '15px', borderRadius: '4px', border: '1.5px solid ' + (on ? '#4f46e5' : '#cbd5e1'), background: on ? '#4f46e5' : 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, color: 'white', fontSize: '10px', fontWeight: 700 },
            checked: on,
            toggle: () => this.setState({ aiWizSel: on ? selArr.filter(i2 => i2 !== x.id) : selArr.concat([x.id]) })
          };
        });
        aiv.wizCustom = s.aiWizCustom;
        aiv.wizCustomSet = e => this.setState({ aiWizCustom: e.target.value });
        const customN = (s.aiWizCustom || '').split('\n').map(x => x.trim()).filter(Boolean).length;
        const totalN = selArr.length + customN;
        aiv.wizNext = () => this.setState({ aiWiz: step + 1 });
        aiv.wizBack = () => this.setState({ aiWiz: step - 1 });
        aiv.wizBackShown = step > 1;
        aiv.wizFinish = () => this.aiFinishSetup(d);
        aiv.wizFinishLabel = s.aiWizBusy ? 'Setting up…' : 'Finish setup — track ' + totalN + ' prompt' + (totalN === 1 ? '' : 's');
        aiv.wizWeekly = perCheck == null
          ? 'Weekly schedule across 4 LLMs — per-check cost unknown until the first run'
          : 'Weekly schedule ≈ ' + money3(totalN * 4 * perCheck * 4.3) + '/mo across 4 LLMs';
        aiv.inputStyle = inputStyle;
        vals.aiv = aiv;
      }

      /* ---------- MAIN ---------- */
      if (d.setupDone) {
        aiv.showMain = true;
        aiv.inputStyle = inputStyle;
        const kpi = d.kpis;
        const prompts = d.prompts;
        const listName = lid => (d.lists.find(l => l.id === lid) || { name: '—' }).name;
        const overCap = d.budget.spent / d.budget.cap;
        aiv.budgetLabel = 'AI spend ' + this.money(d.budget.spent) + ' of ' + this.money(d.budget.cap) + ' cap';
        aiv.budgetStyle = { fontSize: '12px', fontWeight: 600, padding: '4px 10px', borderRadius: '6px', background: overCap >= 0.8 ? '#fee2e2' : '#f1f5f9', color: overCap >= 0.8 ? '#b91c1c' : '#475569' };
        aiv.nextRunLabel = d.next_run ? ('Runs weekly · next ' + d.next_run) : 'Runs weekly · not yet scheduled';
        /* THE RUN IS SERVER STATE. `d.run` is the task the worker process updates, so a run
           in flight survives switching tabs, reloading the page and the death of the worker
           itself. The old `s.aiRunning` was a client-side flag cleared only when the (8-15
           minute) POST resolved — when the proxy killed that request the flag was stuck true
           and EVERY Run button silently stopped working for the rest of the session. */
        const runState = d.run || { state: 'idle' };
        const running = runState.state === 'running';
        aiv.running = running;
        const allUnrun = prompts.reduce((n, pr) => n + unrunOf(pr).length, 0);
        const allCells = prompts.reduce((n, pr) => n + modelsOf(pr).length, 0);
        const doneOf = runState.completed || 0;
        const totalOf = runState.total || 0;
        aiv.runBanner = running
          ? 'Running checks — ' + doneOf + ' of ' + totalOf + ' done'
            + (runState.current ? ' · now asking about “' + runState.current + '”' : '')
            + '. This keeps going if you switch tabs or reload.'
          : '';
        aiv.runProgressStyle = {
          height: '4px', borderRadius: '999px', background: '#1d4ed8',
          width: (totalOf ? Math.round((doneOf / totalOf) * 100) : 0) + '%'
        };
        /* A finished or dead run must say so once, rather than leaving the page looking as
           though the click never registered — the third of the three failures this replaced. */
        aiv.runFailed = runState.state === 'error';
        aiv.runFailedMsg = runState.error || '';
        aiv.runNote = (!running && runState.state === 'done' && runState.detail) ? runState.detail : '';

        aiv.runAllLabel = running ? 'Running…' : planLabel('Run', allUnrun);
        aiv.runAllStyle = (running || allUnrun === 0)
          ? Object.assign({}, redBtn, { background: '#fef2f2', color: '#fca5a5', borderColor: '#fee2e2', cursor: 'default' })
          : redBtn;
        aiv.runAll = () => { if (allUnrun && !running) this.aiRun({}); };
        /* The separate, explicitly-labelled paid action: everything else skips what has
           already been answered, and this is the only way to ask for fresh answers. */
        aiv.rerunLabel = running ? 'Running…'
          : 'Re-run (fresh answers) · ' + costOf(allCells);
        aiv.rerunStyle = running
          ? Object.assign({}, ghostBtn, { color: '#cbd5e1', cursor: 'default' })
          : ghostBtn;
        aiv.rerunAll = () => { if (allCells && !running) this.aiRun({ force: true }); };
        aiv.hasPrompts = prompts.length > 0;

        /* Poll while the run is in flight. A self-terminating chain, not an interval: each
           render schedules exactly one deferred reload, and once `running` goes false nothing
           schedules another. This is also what restores live progress after a page reload —
           the state comes from the server, so there is nothing client-side to restore. */
        if (running && !this._aiPoll) {
          this._aiPoll = setTimeout(() => {
            this._aiPoll = null;
            if (this._alive) this.aiReload();
          }, 2000);
        }

        const sub2 = s.aiSub;
        const goSub = v => { this.setState({ aiSub: v }); this.pushNav({ aiSub: v }); };
        const subBase2 = { padding: '10px 16px', fontSize: '13px', fontWeight: 600, cursor: 'pointer', color: '#64748b', borderBottom: '2px solid transparent', marginBottom: '-1px' };
        aiv.subTabs = [['visibility', 'AI Visibility'], ['prompts', 'Prompts (' + prompts.length + ')'], ['aikw', 'AI Keywords (' + d.aiKeywords.length + ')'], ['inspector', 'Answer Inspector'], ['history', 'History (' + d.history.length + ')']].map(t => ({
          label: t[1],
          style: sub2 === t[0] ? Object.assign({}, subBase2, { color: '#4f46e5', borderBottom: '2px solid #4f46e5' }) : subBase2,
          click: () => goSub(t[0])
        }));
        aiv.showVisibility = sub2 === 'visibility'; aiv.showPrompts = sub2 === 'prompts';
        aiv.showAikw = sub2 === 'aikw'; aiv.showInspector = sub2 === 'inspector'; aiv.showHistory = sub2 === 'history';

        /* targets card + edit modal */
        aiv.tgBrand = d.targets.brand;
        aiv.tgAliases = d.targets.aliases;
        aiv.tgComps = d.targets.competitors;
        aiv.tgEdit = () => this.setState({ aiTgOpen: true, aiWizBrand: d.targets.brand, aiWizAliases: d.targets.aliases.join(', '), aiWizComps: d.targets.competitors.slice(), aiWizCompInput: '' });
        aiv.tgOpen = s.aiTgOpen;
        aiv.tgClose = () => this.setState({ aiTgOpen: false, aiWizBrand: null, aiWizAliases: null, aiWizComps: null, aiWizCompInput: '' });
        aiv.tgSave = () => this.aiSaveTargets(d);
        /* Free corrective action — see App#aiRescan. Offered next to Edit targets because
           that is where a detection mistake gets fixed, and re-scanning is what makes the fix
           take effect on answers already bought. */
        aiv.rescanLabel = s.aiRescanning ? 'Re-scanning…' : '↻ Re-scan answers (free)';
        aiv.rescanStyle = { cursor: s.aiRescanning ? 'default' : 'pointer', padding: '7px 14px', fontSize: '12.5px', fontWeight: 600, color: s.aiRescanning ? '#94a3b8' : '#334155', border: '1px solid #cbd5e1', borderRadius: '8px', background: 'white', whiteSpace: 'nowrap' };
        aiv.rescan = () => this.aiRescan();

        if (sub2 === 'visibility') {
          const sov = d.sov;
          // Each empty case has its own truth; none of them is a zero.
          aiv.visSetup = d.visibilityState === 'setup';
          aiv.visNoComps = d.visibilityState === 'no_competitors';
          aiv.visNoPages = !aiv.visSetup && d.topPages.length === 0;
          aiv.visOk = !aiv.visSetup && !aiv.visNoComps;
          aiv.visSetupMsg = 'No AI visibility data yet — press Refresh to take the first weekly snapshot.';
          aiv.visNoCompsMsg = 'Add competitors under Targets to see share of voice.';
          aiv.visNoPagesMsg = 'AI has not cited any of your pages yet.';
          const maxSov = Math.max.apply(null, sov.rows.map(r => r.sov)) || 1;
          aiv.sovPct = sov.you + '%';
          // delta is null until a second weekly snapshot exists. Printing "+0 pts vs. last
          // week" would assert we measured last week when we did not.
          const hasDelta = sov.delta !== null && sov.delta !== undefined;
          aiv.sovDelta = hasDelta
            ? (sov.delta >= 0 ? '▲ +' : '▼ ') + Math.abs(sov.delta) + ' pts vs. last week'
            : 'first measurement — no comparison yet';
          aiv.sovDeltaStyle = {
            fontSize: '12px', fontWeight: 600, padding: '3px 8px', borderRadius: '4px',
            background: !hasDelta ? '#f1f5f9' : (sov.delta >= 0 ? '#ecfdf5' : '#fff1f2'),
            color: !hasDelta ? '#64748b' : (sov.delta >= 0 ? '#059669' : '#e11d48')
          };
          aiv.sovRows = sov.rows.map((r, i2) => ({
            rank: '#' + (i2 + 1), domain: r.domain, sovFmt: r.sov + '%',
            mentionsFmt: this.fmt(r.mentions) + ' mentions',
            nameStyle: { fontSize: '13px', fontWeight: r.isYou ? 700 : 500, color: r.isYou ? '#4338ca' : '#334155', flex: 1, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' },
            barStyle: { height: '8px', borderRadius: '4px', width: Math.max(3, Math.round((r.sov / maxSov) * 100)) + '%', background: r.isYou ? '#4f46e5' : '#cbd5e1' },
            youChip: r.isYou
          }));
          aiv.kpis = [
            { label: 'Brand mentions · 30d', value: this.fmt(kpi.mentions), sub: 'AI Overviews + ChatGPT' },
            { label: 'AI impressions', value: this.fmt(kpi.impressions), sub: 'est. answer views citing you' },
            { label: 'Cited pages', value: kpi.cited_pages, sub: 'of your URLs used as sources' },
            { label: 'Prompt coverage', value: kpi.prompt_coverage.cited + ' of ' + kpi.prompt_coverage.total, sub: 'tracked prompts citing you' }
          ];
          const chipBase3 = { display: 'inline-flex', alignItems: 'center', gap: '7px', padding: '5px 11px', fontSize: '12px', fontWeight: 500, borderRadius: '999px', cursor: 'pointer', color: '#64748b', border: '1px solid #e2e8f0', background: 'white' };
          aiv.platToggles = d.mentionPlatforms.map(pl2 => {
            const on = !!s.aiPlat[pl2.id];
            return {
              label: pl2.name,
              dot: { width: '8px', height: '8px', borderRadius: '50%', background: on ? pl2.color : '#cbd5e1', flexShrink: 0 },
              style: on ? Object.assign({}, chipBase3, { borderColor: pl2.color, color: '#0f172a' }) : chipBase3,
              click: () => this.setState(st => ({ aiPlat: Object.assign({}, st.aiPlat, { [pl2.id]: !st.aiPlat[pl2.id] }) }))
            };
          });
          const allVals = [];
          d.mentionPlatforms.forEach(pl2 => { if (s.aiPlat[pl2.id]) d.trend.forEach(pt2 => allVals.push(pt2[pl2.id])); });
          const maxV = Math.max(1, ...allVals);
          aiv.trendLines = d.mentionPlatforms.filter(pl2 => s.aiPlat[pl2.id]).map(pl2 => {
            const pts = d.trend.map((pt2, k) => {
              const x = (k / (d.trend.length - 1)) * 590 + 5;
              const y = 190 - (pt2[pl2.id] / maxV) * 175;
              return x.toFixed(1) + ',' + y.toFixed(1);
            }).join(' ');
            return { pts, color: pl2.color };
          });
          aiv.trendFrom = d.trend.length ? d.trend[0].date : '';
          aiv.trendTo = d.trend.length ? d.trend[d.trend.length - 1].date : '';
          aiv.topPages = d.topPages.map(pg2 => ({
            url: pg2.url, mentions: pg2.mentions, imprFmt: this.fmt(pg2.impressions),
            platforms: pg2.platforms.join(' · ') || '—'
          }));
          const maxShare = Math.max.apply(null, d.topDomains.map(dm => dm.share)) || 1;
          aiv.topDomains = d.topDomains.map((dm, i2) => ({
            rank: i2 + 1, domain: dm.domain, shareFmt: dm.share + '%', mentionsFmt: this.fmt(dm.mentions),
            nameStyle: { fontSize: '13px', fontWeight: dm.isYou ? 700 : 500, color: dm.isYou ? '#4338ca' : '#334155', flex: 1, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' },
            barStyle: { height: '7px', borderRadius: '4px', width: Math.max(3, Math.round((dm.share / maxShare) * 100)) + '%', background: dm.isYou ? '#4f46e5' : dm.isComp ? '#f59e0b' : '#cbd5e1' },
            tagLabel: dm.isYou ? 'You' : dm.isComp ? 'Competitor' : '',
            tagStyle: dm.isYou ? chip('#eef2ff', '#4338ca') : chip('#fef3c7', '#b45309')
          }));
        }

        if (sub2 === 'prompts') {
          /* --- prompt explorer --- */
          aiv.expQ = s.aiExpQ;
          aiv.expSet = e => this.setState({ aiExpQ: e.target.value });
          aiv.expKey = e => { if (e.key === 'Enter') this.aiExplore(); };
          aiv.expRun = () => this.aiExplore();
          aiv.expLabel = s.aiExploring ? 'Exploring…' : 'Explore prompts';
          aiv.expBtnStyle = priBtn;
          aiv.hasExp = !!(s.aiExp && s.aiExp.rows);
          if (aiv.hasExp) {
            const selSet = new Set(s.aiExpSel);
            const rows2 = s.aiExp.rows;
            const selTexts = () => rows2.filter(r => selSet.has(r.text) && !r.tracked).map(r => r.text);
            aiv.expMeta = rows2.length + ' prompt ideas · ' + s.aiExp.location + ' · est. cost ' + this.money(s.aiExp.cost);
            aiv.expClear = () => this.setState({ aiExp: null, aiExpSel: [], aiExpAddOpen: false });
            aiv.expSelCount = s.aiExpSel.length;
            aiv.expAnySel = s.aiExpSel.length > 0;
            aiv.expAddOpen = s.aiExpAddOpen;
            aiv.expAddToggle = () => this.setState(st => ({ aiExpAddOpen: !st.aiExpAddOpen }));
            aiv.expAddBtnStyle = Object.assign({}, priBtn, { padding: '7px 14px', fontSize: '12.5px', opacity: s.aiExpSel.length ? 1 : 0.5, cursor: s.aiExpSel.length ? 'pointer' : 'default' });
            aiv.expLists = d.lists.map(l => ({
              name: l.name,
              onAdd: () => this.aiAddPrompts(selTexts(), l.id, () => this.setState({ aiExpSel: [], aiExpAddOpen: false }))
            }));
            aiv.expNewName = s.aiNewPlName;
            aiv.expNewSet = e => this.setState({ aiNewPlName: e.target.value });
            const expCreateAdd = () => {
              const nm = this.state.aiNewPlName.trim();
              const texts = selTexts();
              if (!nm || !texts.length) return;
              /* Only list CREATION can reject here -- aiAddPrompts handles and reports its own
                 failure and resolves undefined, so there is no double toast. Staying silent
                 would leave the user staring at an unchanged screen after naming a new list. */
              this.aiPost('lists', { op: 'create', name: nm })
                .then(r => this.aiAddPrompts(texts, r.id, () => this.setState({ aiExpSel: [], aiExpAddOpen: false, aiNewPlName: '', aiListFilter: r.id })))
                .catch(err => { if (this._alive) this.notify(this.errText(err, 'Could not create the prompt list')); });
            };
            aiv.expNewCreate = expCreateAdd;
            aiv.expNewKey = e => { if (e.key === 'Enter') expCreateAdd(); };
            aiv.expRows = rows2.map(r => {
              const on = selSet.has(r.text);
              const cc = catChip(r.category);
              return {
                text: r.text, volFmt: this.fmt(r.aiVolume), tracked: r.tracked,
                catLabel: cc.label, catStyle: cc.style,
                rowBg: on ? '#f5f7ff' : 'white',
                checkStyle: { width: '15px', height: '15px', borderRadius: '4px', border: '1.5px solid ' + (on ? '#4f46e5' : '#cbd5e1'), background: on ? '#4f46e5' : 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, color: 'white', fontSize: '10px', fontWeight: 700 },
                checked: on,
                toggle: () => { if (r.tracked) return; this.setState(st => ({ aiExpSel: on ? st.aiExpSel.filter(x => x !== r.text) : st.aiExpSel.concat([r.text]) })); }
              };
            });
          }

          /* --- list chips + manage --- */
          const counts = { all: prompts.length };
          d.lists.forEach(l => { counts[l.id] = prompts.filter(pr => pr.listId === l.id).length; });
          const fBase = { padding: '5px 12px', fontSize: '12px', fontWeight: 500, borderRadius: '999px', cursor: 'pointer', color: '#64748b', border: '1px solid #e2e8f0', background: 'white' };
          const fActive = Object.assign({}, fBase, { borderColor: '#4f46e5', color: '#4f46e5', background: '#eef2ff', fontWeight: 600 });
          aiv.listChips = [{ id: 'all', name: 'All' }].concat(d.lists).map(l => ({
            label: l.name + ' (' + counts[l.id] + ')',
            style: s.aiListFilter === l.id ? fActive : fBase,
            click: () => this.setState({ aiListFilter: l.id })
          }));
          aiv.listsOpen = s.aiListsOpen;
          aiv.listsToggle = () => this.setState(st => ({ aiListsOpen: !st.aiListsOpen }));
          aiv.manageRows = d.lists.map(l => ({
            name: l.name, count: counts[l.id] + ' prompt' + (counts[l.id] === 1 ? '' : 's'),
            rename: e => { const nm = e.target.value.trim(); if (nm && nm !== l.name) this.aiListOp('rename', l.id, nm); },
            del: () => this.aiListOp('delete', l.id, null, () => this.setState({ aiListFilter: 'all' })),
            canDel: d.lists.length > 1
          }));
          aiv.newPlName = s.aiNewPlName;
          aiv.newPlSet = e => this.setState({ aiNewPlName: e.target.value });
          const createList = () => { const nm = this.state.aiNewPlName.trim(); if (nm) this.aiListOp('create', null, nm, () => this.setState({ aiNewPlName: '' })); };
          aiv.newPlCreate = createList;
          aiv.newPlKey = e => { if (e.key === 'Enter') createList(); };

          /* --- composer --- */
          aiv.composerOpen = s.aiComposerOpen;
          aiv.composerShow = () => this.setState({ aiComposerOpen: true, aiComposerList: this.state.aiComposerList || (d.lists[0] || {}).id });
          aiv.composerHide = () => this.setState({ aiComposerOpen: false });
          aiv.compText = s.aiComposerText;
          aiv.compTextSet = e => this.setState({ aiComposerText: e.target.value });
          aiv.compList = s.aiComposerList || (d.lists[0] || {}).id;
          aiv.compListSet = e => this.setState({ aiComposerList: e.target.value });
          aiv.compListOptions = d.lists.map(l => ({ value: l.id, label: l.name }));
          aiv.compSugs = d.suggestions.slice(0, 5).map(x => ({
            text: x.text,
            add: () => this.setState(st => ({ aiComposerText: (st.aiComposerText ? st.aiComposerText.replace(/\n?$/, '\n') : '') + x.text }))
          }));
          const compLines = (s.aiComposerText || '').split('\n').map(x => x.trim()).filter(Boolean);
          aiv.compCount = compLines.length;
          aiv.compAddLabel = 'Add ' + compLines.length + ' prompt' + (compLines.length === 1 ? '' : 's');
          aiv.compAddStyle = Object.assign({}, priBtn, { opacity: compLines.length ? 1 : 0.5, cursor: compLines.length ? 'pointer' : 'default' });
          aiv.compAdd = () => { if (compLines.length) this.aiAddPrompts(compLines, this.state.aiComposerList || (d.lists[0] || {}).id, () => this.setState({ aiComposerOpen: false, aiComposerText: '' })); };

          /* --- prompt table --- */
          aiv.noPrompts = prompts.length === 0;
          aiv.platNames = llm.map(pl2 => pl2.name);
          aiv.promptGridCols = '28px minmax(220px, 1.6fr) repeat(' + llm.length + ', minmax(88px, 1fr)) 230px';
          /* Every state a check can really be in gets its own label. A run whose answer simply
             did not mention the brand used to render the same "—" as a never-run cell, so a
             completed (and paid-for) check looked like nothing had happened. */
          const pill = (bg, fg, w) => ({ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', minWidth: '44px', height: '24px', padding: '0 8px', borderRadius: '4px', fontSize: '12px', fontWeight: w || 600, background: bg, color: fg });
          const cell = (tracked, r) => {
            if (!tracked) return { label: 'off', style: Object.assign(chip('#f8fafc', '#cbd5e1'), { fontSize: '11px', fontWeight: 500 }) };
            if (!r || !r.state) return { label: 'Not run', style: pill('#f8fafc', '#94a3b8', 500) };
            if (r.state === 'not_connected') return { label: 'No key', style: pill('#fef3c7', '#b45309') };
            if (r.state === 'error') return { label: 'Error', style: pill('#fee2e2', '#b91c1c') };
            if (r.cited) return { label: 'Cited #' + r.position, style: pill('#d1fae5', '#047857', 700) };
            if (r.mentioned) return { label: 'Mentioned', style: pill('#dbeafe', '#1d4ed8') };
            return { label: 'Not mentioned', style: pill('#fee2e2', '#b91c1c') };
          };
          const visPrompts = prompts.filter(pr => s.aiListFilter === 'all' || pr.listId === s.aiListFilter);
          aiv.promptEmptyFiltered = prompts.length > 0 && visPrompts.length === 0;

          /* --- select + bulk remove --- */
          const promptSel = s.aiPromptSel || [];
          const promptSelSet = new Set(promptSel);
          const visPromptSel = visPrompts.filter(pr => promptSelSet.has(pr.id));
          const promptAllOn = visPrompts.length > 0 && visPrompts.every(pr => promptSelSet.has(pr.id));
          aiv.promptAllChecked = promptAllOn;
          aiv.promptAllCheckStyle = { width: '15px', height: '15px', borderRadius: '4px', border: '1.5px solid ' + (promptAllOn ? '#4f46e5' : '#cbd5e1'), background: promptAllOn ? '#4f46e5' : 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, color: 'white', fontSize: '10px', fontWeight: 700, cursor: 'pointer' };
          aiv.promptToggleAll = () => this.setState({ aiPromptSel: promptAllOn ? [] : visPrompts.map(pr => pr.id) });
          aiv.promptAnySel = visPromptSel.length > 0;
          aiv.promptSelCount = visPromptSel.length + ' selected';
          aiv.promptClearSel = () => this.setState({ aiPromptSel: [] });
          aiv.promptRemoveSel = () => this.aiRemovePrompts(visPromptSel.map(pr => pr.id));
          const selUnrun = visPromptSel.reduce((n, pr) => n + unrunOf(pr).length, 0);
          aiv.promptRunSelLabel = running ? 'Running…' : planLabel('Run', selUnrun);
          aiv.promptRunSelStyle = (running || selUnrun === 0)
            ? Object.assign({}, redBtn, { background: '#fef2f2', color: '#fca5a5', borderColor: '#fee2e2', cursor: 'default' })
            : redBtn;
          aiv.promptRunSel = () => { if (!running && selUnrun) this.aiRun({ promptIds: visPromptSel.map(pr => pr.id) }); };
          aiv.promptRerunSelLabel = running ? 'Running…'
            : 'Re-run · ' + costOf(visPromptSel.reduce((n, pr) => n + modelsOf(pr).length, 0));
          aiv.promptRerunSel = () => { if (!running && visPromptSel.length) this.aiRun({ promptIds: visPromptSel.map(pr => pr.id), force: true }); };

          /* Row click opens the prompt in the Answer Inspector — showing the answer that was
             ALREADY paid for when one exists. The old "Inspect answer" button fired a fresh
             paid check on every click; a stored answer must never cost money to re-read.
             `aiInspEntry: false` (not null) is the explicit "this prompt has never been run"
             sentinel — null/undefined mean "no selection" and fall back to the latest history
             entry, which would show some OTHER prompt's answer here. */
          /* `find(e => e.promptId === pr.id)` alone returns the FIRST match, which after a run
             is whichever engine happened to be checked LAST — not the cell the user clicked.
             Clicking a cell now opens that cell's platform; clicking the row's "Open answer"
             falls back to the newest answer for the prompt, whichever engine it came from. */
          const openInspector = (pr, platformId) => {
            const forCell = platformId
              ? d.history.find(e => e.promptId === pr.id && e.platform === platformId)
              : null;
            const stored2 = forCell || (platformId ? null : d.history.find(e => e.promptId === pr.id)) || null;
            this.setState({ aiInspEntry: stored2 || false, aiInspQ: pr.text, aiInspPromptId: pr.id, aiInspPlat: platformId || null, aiSub: 'inspector' });
            this.pushNav({ aiSub: 'inspector' });
          };
          aiv.promptRows = visPrompts.map(pr => {
            const prSelOn = promptSelSet.has(pr.id);
            /* `results` is {} until the prompt has actually been run — build_ai_response says so
               explicitly. A TRACKED model routinely has no result entry, so every read through
               pr.results[id] stays guarded (an unguarded read here once blanked the whole SPA). */
            const res = pl2 => pr.results[pl2.id] || null;
            const metaParts = [];
            const flt2 = d.lists.find(l => l.id === pr.listId);
            if (flt2) metaParts.push(flt2.name);
            metaParts.push(pr.cfg.models.length + ' model' + (pr.cfg.models.length === 1 ? '' : 's'));
            metaParts.push(pr.cfg.cadence);
            if (pr.cfg.city || pr.cfg.country) metaParts.push(pr.cfg.city || pr.cfg.country);
            metaParts.push(pr.lastRun ? 'last run ' + String(pr.lastRun).replace('T', ' ').slice(0, 16) : 'not run yet');
            /* Tracked competitors named in this prompt's stored answers (union across models) —
               the per-answer detail lives in the Inspector, this is the at-a-glance flag. */
            const compSeen = {};
            llm.forEach(pl2 => { const r2 = res(pl2); ((r2 && r2.competitors) || []).forEach(c2 => { compSeen[c2.name] = 1; }); });
            const compNames = Object.keys(compSeen);
            if (compNames.length) metaParts.push('⚠ competitors in answers: ' + compNames.join(', '));
            return {
              text: pr.text,
              meta: metaParts.join(' · '),
              cells: llm.map(pl2 => Object.assign(
                cell(modelsOf(pr).includes(pl2.id), res(pl2)),
                { open: e => { e.stopPropagation(); openInspector(pr, pl2.id); },
                  title: 'Open ' + pl2.name + '’s answer to this prompt' })),
              checked: prSelOn,
              checkStyle: { width: '15px', height: '15px', borderRadius: '4px', border: '1.5px solid ' + (prSelOn ? '#4f46e5' : '#cbd5e1'), background: prSelOn ? '#4f46e5' : 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, color: 'white', fontSize: '10px', fontWeight: 700, cursor: 'pointer' },
              toggleSel: e => { e.stopPropagation(); this.setState(st => ({ aiPromptSel: prSelOn ? (st.aiPromptSel || []).filter(x => x !== pr.id) : (st.aiPromptSel || []).concat([pr.id]) })); },
              openIns: () => openInspector(pr),
              runLabel: running ? 'Running…'
                : (unrunOf(pr).length === 0 ? 'Up to date'
                  : 'Run ' + unrunOf(pr).length + ' · ' + costOf(unrunOf(pr).length)),
              runStyle: (running || unrunOf(pr).length === 0)
                ? Object.assign({}, redBtn, { background: '#fef2f2', color: '#fca5a5', borderColor: '#fee2e2', cursor: 'default', padding: '6px 10px' })
                : Object.assign({}, redBtn, { padding: '6px 10px' }),
              run: e => { e.stopPropagation(); if (!running && unrunOf(pr).length) this.aiRun({ promptId: pr.id }); },
              rerunTitle: 'Re-run this prompt on every tracked engine · ' + costOf(modelsOf(pr).length),
              rerun: e => { e.stopPropagation(); if (!running) this.aiRun({ promptId: pr.id, force: true }); },
              cfgOpen: e => { e.stopPropagation(); this.setState({ aiCfgOpen: pr.id, aiCfgDraft: Object.assign({}, pr.cfg, { models: pr.cfg.models.slice(), listId: pr.listId, text: pr.text }) }); },
              remove: e => { e.stopPropagation(); this.aiRemovePrompts([pr.id]); }
            };
          });
          const flt = d.lists.find(l => l.id === s.aiListFilter);
          if (flt) {
            const listUnrun = visPrompts.reduce((n, pr) => n + unrunOf(pr).length, 0);
            aiv.runListShown = visPrompts.length > 0;
            aiv.runListLabel = running ? 'Running…' : planLabel('Run "' + flt.name + '" —', listUnrun);
            aiv.runListStyle = (running || listUnrun === 0)
              ? Object.assign({}, redBtn, { background: '#fef2f2', color: '#fca5a5', borderColor: '#fee2e2', cursor: 'default' })
              : redBtn;
            aiv.runList = () => { if (!running && listUnrun) this.aiRun({ listId: flt.id }); };
          } else { aiv.runListShown = false; }

          /* --- config modal --- */
          const cfgPr = s.aiCfgOpen ? prompts.find(pr => pr.id === s.aiCfgOpen) : null;
          if (cfgPr && s.aiCfgDraft) {
            const dr = s.aiCfgDraft;
            const setDr = patch => this.setState(st => ({ aiCfgDraft: Object.assign({}, st.aiCfgDraft, patch) }));
            const tg = toggle2(!!dr.webSearch);
            aiv.cfg = {
              open: true, text: dr.text, textSet: e => setDr({ text: e.target.value }),
              models: llm.map(pl2 => {
                const on = dr.models.includes(pl2.id);
                return {
                  name: pl2.name,
                  style: { display: 'inline-flex', alignItems: 'center', gap: '7px', padding: '6px 12px', fontSize: '12.5px', fontWeight: 600, borderRadius: '8px', cursor: 'pointer', border: '1px solid ' + (on ? pl2.color : '#e2e8f0'), background: on ? '#f8fafc' : 'white', color: on ? '#0f172a' : '#94a3b8' },
                  dot: { width: '8px', height: '8px', borderRadius: '50%', background: on ? pl2.color : '#cbd5e1', flexShrink: 0 },
                  toggle: () => { const next = on ? dr.models.filter(m => m !== pl2.id) : dr.models.concat([pl2.id]); if (next.length) setDr({ models: next }); }
                };
              }),
              webTrack: tg.track, webKnob: tg.knob,
              webToggle: () => setDr({ webSearch: !dr.webSearch }),
              webNote: dr.webSearch ? 'Web search on — answers can cite live sources' : 'Web search off — no citations returned',
              country: dr.country, countrySet: e => setDr({ country: e.target.value }),
              city: dr.city, citySet: e => setDr({ city: e.target.value }),
              cadence: dr.cadence, cadenceSet: e => setDr({ cadence: e.target.value }),
              listId: dr.listId, listSet: e => setDr({ listId: e.target.value }),
              listOptions: d.lists.map(l => ({ value: l.id, label: l.name })),
              costNote: 'One run ≈ ' + money3(dr.models.length * d.costs.model) + ' · ' + (dr.cadence === 'manual' ? 'manual runs only' : dr.cadence + ' ≈ ' + money3(dr.models.length * d.costs.model * (dr.cadence === 'daily' ? 30 : 4.3)) + '/mo'),
              close: () => this.setState({ aiCfgOpen: null, aiCfgDraft: null }),
              save: () => this.aiPost('prompts-config', { id: cfgPr.id, cfg: { models: dr.models, webSearch: dr.webSearch, country: dr.country, city: dr.city, cadence: dr.cadence }, listId: dr.listId, text: dr.text })
                .then(() => { this.setState({ aiCfgOpen: null, aiCfgDraft: null }); this.aiReload(); this.notify('Prompt settings saved'); })
                .catch(err => { if (this._alive) this.notify(this.errText(err, 'Could not save prompt settings')); })
            };
          } else { aiv.cfg = { open: false }; }
        }

        if (sub2 === 'aikw') {
          const allRows = d.aiKeywords;
          const gaps = allRows.filter(r => r.gap);
          aiv.kwKpis = [
            { label: 'Total AI search volume', value: this.fmt(allRows.reduce((a2, r) => a2 + r.aiVolume, 0)), sub: 'est. monthly prompts on your keywords' },
            { label: 'AI-heavy keywords', value: allRows.filter(r => r.ratio >= 30).length, sub: 'AI volume ≥ 30% of Google volume' },
            { label: 'Visibility gaps', value: gaps.length, sub: 'high AI volume, zero mentions of you' }
          ];
          /* search + segment filters */
          const segDefs = [['all', 'All'], ['heavy', 'AI-heavy'], ['gap', 'Gaps'], ['mentioned', 'Mentioned']];
          const segCounts = {
            all: allRows.length,
            heavy: allRows.filter(r => r.ratio >= 30).length,
            gap: gaps.length,
            mentioned: allRows.filter(r => r.mentions > 0).length
          };
          const segBase = { padding: '5px 12px', fontSize: '12px', fontWeight: 500, borderRadius: '999px', cursor: 'pointer', color: '#64748b', border: '1px solid #e2e8f0', background: 'white' };
          const segActive = Object.assign({}, segBase, { borderColor: '#4f46e5', color: '#4f46e5', background: '#eef2ff', fontWeight: 600 });
          const seg = s.aiKwSeg || 'all';
          aiv.kwSegs = segDefs.map(sd => ({
            label: sd[1] + ' (' + segCounts[sd[0]] + ')',
            style: seg === sd[0] ? segActive : segBase,
            click: () => this.setState({ aiKwSeg: sd[0] })
          }));
          let rows = allRows.filter(r => seg === 'all' || (seg === 'heavy' && r.ratio >= 30) || (seg === 'gap' && r.gap) || (seg === 'mentioned' && r.mentions > 0));
          if (s.aiKwQ) { const q2 = s.aiKwQ.toLowerCase(); rows = rows.filter(r => r.kw.toLowerCase().includes(q2)); }
          aiv.kwQ = s.aiKwQ || '';
          aiv.kwQSet = e => this.setState({ aiKwQ: e.target.value });
          aiv.kwNoRows = rows.length === 0;
          aiv.kwCount = rows.length + ' of ' + allRows.length + ' keywords';
          /* selection */
          const kwSel = s.aiKwSel || [];
          const kwSelSet = new Set(kwSel);
          const visSel = rows.filter(r => kwSelSet.has(r.kw));
          const allOn = rows.length > 0 && rows.every(r => kwSelSet.has(r.kw));
          aiv.kwAllChecked = allOn;
          aiv.kwAllCheckStyle = { width: '15px', height: '15px', borderRadius: '4px', border: '1.5px solid ' + (allOn ? '#4f46e5' : '#cbd5e1'), background: allOn ? '#4f46e5' : 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, color: 'white', fontSize: '10px', fontWeight: 700, cursor: 'pointer' };
          aiv.kwToggleAll = () => this.setState({ aiKwSel: allOn ? [] : rows.map(r => r.kw) });
          aiv.kwAnySel = visSel.length > 0;
          aiv.kwSelCount = visSel.length + ' selected';
          aiv.kwClearSel = () => this.setState({ aiKwSel: [], aiKwAddOpen: false });
          aiv.kwToolbarBg = visSel.length > 0 ? '#f5f7ff' : '#f8fafc';
          /* management actions */
          const promptOf = kw2 => 'What is the best ' + kw2 + ' and who do you recommend?';
          const selPromptTexts = () => visSel.map(r => promptOf(r.kw));
          aiv.kwAddOpen = s.aiKwAddOpen;
          aiv.kwAddToggle = () => this.setState(st => ({ aiKwAddOpen: !st.aiKwAddOpen }));
          aiv.kwAddBtnStyle = { display: 'inline-flex', alignItems: 'center', gap: '6px', cursor: visSel.length ? 'pointer' : 'default', padding: '7px 14px', fontSize: '12.5px', fontWeight: 600, color: 'white', background: '#4f46e5', borderRadius: '8px', opacity: visSel.length ? 1 : 0.5 };
          aiv.kwLists = d.lists.map(l => ({
            name: l.name,
            onAdd: () => this.aiAddPrompts(selPromptTexts(), l.id, () => this.setState({ aiKwSel: [], aiKwAddOpen: false }))
          }));
          aiv.kwNewName = s.aiNewPlName;
          aiv.kwNewSet = e => this.setState({ aiNewPlName: e.target.value });
          const kwCreateAdd = () => {
            const nm = this.state.aiNewPlName.trim();
            const texts = selPromptTexts();
            if (!nm || !texts.length) return;
            /* Same as expCreateAdd above: only the list creation rejects into this catch. */
            this.aiPost('lists', { op: 'create', name: nm })
              .then(r => this.aiAddPrompts(texts, r.id, () => this.setState({ aiKwSel: [], aiKwAddOpen: false, aiNewPlName: '' })))
              .catch(err => { if (this._alive) this.notify(this.errText(err, 'Could not create the prompt list')); });
          };
          aiv.kwNewCreate = kwCreateAdd;
          aiv.kwNewKey = e => { if (e.key === 'Enter') kwCreateAdd(); };
          aiv.kwExport = () => {
            const exp = visSel.length ? visSel : rows;
            this.downloadCsv(project.domain + '-ai-keywords.csv',
              [['keyword', 'kw'], ['ai_volume', 'aiVolume'], ['google_volume', 'gVolume'], ['ai_share_pct', 'ratio'], ['intent', 'intent'], ['your_mentions', 'mentions']], exp);
            this.notify('Exported ' + exp.length + ' AI keyword' + (exp.length === 1 ? '' : 's') + ' (CSV)');
          };
          aiv.kwExportLabel = 'Export CSV ' + (visSel.length ? '(' + visSel.length + ')' : '(all ' + rows.length + ')');
          aiv.kwRows = rows.map(r => {
            const iv = this.intentView(r.intent);
            const on = kwSelSet.has(r.kw);
            return {
              checked: on,
              rowBg: on ? '#f5f7ff' : 'white',
              checkStyle: { width: '15px', height: '15px', borderRadius: '4px', border: '1.5px solid ' + (on ? '#4f46e5' : '#cbd5e1'), background: on ? '#4f46e5' : 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, color: 'white', fontSize: '10px', fontWeight: 700, cursor: 'pointer' },
              toggleSel: () => this.setState(st => ({ aiKwSel: on ? (st.aiKwSel || []).filter(x => x !== r.kw) : (st.aiKwSel || []).concat([r.kw]) })),
              kw: r.kw, aiVolFmt: this.fmt(r.aiVolume), gVolFmt: this.fmt(r.gVolume),
              spark: this.spark(r.trend, 46, 16),
              sparkColor: r.trend[11] >= r.trend[0] ? '#22c55e' : '#ef4444',
              ratioLabel: r.ratio == null ? '—' : r.ratio + '%',
              ratioStyle: { fontSize: '12px', fontWeight: 700, color: r.ratio >= 30 ? '#7c3aed' : '#64748b', textAlign: 'right' },
              intentLabel: iv.label, intentStyle: iv.style,
              mentions: r.mentions,
              gap: r.gap,
              mentionsStyle: { fontSize: '13px', fontWeight: 600, color: r.mentions === 0 ? '#cbd5e1' : '#0f172a', textAlign: 'right' },
              track: () => this.aiInspect('What is the best ' + r.kw + ' and who do you recommend?', null)
            };
          });
        }

        if (sub2 === 'inspector') {
          aiv.inspQ = s.aiInspQ;
          /* Editing the question by hand detaches it from any tracked prompt — otherwise the
             next inspection would be filed against a prompt whose text it no longer matches. */
          aiv.inspQSet = e => this.setState({ aiInspQ: e.target.value, aiInspPromptId: null });
          const inspGo = () => this.aiInspect(this.state.aiInspQ, this.state.aiInspPromptId || null);
          aiv.inspQKey = e => { if (e.key === 'Enter') inspGo(); };
          aiv.inspRun = inspGo;
          aiv.inspRunLabel = s.aiInspecting ? 'Inspecting…' : 'Inspect now · ' + money3(d.costs.inspect);
          aiv.inspRunStyle = Object.assign({}, redBtn, { padding: '9px 16px', fontSize: '13px' });
          /* false = a prompt row was opened that has never been run: show the honest "not run
             yet" panel instead of silently falling back to some other question's answer. */
          const entry = s.aiInspEntry === false ? null : (s.aiInspEntry || d.history[0] || null);
          aiv.inspHasEntry = !!entry;
          /* One answer belongs to ONE engine, and the panel never said which. When a prompt
             has been answered by several engines the user needs to move between them without
             going back to the grid — and without paying for a fresh check to do it. */
          const inspPid = s.aiInspPromptId;
          const inspSeen = {};
          const inspAlts = inspPid == null ? [] : d.history.filter(e => {
            if (e.promptId !== inspPid || inspSeen[e.platform]) return false;
            inspSeen[e.platform] = 1; return true;
          });
          const inspChipBase = { display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '4px 11px', fontSize: '12px', fontWeight: 500, borderRadius: '999px', cursor: 'pointer', color: '#64748b', border: '1px solid #e2e8f0', background: 'white' };
          aiv.inspHasAlts = inspAlts.length > 1;
          aiv.inspAlts = inspAlts.map(e => ({
            label: e.platformName || e.platform || 'Unknown engine',
            style: (entry && e.id === entry.id)
              ? Object.assign({}, inspChipBase, { borderColor: '#4f46e5', color: '#4f46e5', background: '#eef2ff', fontWeight: 600 })
              : inspChipBase,
            click: () => this.setState({ aiInspEntry: e, aiInspPlat: e.platform })
          }));
          aiv.inspNotRun = s.aiInspEntry === false && !s.aiInspecting;
          aiv.inspNotRunQ = '“' + (s.aiInspQ || '') + '”';
          aiv.inspecting = s.aiInspecting;
          if (entry) {
            const sc2 = entry.scrape;
            const vc = verdictChip(entry.verdict);
            aiv.inspPrompt = entry.question;
            /* The engine's NAME leads: an answer is one engine's answer, and the panel used to
               show only the model id, so it was impossible to tell which of four columns you
               were reading. `platformName` has always been stored on the entry. */
            aiv.inspMeta = (entry.platformName || entry.platform || 'Unknown engine')
              + ' · ' + sc2.model + ' · ' + sc2.location + ' · captured ' + entry.ts;
            aiv.inspVerdict = entry.verdict === 'cited' ? 'You are cited at position #' + entry.position : entry.verdict === 'mentioned' ? 'You are mentioned but not cited' : 'You are not mentioned in this answer';
            aiv.inspVerdictStyle = Object.assign({}, vc.style, { fontSize: '12px', padding: '4px 10px', borderRadius: '999px' });
            /* Tracked competitors the answer really named — analyze_answer has always detected
               and stored these on every check; they were just never rendered anywhere. */
            const compHits = entry.competitors || [];
            aiv.inspHasComps = compHits.length > 0;
            aiv.inspComps = compHits.map(c2 => ({
              name: c2.name,
              label: c2.cited ? 'Cited #' + c2.position : 'Mentioned',
              snippet: c2.snippet || '',
              style: Object.assign(chip(c2.cited ? '#fef3c7' : '#f3e8ff', c2.cited ? '#b45309' : '#7e22ce'), { fontSize: '11px', padding: '3px 9px', borderRadius: '999px' })
            }));
            /* Display cleanup only: the model writes markdown emphasis; raw ** around every
               name is noise in a plain-text render. Verdicts are computed on the raw answer. */
            const unmd = t => String(t || '').replace(/\*\*|__/g, '');
            aiv.inspParas = sc2.paragraphs.map(pa => ({
              text: unmd(pa.text),
              style: pa.hit
                ? { fontSize: '14px', lineHeight: 1.65, color: '#312e81', background: '#eef2ff', border: '1px solid #c7d2fe', borderRadius: '8px', padding: '12px 14px', margin: 0 }
                : { fontSize: '14px', lineHeight: 1.65, color: '#334155', margin: 0, padding: '0 14px' }
            }));
            /* Citations arrive from check_prompt as bare {title, url} pairs — n/domain/isYou
               were never on them, so the list rendered "[undefined]" with blank domains. The
               ordinal is the list position; the domain comes off the URL; "You" is a real
               hostname match against this project's domain. */
            aiv.inspCites = sc2.citations.map((c2, i2) => {
              const host = c2.domain || ((String(c2.url || '').match(/^https?:\/\/(?:www\.)?([^\/]+)/) || [])[1] || '');
              const isYou = c2.isYou != null ? c2.isYou : isOurs(host);
              return {
                n: '[' + (c2.n != null ? c2.n : i2 + 1) + ']',
                title: c2.title || host || c2.url || '', domain: host,
                rowStyle: { display: 'flex', alignItems: 'flex-start', gap: '10px', padding: '10px 14px', borderTop: '1px solid #f8fafc', background: isYou ? '#eef2ff' : 'transparent' },
                titleStyle: { fontSize: '13px', fontWeight: isYou ? 700 : 500, color: isYou ? '#4338ca' : '#334155' },
                youChip: isYou
              };
            });
          }
        }

        if (sub2 === 'history') {
          aiv.histEmpty = d.history.length === 0;
          aiv.histRows = d.history.map(e => {
            const vc = verdictChip(e.verdict);
            return {
              date: e.ts, question: e.question,
              verdictLabel: vc.label, verdictStyle: vc.style,
              pos: e.position ? '#' + e.position : '—',
              costFmt: money3(e.cost),
              open: () => { this.setState({ aiInspEntry: e, aiInspQ: e.question, aiInspPromptId: e.promptId || null, aiSub: 'inspector' }); this.pushNav({ aiSub: 'inspector' }); }
            };
          });
        }

        vals.aiv = aiv;
      }
    }

