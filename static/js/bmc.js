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

    document.addEventListener('DOMContentLoaded', function () {
        setupHeat();
        setupTabs();
        setupRowFilter();
        setupSort();
        setupBarsOnReveal();
        setupChats();
    });
})();
