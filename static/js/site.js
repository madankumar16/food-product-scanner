// The ⋮ menu (Download PDF report, History, Nutri-Score) and the storage notice.
// No tracking of any kind.
(function () {
    var menuBtn = document.getElementById('menu-btn');
    var menu = document.getElementById('app-menu');
    function setMenu(open, focusFirst) {
        menu.classList.toggle('is-hidden', !open);
        menuBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
        if (open && focusFirst) {
            var first = menu.querySelector('button:not([disabled]), a');
            if (first) first.focus();
        }
    }
    if (menuBtn && menu) {
        menuBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            setMenu(menu.classList.contains('is-hidden'), true);
        });
        document.addEventListener('click', function (e) { if (!menu.contains(e.target)) setMenu(false); });
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && !menu.classList.contains('is-hidden')) { setMenu(false); menuBtn.focus(); }
        });
    }

    // PDF of the result on screen, or of the latest scan on other pages.
    var pdfBtn = document.getElementById('pdf-btn');
    if (pdfBtn && window.FPS) {
        var refresh = function () { pdfBtn.disabled = !FPS.current(); };
        refresh();
        document.addEventListener('fps:result', refresh);
        pdfBtn.addEventListener('click', function () {
            var data = FPS.current();
            setMenu(false);
            if (data) FPS.downloadPdf(data, pdfBtn, null);
        });
    }

    var notice = document.getElementById('cookie-notice');
    var ok = document.getElementById('cookie-ok');
    var KEY = 'notice-dismissed';
    var dismissed = false;
    try { dismissed = localStorage.getItem(KEY) === '1'; } catch (e) { /* storage blocked */ }
    if (notice && ok && !dismissed) {
        notice.classList.remove('is-hidden');
        ok.addEventListener('click', function () {
            notice.classList.add('is-hidden');
            try { localStorage.setItem(KEY, '1'); } catch (e) { /* storage blocked */ }
        });
    }
})();
