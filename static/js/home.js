// Home: the "last scan" card under the camera. Data comes only from this
// browser's history; nothing is shown that the scan didn't contain.
(function () {
    'use strict';
    var el = FPS.el;
    var card = document.getElementById('score-card');
    var latest = FPS.store.recent()[0];
    if (!card || !latest || !latest.data) return;
    var data = latest.data;
    card.textContent = '';

    if (data.kind && data.kind !== 'food') {
        card.appendChild(el('p', { class: 'eyebrow', text: 'Last scan · ' + FPS.kindLabel(data.kind) }));
        card.appendChild(el('p', { class: 'score-name', text: FPS.titleOf(data) }));
        var sub = data.item && data.item.subtitle;
        if (typeof sub === 'string' && sub) card.appendChild(el('p', { class: 'muted', text: sub }));
        if (typeof data.warning === 'string' && data.warning) card.appendChild(el('p', { class: 'alert-box', text: data.warning }));
        card.appendChild(el('p', { class: 'muted', text: 'Tap to see the details.' }));
        return;
    }

    var d = data.dashboard || {};
    var off = data.open_food_facts || {};
    var score = typeof d['Safety Score'] === 'number' ? d['Safety Score'] : null;
    var top = el('div', { class: 'score-top' }, [
        el('div', {}, [el('p', { class: 'eyebrow', text: 'Last scan · Food' }),
                       el('p', { class: 'score-name', text: FPS.titleOf(data) })]),
        score === null ? null : el('div', {}, [
            el('p', { class: 'score-num' }, [document.createTextNode(String(score)), el('small', { text: '/100' })]),
            el('p', { class: 'muted', text: 'Ingredient score' })])
    ]);
    card.appendChild(top);
    if (typeof data.warning === 'string' && data.warning) card.appendChild(el('p', { class: 'alert-box', text: data.warning }));

    // Nutri-Score A–E with the product's grade highlighted (none if unknown).
    var grade = /^[A-E]$/.test(off.nutriscore || '') ? off.nutriscore : null;
    var bar = el('ul', { class: 'ns-bar', 'aria-label': grade ? 'Nutri-Score ' + grade : 'Nutri-Score: not enough data' });
    'ABCDE'.split('').forEach(function (g) {
        bar.appendChild(el('li', { class: g + (g === grade ? ' on' : ''), text: g, 'aria-hidden': 'true' }));
    });
    card.appendChild(bar);
    if (!grade) card.appendChild(el('p', { class: 'muted', text: 'Nutri-Score: not enough nutrition data.' }));

    // Sugar, fat and salt per 100 g, only when the database has them.
    var n = off.nutriments || {};
    function grams(key) { return typeof n[key] === 'number' ? n[key].toFixed(n[key] < 10 ? 1 : 0) + ' g' : 'Not listed'; }
    card.appendChild(el('dl', { class: 'macros' }, [
        el('div', {}, [el('dt', { text: 'Sugar' }), el('dd', { text: grams('sugars_100g') })]),
        el('div', {}, [el('dt', { text: 'Fat' }), el('dd', { text: grams('fat_100g') })]),
        el('div', {}, [el('dt', { text: 'Salt' }), el('dd', { text: grams('salt_100g') })])
    ]));
})();
