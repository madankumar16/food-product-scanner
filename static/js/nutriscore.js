// Nutri-Score calculator page.
(function () {
    'use strict';
    var el = FPS_el();
    var form = document.getElementById('calc-form');
    var out = document.getElementById('result');
    var panel = document.getElementById('result-panel');
    var statusNode = document.getElementById('status');

    function FPS_el() {
        return function (tag, props, children) {
            var n = document.createElement(tag);
            Object.keys(props || {}).forEach(function (k) {
                if (k === 'text') n.textContent = props[k]; else if (k === 'class') n.className = props[k]; else n.setAttribute(k, props[k]);
            });
            (children || []).forEach(function (c) { n.appendChild(c); });
            return n;
        };
    }
    function status(text, kind) {
        statusNode.textContent = text;
        statusNode.className = 'status-msg' + (kind === 'err' ? ' is-err' : kind === 'ok' ? ' is-ok' : '');
    }

    var NAMES = { energy: 'Energy', sat_fat: 'Saturated fat', sugars: 'Sugars', salt: 'Salt', sweeteners: 'Sweeteners',
                  fiber: 'Fibre', protein: 'Protein', fruit_veg: 'Fruit, veg & legumes' };

    form.addEventListener('submit', async function (e) {
        e.preventDefault();
        var body = {};
        new FormData(form).forEach(function (v, k) { body[k] = v; });
        var required = ['energy_kj', 'sat_fat', 'sugars', 'salt'];
        var missing = required.filter(function (k) { return body[k] === ''; });
        if (body.category === 'fats_oils_nuts' && body.fat === '') missing.push('fat');
        form.querySelectorAll('input').forEach(function (i) { i.removeAttribute('aria-invalid'); });
        if (missing.length) {
            missing.forEach(function (k) { document.getElementById(k).setAttribute('aria-invalid', 'true'); });
            document.getElementById(missing[0]).focus();
            status('Please fill in: ' + missing.map(function (k) { return document.querySelector('label[for="' + k + '"]').textContent; }).join(', ') + '.', 'err');
            return;
        }
        status('Calculating…');
        try {
            var res = await fetch('/api/nutri-score/calculate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
            var data = await res.json();
            if (!res.ok || !data.success) { status(data.error || 'Please check your values.', 'err'); return; }
            show(data.result);
            status('Done.', 'ok');
            panel.focus();
        } catch (err) {
            status('Could not reach the server. Please try again.', 'err');
        }
    });

    function show(r) {
        out.textContent = '';
        out.appendChild(el('p', {}, [el('span', { class: 'grade grade-' + r.letter, text: r.letter }),
                                      document.createTextNode('  Score ' + r.final_score)]));
        var rows = el('tbody');
        Object.keys(NAMES).forEach(function (k) {
            if (typeof r.breakdown[k] === 'number') {
                var neg = ['energy', 'sat_fat', 'sugars', 'salt', 'sweeteners'].indexOf(k) >= 0;
                var note = (k === 'protein' && r.breakdown.protein_counted === 0) ? ' (not counted)' : '';
                rows.appendChild(el('tr', {}, [el('th', { scope: 'row', text: NAMES[k] }),
                                               el('td', { text: (neg ? '+' : '−') + r.breakdown[k] + note })]));
            }
        });
        out.appendChild(el('table', { class: 'nutrition' }, [el('caption', { class: 'visually-hidden', text: 'Points breakdown' }), rows]));
        out.appendChild(el('p', { class: 'muted', text: 'Lower scores are better. Calculated with the 2023 Nutri-Score algorithm.' }));
    }
})();
