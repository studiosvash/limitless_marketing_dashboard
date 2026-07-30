    /* ============ AI OPTIMIZATION ============ */
    if (tab === 'ai') {
      vals.showAi = true;
      const d = data;
      const llm = d.llmPlatforms;
      const money3 = c => '$' + Number(c || 0).toFixed(c > 0 && c < 0.1 ? 3 : 2);
      const runCostOf = pr => pr.cfg.models.length * d.costs.model;
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
        aiv.wizWeekly = 'Weekly schedule ≈ ' + money3(totalN * 4 * d.costs.model * 4.3) + '/mo across 4 LLMs';
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
        const allCost = prompts.reduce((a2, pr) => a2 + runCostOf(pr), 0);
        aiv.runAllLabel = 'Run all now · ' + money3(allCost);
        aiv.runAllStyle = redBtn;
        aiv.runAll = () => { if (prompts.length) this.aiRun({}); };
        aiv.hasPrompts = prompts.length > 0;

        const sub2 = s.aiSub;
        const goSub = v => { this.setState({ aiSub: v, aiOpen: null }); this.pushNav({ aiSub: v }); };
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

        if (sub2 === 'visibility') {
          const sov = d.sov;
          const maxSov = Math.max.apply(null, sov.rows.map(r => r.sov)) || 1;
          aiv.sovPct = sov.you + '%';
          aiv.sovDelta = (sov.delta >= 0 ? '▲ +' : '▼ ') + Math.abs(sov.delta) + ' pts vs. last week';
          aiv.sovDeltaStyle = { fontSize: '12px', fontWeight: 600, padding: '3px 8px', borderRadius: '4px', background: sov.delta >= 0 ? '#ecfdf5' : '#fff1f2', color: sov.delta >= 0 ? '#059669' : '#e11d48' };
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
          aiv.promptGridCols = '28px minmax(280px, 1.8fr) repeat(' + llm.length + ', 1fr)';
          const cell = r => {
            if (!r) return { label: 'off', style: Object.assign(chip('#f8fafc', '#cbd5e1'), { fontSize: '11px', fontWeight: 500 }) };
            if (!r.mentioned) return { label: '—', style: { display: 'inline-flex', alignItems: 'center', justifyContent: 'center', minWidth: '44px', height: '24px', borderRadius: '4px', fontSize: '12px', fontWeight: 600, background: '#f8fafc', color: '#cbd5e1' } };
            if (r.cited) return { label: 'Cited #' + r.position, style: { display: 'inline-flex', alignItems: 'center', justifyContent: 'center', minWidth: '44px', height: '24px', padding: '0 8px', borderRadius: '4px', fontSize: '12px', fontWeight: 700, background: '#d1fae5', color: '#047857' } };
            return { label: 'Mentioned', style: { display: 'inline-flex', alignItems: 'center', justifyContent: 'center', minWidth: '44px', height: '24px', padding: '0 8px', borderRadius: '4px', fontSize: '12px', fontWeight: 600, background: '#dbeafe', color: '#1d4ed8' } };
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

          aiv.promptRows = visPrompts.map(pr => {
            const open = s.aiOpen === pr.id;
            const prSelOn = promptSelSet.has(pr.id);
            /* `results` is {} until the prompt has actually been run — build_ai_response says so
               explicitly ("Real observed results keyed by platform id -- {} until this prompt is
               actually run"). So a TRACKED model routinely has no result entry, and reading
               through pr.results[id] without a guard threw a TypeError. There is no try/catch
               around renderVals(), so that throw killed the whole vals() build and the entire
               SPA render went blank — the reported "Prompts tab bugs out".
               It became reachable when _handle_setup started seeding tracked_models with
               connectable_platforms(): every prompt the setup wizard creates on a new project
               has models but no results, so a fresh project crashed on first visit.
               cell() already tolerates null; these two reads did not. */
            const res = pl2 => pr.results[pl2.id] || null;
            const citedN = llm.filter(pl2 => pr.cfg.models.includes(pl2.id) && (res(pl2) || {}).cited).length;
            return {
              text: pr.text, open,
              meta: listName(pr.listId) + ' · ' + pr.cfg.models.length + ' model' + (pr.cfg.models.length === 1 ? '' : 's') + ' · ' + pr.cfg.cadence + ' · ' + (pr.cfg.city || pr.cfg.country) + (pr.lastRun ? ' · last run ' + pr.lastRun : ' · not run yet'),
              cells: llm.map(pl2 => cell(pr.cfg.models.includes(pl2.id) ? res(pl2) : null)),
              checked: prSelOn,
              checkStyle: { width: '15px', height: '15px', borderRadius: '4px', border: '1.5px solid ' + (prSelOn ? '#4f46e5' : '#cbd5e1'), background: prSelOn ? '#4f46e5' : 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, color: 'white', fontSize: '10px', fontWeight: 700, cursor: 'pointer' },
              toggleSel: e => { e.stopPropagation(); this.setState(st => ({ aiPromptSel: prSelOn ? (st.aiPromptSel || []).filter(x => x !== pr.id) : (st.aiPromptSel || []).concat([pr.id]) })); },
              toggle: () => this.setState({ aiOpen: open ? null : pr.id }),
              chev: { color: '#cbd5e1', fontSize: '18px', transform: open ? 'rotate(90deg)' : 'none', transition: 'transform 0.15s ease', flexShrink: 0 },
              coverage: citedN + ' of ' + pr.cfg.models.length + ' models cite you',
              details: llm.filter(pl2 => pr.cfg.models.includes(pl2.id)).map(pl2 => ({
                name: pl2.name,
                dot: { width: '8px', height: '8px', borderRadius: '50%', background: pl2.color, flexShrink: 0 },
                /* Honest placeholder rather than a blank paragraph: the row exists because the
                   model is tracked, and "not run yet" is the actual state, not missing data. */
                snippet: (res(pl2) || {}).snippet || 'Not run yet — press “Run now” to check this model.'
              })),
              runLabel: 'Run now · ' + money3(runCostOf(pr)),
              runStyle: redBtn,
              run: () => this.aiRun({ promptId: pr.id }),
              inspect: () => this.aiInspect(pr.text, pr.id),
              cfgOpen: () => this.setState({ aiCfgOpen: pr.id, aiCfgDraft: Object.assign({}, pr.cfg, { models: pr.cfg.models.slice(), listId: pr.listId, text: pr.text }) }),
              remove: () => this.aiRemovePrompts([pr.id])
            };
          });
          const flt = d.lists.find(l => l.id === s.aiListFilter);
          if (flt) {
            const listCost = visPrompts.reduce((a2, pr) => a2 + runCostOf(pr), 0);
            aiv.runListShown = visPrompts.length > 0;
            aiv.runListLabel = 'Run "' + flt.name + '" now · ' + money3(listCost);
            aiv.runListStyle = redBtn;
            aiv.runList = () => this.aiRun({ listId: flt.id });
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
          aiv.inspQSet = e => this.setState({ aiInspQ: e.target.value });
          aiv.inspQKey = e => { if (e.key === 'Enter') this.aiInspect(this.state.aiInspQ, null); };
          aiv.inspRun = () => this.aiInspect(this.state.aiInspQ, null);
          aiv.inspRunLabel = s.aiInspecting ? 'Inspecting…' : 'Inspect now · ' + money3(d.costs.inspect);
          aiv.inspRunStyle = Object.assign({}, redBtn, { padding: '9px 16px', fontSize: '13px' });
          const entry = s.aiInspEntry || d.history[0] || null;
          aiv.inspHasEntry = !!entry;
          aiv.inspecting = s.aiInspecting;
          if (entry) {
            const sc2 = entry.scrape;
            const vc = verdictChip(entry.verdict);
            aiv.inspPrompt = entry.question;
            aiv.inspMeta = sc2.model + ' · ' + sc2.location + ' · captured ' + entry.ts;
            aiv.inspVerdict = entry.verdict === 'cited' ? 'You are cited at position #' + entry.position : entry.verdict === 'mentioned' ? 'You are mentioned but not cited' : 'You are not mentioned in this answer';
            aiv.inspVerdictStyle = Object.assign({}, vc.style, { fontSize: '12px', padding: '4px 10px', borderRadius: '999px' });
            aiv.inspParas = sc2.paragraphs.map(pa => ({
              text: pa.text,
              style: pa.hit
                ? { fontSize: '14px', lineHeight: 1.65, color: '#312e81', background: '#eef2ff', border: '1px solid #c7d2fe', borderRadius: '8px', padding: '12px 14px', margin: 0 }
                : { fontSize: '14px', lineHeight: 1.65, color: '#334155', margin: 0, padding: '0 14px' }
            }));
            aiv.inspCites = sc2.citations.map(c2 => ({
              n: '[' + c2.n + ']', title: c2.title, domain: c2.domain,
              rowStyle: { display: 'flex', alignItems: 'flex-start', gap: '10px', padding: '10px 14px', borderTop: '1px solid #f8fafc', background: c2.isYou ? '#eef2ff' : 'transparent' },
              titleStyle: { fontSize: '13px', fontWeight: c2.isYou ? 700 : 500, color: c2.isYou ? '#4338ca' : '#334155' },
              youChip: c2.isYou
            }));
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
              open: () => { this.setState({ aiInspEntry: e, aiSub: 'inspector' }); this.pushNav({ aiSub: 'inspector' }); }
            };
          });
        }

        vals.aiv = aiv;
      }
    }

