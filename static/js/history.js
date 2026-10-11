// History page: everything here comes from this browser's local storage.
(function () {
    'use strict';
    var el = FPS.el;
    var resultBox = document.getElementById('result');
    var panel = document.getElementById('result-panel');
    var clearStatus = FPS.statusFn(document.getElementById('clear-status'));

    function row(item) {
        var d = (item.data && item.data.dashboard) || {};
        var off = (item.data && item.data.open_food_facts) || {};
        var img = FPS.safeImage(off.image_url);
        var when = '';
        try { when = new Date(item.at).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' }); } catch (e) { /* bad date */ }
        var btn = el('button', { class: 'link-button', type: 'button', text: 'View' });
        btn.setAttribute('aria-label', 'View ' + FPS.str(d['Product Name'], 'product'));
        btn.addEventListener('click', function () {
            FPS.render(resultBox, item.data, { onChange: draw, status: clearStatus });
            panel.focus();
        });
        return el('li', {}, [
            img ? el('img', { src: img, alt: '', width: '56', height: '56', loading: 'lazy', referrerpolicy: 'no-referrer' }) : el('div', { class: 'no-photo', text: '—' }),
            el('div', {}, [el('div', { class: 'name', text: FPS.str(d['Product Name'], 'Unnamed product') }),
                           el('div', { class: 'meta', text: [FPS.str(d['Veg Status']), when].filter(Boolean).join(' · ') })]),
            btn
        ]);
    }

    function fill(listId, emptyId, items) {
        var list = document.getElementById(listId);
        list.textContent = '';
        items.forEach(function (item) { if (item && item.data) list.appendChild(row(item)); });
        document.getElementById(emptyId).classList.toggle('is-hidden', items.length > 0);
    }

    function draw() {
        fill('recent-list', 'recent-empty', FPS.store.recent().slice(0, 20));
        fill('fav-list', 'fav-empty', FPS.store.saved());
    }

    document.getElementById('clear-btn').addEventListener('click', function () {
        if (!window.confirm('Delete all scans and saved products from this browser?')) return;
        if (FPS.store.clear()) {
            draw();
            resultBox.textContent = '';
            resultBox.appendChild(el('p', { class: 'muted', text: 'Choose a product to see its details.' }));
            clearStatus('Your history has been deleted.', 'ok');
        } else {
            clearStatus('Could not delete. Try clearing this site\'s data in your browser settings.', 'err');
        }
    });

    draw();
})();
