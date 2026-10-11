// Safe rendering of scan results and on-device history.
// Every value is inserted with textContent — never as HTML — so product data
// from any source can't run code in the page.
window.FPS = (function () {
    'use strict';

    function el(tag, props, children) {
        var node = document.createElement(tag);
        Object.keys(props || {}).forEach(function (k) {
            if (k === 'text') node.textContent = props[k];
            else if (k === 'class') node.className = props[k];
            else node.setAttribute(k, props[k]);
        });
        (children || []).forEach(function (c) { if (c) node.appendChild(c); });
        return node;
    }

    function safeImage(url) {
        return typeof url === 'string' && /^https:\/\/images\.openfoodfacts\.(org|net)\//.test(url) ? url : null;
    }

    function str(v, fallback) { return (typeof v === 'string' && v.trim()) ? v : (fallback || ''); }
    function list(v) { return Array.isArray(v) ? v.filter(function (x) { return typeof x === 'string'; }) : []; }

    // ---------- storage (this browser only) ----------
    var RECENT = 'fps-recent', SAVED = 'fps-saved', MAX = 50;
    function read(key) {
        try { var v = JSON.parse(localStorage.getItem(key) || '[]'); return Array.isArray(v) ? v : []; }
        catch (e) { return []; }
    }
    function write(key, items) {
        try { localStorage.setItem(key, JSON.stringify(items.slice(0, MAX))); return true; }
        catch (e) { return false; }
    }
    function idOf(data) {
        var off = data && data.open_food_facts || {};
        var d = data && data.dashboard || {};
        return off.barcode || ('name:' + str(d['Product Name']) + '|' + str(d['Brand']));
    }
    var store = {
        recent: function () { return read(RECENT); },
        saved: function () { return read(SAVED); },
        addRecent: function (data) {
            var id = idOf(data);
            var items = read(RECENT).filter(function (x) { return x.id !== id; });
            items.unshift({ id: id, at: new Date().toISOString(), data: data });
            write(RECENT, items);
        },
        isSaved: function (data) { var id = idOf(data); return read(SAVED).some(function (x) { return x.id === id; }); },
        toggleSaved: function (data) {
            var id = idOf(data);
            var items = read(SAVED);
            var exists = items.some(function (x) { return x.id === id; });
            items = exists ? items.filter(function (x) { return x.id !== id; })
                           : [{ id: id, at: new Date().toISOString(), data: data }].concat(items);
            write(SAVED, items);
            return !exists;
        },
        clear: function () {
            try { localStorage.removeItem(RECENT); localStorage.removeItem(SAVED); return true; } catch (e) { return false; }
        }
    };

    // ---------- result card ----------
    function vegClass(status) {
        if (status === 'Vegetarian' || status === 'Vegan') return 'veg-yes';
        if (status === 'Non-Vegetarian') return 'veg-no';
        return 'veg-unknown';
    }

    function fact(label, valueNode, small) {
        var dd = el('dd', {}, [valueNode]);
        if (small) dd.appendChild(el('small', { text: small }));
        return el('div', {}, [el('dt', { text: label }), dd]);
    }

    function nutritionTable(n) {
        var rows = [['energy-kcal_100g', 'Energy', 'kcal', 0], ['fat_100g', 'Fat', 'g', 1], ['saturated-fat_100g', 'Saturated fat', 'g', 1],
                    ['carbohydrates_100g', 'Carbohydrates', 'g', 1], ['sugars_100g', 'Sugars', 'g', 1], ['fiber_100g', 'Fibre', 'g', 1],
                    ['proteins_100g', 'Protein', 'g', 1], ['salt_100g', 'Salt', 'g', 2]];
        var body = el('tbody');
        if (typeof n['energy-kcal_100g'] !== 'number' && typeof n['energy-kj_100g'] === 'number') {
            n = Object.assign({}, n, { 'energy-kcal_100g': n['energy-kj_100g'] / 4.184 });
        }
        rows.forEach(function (r) {
            if (typeof n[r[0]] === 'number') {
                body.appendChild(el('tr', {}, [el('th', { scope: 'row', text: r[1] }), el('td', { text: n[r[0]].toFixed(r[3]) + ' ' + r[2] })]));
            }
        });
        if (!body.children.length) return null;
        return el('table', { class: 'nutrition' }, [el('caption', { class: 'visually-hidden', text: 'Nutrition per 100 g' }), body]);
    }

    function render(container, data, opts) {
        opts = opts || {};
        var d = (data && data.dashboard) || {};
        var off = (data && data.open_food_facts) || {};
        container.textContent = '';

        var img = safeImage(off.image_url);
        var head = el('div', { class: 'result-head' }, [
            img ? el('img', { src: img, alt: 'Pack of ' + str(d['Product Name'], 'product'), width: '112', height: '112', loading: 'lazy', referrerpolicy: 'no-referrer' })
                : el('div', { class: 'no-photo', text: 'No photo' }),
            el('div', {}, [el('h2', { text: str(d['Product Name'], 'Name not available') }),
                           el('p', { text: str(d['Brand'], 'Brand not available') + (off.barcode ? ' · ' + off.barcode : '') })])
        ]);
        container.appendChild(head);

        var vegStatus = str(d['Veg Status'], 'Not confirmed');
        var vegNode = el('span', {}, [el('span', { class: 'veg-dot ' + vegClass(vegStatus), 'aria-hidden': 'true' }), document.createTextNode(vegStatus)]);
        var grade = str(off.nutriscore);
        var gradeNode = /^[A-E]$/.test(grade) ? el('span', { class: 'grade grade-' + grade, text: grade }) : el('span', { text: 'Not enough data' });
        var score = typeof d['Safety Score'] === 'number' ? d['Safety Score'] + '/100' : 'Not available';
        var nova = [1, 2, 3, 4].indexOf(off.nova_group) >= 0 ? 'Group ' + off.nova_group : 'Unknown';

        container.appendChild(el('dl', { class: 'facts' }, [
            fact('Veg status', vegNode, str(d['Veg Reason'])),
            fact('Nutri-Score', gradeNode),
            fact('Ingredient score', document.createTextNode(score), 'Simple rule-based guide'),
            fact('Processing (NOVA)', document.createTextNode(nova))
        ]));

        var allergens = list(d['Allergens']);
        container.appendChild(el('h3', { text: 'Possible allergens' }));
        container.appendChild(allergens.length ? el('ul', { class: 'chips alert' }, allergens.map(function (a) { return el('li', { text: a }); }))
                                               : el('p', { class: 'muted', text: 'None found in the ingredients text. Check the pack.' }));

        var flags = list(d['Flags']);
        if (flags.length) {
            container.appendChild(el('h3', { text: 'Ingredients to watch' }));
            container.appendChild(el('ul', { class: 'chips caution' }, flags.map(function (f) { return el('li', { text: f }); })));
        }

        var ingredients = list(d['Ingredients']);
        container.appendChild(el('h3', { text: 'Ingredients (' + ingredients.length + ')' }));
        container.appendChild(ingredients.length ? el('p', { text: ingredients.join(', ') })
                                                 : el('p', { class: 'muted', text: 'No ingredients list available for this product.' }));

        var table = nutritionTable(off.nutriments || {});
        if (table) { container.appendChild(el('h3', { text: 'Nutrition per 100 g' })); container.appendChild(table); }

        var actions = el('div', { class: 'controls' });
        var saveBtn = el('button', { class: 'btn', type: 'button', text: store.isSaved(data) ? 'Remove from saved' : 'Save product' });
        saveBtn.addEventListener('click', function () {
            var nowSaved = store.toggleSaved(data);
            saveBtn.textContent = nowSaved ? 'Remove from saved' : 'Save product';
            if (opts.onChange) opts.onChange();
            if (opts.status) opts.status(nowSaved ? 'Saved in this browser.' : 'Removed from saved.', 'ok');
        });
        var pdfBtn = el('button', { class: 'btn', type: 'button', text: 'Download PDF' });
        pdfBtn.addEventListener('click', function () { downloadPdf(data, pdfBtn, opts.status); });
        actions.appendChild(saveBtn);
        actions.appendChild(pdfBtn);
        container.appendChild(actions);
    }

    async function downloadPdf(data, btn, status) {
        btn.disabled = true;
        try {
            var res = await fetch('/api/report/pdf', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
            if (!res.ok) throw new Error('bad status');
            var blob = await res.blob();
            var url = URL.createObjectURL(blob);
            var name = (str((data.dashboard || {})['Product Name'], 'product').replace(/[^A-Za-z0-9]+/g, '_').slice(0, 60) || 'product') + '_report.pdf';
            var a = el('a', { href: url, download: name });
            document.body.appendChild(a); a.click(); a.remove();
            setTimeout(function () { URL.revokeObjectURL(url); }, 2000);
            if (status) status('Report downloaded.', 'ok');
        } catch (e) {
            if (status) status('The report could not be created. Please try again.', 'err');
        }
        btn.disabled = false;
    }

    function statusFn(node) {
        return function (text, kind) {
            node.textContent = text;
            node.className = 'status-msg' + (kind === 'ok' ? ' is-ok' : kind === 'err' ? ' is-err' : '');
        };
    }

    return { el: el, render: render, store: store, safeImage: safeImage, statusFn: statusFn, str: str };
})();
