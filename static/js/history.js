// History page: everything here comes from this browser's local storage.
(function () {
    'use strict';
    var el = FPS.el;
    var resultBox = document.getElementById('result');
    var panel = document.getElementById('result-panel');
    var clearStatus = FPS.statusFn(document.getElementById('clear-status'));

    function row(item) {
        var data = item.data || {};
        var d = data.dashboard || {};
        var off = data.open_food_facts || {};
        var img = FPS.safeImage(off.image_url || (data.item && data.item.image_url));
        var title = FPS.titleOf(data);
        // Veg status only exists for food; everything else shows what kind of code it was.
        var kind = data.kind && data.kind !== 'food' ? FPS.kindLabel(data.kind) : FPS.str(d['Veg Status']);
        var when = '';
        try { when = new Date(item.at).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' }); } catch (e) { /* bad date */ }
        var btn = el('button', { class: 'link-button', type: 'button', text: 'View' });
        btn.setAttribute('aria-label', 'View ' + title);
        btn.addEventListener('click', function () {
            FPS.render(resultBox, item.data, { onChange: draw, status: clearStatus });
            panel.focus();
        });
        return el('li', {}, [
            img ? el('img', { src: img, alt: '', width: '56', height: '56', loading: 'lazy', referrerpolicy: 'no-referrer' }) : el('div', { class: 'no-photo', 'aria-hidden': 'true' }),
            el('div', {}, [el('div', { class: 'name', text: title }),
                           el('div', { class: 'meta', text: [kind, when].filter(Boolean).join(' · ') })]),
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
            resultBox.appendChild(el('p', { class: 'muted', text: 'Choose a scan to see its details.' }));
            clearStatus('Your history has been deleted.', 'ok');
        } else {
            clearStatus('Could not delete. Try clearing this site\'s data in your browser settings.', 'err');
        }
    });

    draw();
})();
