/* Bangla MedConv – interactive behaviour (tabs, heat-maps, language switch, sorting, chat viewer) */
(function () {
    function $all(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }

    /* ---------- colour scale ---------- */
    function num(text) {
        var m = String(text).replace('\u2212', '-').match(/-?\d+(\.\d+)?/);
        return m ? parseFloat(m[0]) : NaN;
    }
    function color(t, dir) {
        t = Math.max(0, Math.min(1, t));
        if (dir === 'mag') { return 'hsl(262 70% ' + (97 - t * 25) + '%)'; }
        if (dir === 'down') { t = 1 - t; }
        return 'hsl(' + (8 + t * 147) + ' ' + (68 - t * 6) + '% ' + (84 + (t < .5 ? t : 1 - t) * 4) + '%)';
    }

    /* ---------- paired EN / BN cell rendering ---------- */
    function currentLang(el) {
        var scope = el.closest('[data-lang]');
        return scope ? scope.getAttribute('data-lang') : 'en';
    }
    function paintTable(table) {
        var cfg;
        try { cfg = JSON.parse(table.getAttribute('data-heat') || '{}'); } catch (e) { cfg = {}; }
        var lang = currentLang(table);
        $all('tbody tr', table).forEach(function (row) {
            $all('td', row).forEach(function (td, idx) {
                if (td.hasAttribute('data-en') && td.hasAttribute('data-bn')) {
                    td.textContent = td.getAttribute('data-' + lang);
                }
                var c = cfg[idx];
                if (!c) { return; }
                var v = num(td.textContent);
                if (isNaN(v)) { return; }
                td.style.background = color((v - c[0]) / (c[1] - c[0]), c[2]);
            });
        });
    }

    function setupHeat() {
        $all('table[data-heat]').forEach(paintTable);
        $all('[data-lang-switch] .bmc-tab-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var scope = btn.closest('[data-lang-scope]');
                if (!scope) { return; }
                scope.setAttribute('data-lang', btn.getAttribute('data-value'));
                $all('[data-lang-switch] .bmc-tab-btn', scope).forEach(function (b) {
                    b.classList.toggle('active', b === btn);
                });
                $all('table[data-heat]', scope).forEach(paintTable);
            });
        });
    }

    /* ---------- generic tabs ---------- */
    function setupTabs() {
        $all('[data-tabs]').forEach(function (group) {
            var btns = $all('.bmc-tab-btn', group);
            var scope = group.closest('[data-tab-scope]') || group.parentElement;
            btns.forEach(function (btn) {
                btn.addEventListener('click', function () {
                    var target = btn.getAttribute('data-tab');
                    btns.forEach(function (b) { b.classList.toggle('active', b === btn); });
                    $all('.bmc-tab-panel[data-group="' + group.getAttribute('data-tabs') + '"]', scope).forEach(function (p) {
                        p.classList.toggle('active', p.getAttribute('data-panel') === target);
                    });
                    $all('table[data-heat]', scope).forEach(paintTable);
                    animateBars(scope);
                });
            });
        });
    }

    /* ---------- row filter (All / EN / BN) ---------- */
    function setupRowFilter() {
        $all('[data-row-filter]').forEach(function (group) {
            var table = document.getElementById(group.getAttribute('data-row-filter'));
            if (!table) { return; }
            $all('.bmc-tab-btn', group).forEach(function (btn) {
                btn.addEventListener('click', function () {
                    var v = btn.getAttribute('data-value');
                    $all('.bmc-tab-btn', group).forEach(function (b) { b.classList.toggle('active', b === btn); });
                    $all('tbody tr', table).forEach(function (r) {
                        var l = r.getAttribute('data-l');
                        r.classList.toggle('is-hidden-row', v !== 'all' && l && l !== v);
                    });
                });
            });
        });
    }

    /* ---------- sortable tables ---------- */
    function setupSort() {
        $all('table.sortable').forEach(function (table) {
            var heads = $all('thead th', table);
            heads.forEach(function (th, idx) {
                th.classList.add('sortable');
                th.addEventListener('click', function () {
                    var asc = !th.classList.contains('asc');
                    heads.forEach(function (h) { h.classList.remove('asc', 'desc'); });
                    th.classList.add(asc ? 'asc' : 'desc');
                    var tbody = table.querySelector('tbody');
                    var rows = $all('tr', tbody);
                    rows.sort(function (a, b) {
                        var x = a.children[idx].textContent.trim(), y = b.children[idx].textContent.trim();
                        var nx = num(x), ny = num(y);
                        var r = (!isNaN(nx) && !isNaN(ny)) ? nx - ny : x.localeCompare(y);
                        return asc ? r : -r;
                    });
                    rows.forEach(function (r) { r.classList.remove('group-start'); tbody.appendChild(r); });
                });
            });
        });
    }

    /* ---------- animated bars ---------- */
    function animateBars(root) {
        $all('.crit-fill[data-w]', root || document).forEach(function (el) {
            el.style.width = '0';
            requestAnimationFrame(function () { requestAnimationFrame(function () { el.style.width = el.getAttribute('data-w') + '%'; }); });
        });
    }
    function setupBarsOnReveal() {
        var els = $all('.crit-grid');
        if (!els.length || !('IntersectionObserver' in window)) { animateBars(); return; }
        var io = new IntersectionObserver(function (entries, obs) {
            entries.forEach(function (e) {
                if (e.isIntersecting) { animateBars(e.target); obs.unobserve(e.target); }
            });
        }, { threshold: 0.2 });
        els.forEach(function (el) { io.observe(el); });
    }

    /* ---------- chat viewer ---------- */
    function setupChats() {
        $all('[data-chat]').forEach(function (chat) {
            var msgs = $all('.chat-msg', chat);
            var body = chat.querySelector('.chat-body');
            var next = chat.querySelector('[data-act="next"]');
            var all = chat.querySelector('[data-act="all"]');
            var reset = chat.querySelector('[data-act="reset"]');
            var bar = chat.querySelector('.chat-progress span');
            var shown = 0;

            function render() {
                msgs.forEach(function (m, i) { m.classList.toggle('shown', i < shown); });
                if (bar) { bar.style.width = (100 * shown / msgs.length) + '%'; }
                if (next) { next.disabled = shown >= msgs.length; next.textContent = shown === 0 ? 'Start conversation' : 'Next message (' + shown + '/' + msgs.length + ')'; }
                if (body) { body.scrollTop = body.scrollHeight; }
            }
            if (next) { next.addEventListener('click', function () { if (shown < msgs.length) { shown++; render(); } }); }
            if (all) { all.addEventListener('click', function () { shown = msgs.length; render(); }); }
            if (reset) { reset.addEventListener('click', function () { shown = 0; render(); if (body) { body.scrollTop = 0; } }); }
            chat._show = function (n) { shown = n; render(); };
            chat._show(Math.min(2, msgs.length));
            if (body) { body.scrollTop = 0; }
        });
    }

    /* ---------- interactive model arena comparator ---------- */
    var ARENA_MODELS = {
        'gemma-31b': {
            name: 'Gemma 4 31B',
            en: { safety: 4.23, acc: 2.81, uncert: 4.21, vqa: 62.0, crit: 6.7, loop: 0.0, compl: 100.0 },
            bn: { safety: 4.11, acc: 2.80, uncert: 4.11, vqa: 62.0, crit: 16.7, loop: 0.0, compl: 100.0 },
            delta: { safety: 0.12, ci: '[-0.06, 0.30]', p: 'p = 0.357 (n.s.)', vqaDiff: '+0.0%' },
            notes: 'Top overall clinical safety across both languages. Retains advice reliability with zero degenerate loops and 100% Bangla script compliance.'
        },
        'llama-scout': {
            name: 'Llama 4 Scout',
            en: { safety: 3.83, acc: 2.58, uncert: 3.85, vqa: 49.0, crit: 30.0, loop: 0.0, compl: 100.0 },
            bn: { safety: 3.36, acc: 2.38, uncert: 3.21, vqa: 57.0, crit: 20.0, loop: 0.0, compl: 95.9 },
            delta: { safety: 0.47, ci: '[0.24, 0.69]', p: 'p = 0.001 (sig)', vqaDiff: '+8.0%' },
            notes: 'Shows significant safety degradation in Bangla (Δ = 0.47) and sharp uncertainty drop (3.85 → 3.21), despite higher single-turn Bangla VQA score.'
        },
        'medgemma-27b': {
            name: 'MedGemma 27B',
            en: { safety: 3.99, acc: 2.49, uncert: 3.86, vqa: 62.0, crit: 40.0, loop: 0.0, compl: 100.0 },
            bn: { safety: 3.99, acc: 2.66, uncert: 3.81, vqa: 59.0, crit: 6.7, loop: 0.0, compl: 96.2 },
            delta: { safety: 0.00, ci: '[-0.23, 0.22]', p: 'p = 0.729 (n.s.)', vqaDiff: '-3.0%' },
            notes: 'Exceptional cross-lingual consistency (Δ = 0.00). In Bangla, emergency under-triage plummets from 40.0% to 6.7% due to conservative emergency escalation.'
        },
        'medgemma-4b': {
            name: 'MedGemma 4B',
            en: { safety: 3.71, acc: 2.81, uncert: 3.58, vqa: 65.0, crit: 30.0, loop: 2.5, compl: 100.0 },
            bn: { safety: 3.26, acc: 2.59, uncert: 3.59, vqa: 59.0, crit: 43.3, loop: 1.9, compl: 46.6 },
            delta: { safety: 0.44, ci: '[0.19, 0.69]', p: 'p = 0.010 (sig)', vqaDiff: '-6.0%' },
            notes: 'High diagnostic VQA accuracy (65% EN) yet substantial Bangla safety drop (Δ = 0.44). Suffers severe language switching failure (only 46.6% in Bangla script).'
        },
        'mistral-small': {
            name: 'Mistral Small 3.2',
            en: { safety: 3.71, acc: 2.27, uncert: 3.79, vqa: 53.0, crit: 20.0, loop: 0.0, compl: 100.0 },
            bn: { safety: 3.39, acc: 1.98, uncert: 3.56, vqa: 53.0, crit: 36.7, loop: 10.0, compl: 100.0 },
            delta: { safety: 0.32, ci: '[0.06, 0.56]', p: 'p = 0.052 (borderline)', vqaDiff: '0.0%' },
            notes: 'Moderate safety degradation in Bangla (Δ = 0.32). Degenerates into repetition loops in 10.0% of Bangla consultations while 0% in English.'
        },
        'qwen25-vl': {
            name: 'Qwen2.5-VL 7B',
            en: { safety: 3.26, acc: 2.26, uncert: 3.01, vqa: 57.0, crit: 50.0, loop: 0.6, compl: 100.0 },
            bn: { safety: 1.96, acc: 2.07, uncert: 1.89, vqa: 32.0, crit: 83.3, loop: 83.1, compl: 100.0 },
            delta: { safety: 1.30, ci: '[1.05, 1.56]', p: 'p < 0.0001 (sig)', vqaDiff: '-25.0%' },
            notes: 'Catastrophic failure in Bangla: Safety drops 1.30 points to 1.96 / 5.0, caused by 83.1% repetition loop rate and 83.3% emergency under-triage.'
        }
    };

    function setupArena() {
        var card = document.getElementById('model-arena');
        if (!card) { return; }
        var selA = document.getElementById('arenaModelA');
        var selB = document.getElementById('arenaModelB');
        var metricsA = document.getElementById('arenaMetricsA');
        var metricsB = document.getElementById('arenaMetricsB');
        var verdictA = document.getElementById('arenaVerdictA');
        var verdictB = document.getElementById('arenaVerdictB');
        var takeaway = document.getElementById('arenaTakeaway');
        var langBtns = $all('[data-arena-lang]', card);
        var curLang = 'bn';

        function renderModelMetrics(key, targetMetrics, targetVerdict) {
            var data = ARENA_MODELS[key];
            if (!data) { return; }
            var html = '';
            if (curLang === 'delta') {
                var d = data.delta;
                var safeColor = d.safety <= 0.15 ? 'fill-green' : (d.safety <= 0.45 ? 'fill-amber' : 'fill-red');
                var wSafety = Math.min(100, (d.safety / 1.5) * 100);
                html += '<div class="arena-metric-row"><div class="arena-metric-meta"><span class="arena-metric-label">Safety Gap (&Delta; EN&minus;BN)</span><span class="arena-metric-val">' + d.safety.toFixed(2) + ' <small class="has-text-grey">' + d.ci + '</small></span></div><div class="arena-metric-bar"><div class="arena-metric-fill ' + safeColor + '" style="width:' + wSafety + '%"></div></div></div>';
                html += '<div class="arena-metric-row"><div class="arena-metric-meta"><span class="arena-metric-label">Significance (Holm p)</span><span class="arena-metric-val">' + d.p + '</span></div></div>';
                html += '<div class="arena-metric-row"><div class="arena-metric-meta"><span class="arena-metric-label">VQA Accuracy Gap</span><span class="arena-metric-val">' + d.vqaDiff + '</span></div></div>';
            } else {
                var m = data[curLang];
                var sColor = m.safety >= 4.0 ? 'fill-green' : (m.safety >= 3.3 ? 'fill-blue' : 'fill-red');
                var uColor = m.crit <= 20.0 ? 'fill-green' : (m.crit <= 40.0 ? 'fill-amber' : 'fill-red');
                var lColor = m.loop === 0 ? 'fill-green' : (m.loop <= 5 ? 'fill-amber' : 'fill-red');

                html += '<div class="arena-metric-row"><div class="arena-metric-meta"><span class="arena-metric-label">Clinical Advice Safety (1&ndash;5)</span><span class="arena-metric-val">' + m.safety.toFixed(2) + ' / 5.0</span></div><div class="arena-metric-bar"><div class="arena-metric-fill ' + sColor + '" style="width:' + ((m.safety / 5) * 100) + '%"></div></div></div>';
                html += '<div class="arena-metric-row"><div class="arena-metric-meta"><span class="arena-metric-label">Diagnostic VQA Accuracy</span><span class="arena-metric-val">' + m.vqa.toFixed(1) + '%</span></div><div class="arena-metric-bar"><div class="arena-metric-fill fill-blue" style="width:' + m.vqa + '%"></div></div></div>';
                html += '<div class="arena-metric-row"><div class="arena-metric-meta"><span class="arena-metric-label">Uncertainty Calibration (1&ndash;5)</span><span class="arena-metric-val">' + m.uncert.toFixed(2) + ' / 5.0</span></div><div class="arena-metric-bar"><div class="arena-metric-fill fill-purple" style="width:' + ((m.uncert / 5) * 100) + '%"></div></div></div>';
                html += '<div class="arena-metric-row"><div class="arena-metric-meta"><span class="arena-metric-label">Emergency Under-Triage Risk</span><span class="arena-metric-val has-text-danger">' + m.crit.toFixed(1) + '%</span></div><div class="arena-metric-bar"><div class="arena-metric-fill ' + uColor + '" style="width:' + m.crit + '%"></div></div></div>';
                html += '<div class="arena-metric-row"><div class="arena-metric-meta"><span class="arena-metric-label">Repetition Degeneration Loops</span><span class="arena-metric-val">' + m.loop.toFixed(1) + '%</span></div><div class="arena-metric-bar"><div class="arena-metric-fill ' + lColor + '" style="width:' + Math.min(100, m.loop * 1.2) + '%"></div></div></div>';
            }
            targetMetrics.innerHTML = html;
            targetVerdict.innerHTML = '<strong>Clinical Summary:</strong> ' + data.notes;
        }

        function updateTakeaway() {
            var a = ARENA_MODELS[selA.value];
            var b = ARENA_MODELS[selB.value];
            if (!a || !b || !takeaway) { return; }
            if (selA.value === selB.value) {
                takeaway.className = 'arena-takeaway-bar';
                takeaway.innerHTML = '<i class="fas fa-info-circle"></i> <span>Select two distinct models to see direct head-to-head clinical trade-offs.</span>';
                return;
            }
            var text = '';
            var isAlert = false;
            if (curLang === 'delta') {
                var lowerGap = a.delta.safety < b.delta.safety ? a : b;
                var higherGap = a.delta.safety < b.delta.safety ? b : a;
                text = '<strong>Cross-Lingual Stability:</strong> <strong>' + lowerGap.name + '</strong> has superior cross-lingual stability (&Delta;=' + lowerGap.delta.safety.toFixed(2) + '), whereas <strong>' + higherGap.name + '</strong> exhibits severe disparity (&Delta;=' + higherGap.delta.safety.toFixed(2) + ', ' + higherGap.delta.p + ').';
                isAlert = higherGap.delta.safety > 0.4;
            } else {
                var sA = a[curLang].safety, sB = b[curLang].safety;
                var winner = sA >= sB ? a : b;
                var loser = sA >= sB ? b : a;
                var diff = Math.abs(sA - sB).toFixed(2);
                var langLabel = curLang === 'bn' ? 'Bangla' : 'English';
                text = '<strong>Head-to-Head (' + langLabel + '):</strong> <strong>' + winner.name + '</strong> leads in clinical safety by <strong>+' + diff + ' points</strong> (' + winner[curLang].safety.toFixed(2) + ' vs ' + loser[curLang].safety.toFixed(2) + '). ';
                if (loser[curLang].crit > 35.0 || loser[curLang].loop > 5.0) {
                    text += 'Note: <strong>' + loser.name + '</strong> exhibits significant clinical risk (Under-triage: ' + loser[curLang].crit.toFixed(1) + '%, Loops: ' + loser[curLang].loop.toFixed(1) + '%).';
                    isAlert = true;
                }
            }
            takeaway.className = 'arena-takeaway-bar' + (isAlert ? ' alert' : '');
            takeaway.innerHTML = '<i class="fas ' + (isAlert ? 'fa-exclamation-triangle' : 'fa-check-circle') + '"></i> <span>' + text + '</span>';
        }

        function refresh() {
            renderModelMetrics(selA.value, metricsA, verdictA);
            renderModelMetrics(selB.value, metricsB, verdictB);
            updateTakeaway();
        }

        selA.addEventListener('change', refresh);
        selB.addEventListener('change', refresh);
        langBtns.forEach(function (btn) {
            btn.addEventListener('click', function () {
                curLang = btn.getAttribute('data-arena-lang');
                langBtns.forEach(function (b) { b.classList.toggle('active', b === btn); });
                refresh();
            });
        });

        refresh();
    }

    document.addEventListener('DOMContentLoaded', function () {
        setupHeat();
        setupTabs();
        setupRowFilter();
        setupSort();
        setupBarsOnReveal();
        setupChats();
        setupArena();
    });
})();
