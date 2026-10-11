// Mobile menu and the storage notice. No tracking of any kind.
(function () {
    var toggle = document.querySelector('.menu-toggle');
    var links = document.getElementById('nav-links');
    if (toggle && links) {
        toggle.addEventListener('click', function () {
            var open = links.classList.toggle('open');
            toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
        });
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && links.classList.contains('open')) {
                links.classList.remove('open');
                toggle.setAttribute('aria-expanded', 'false');
                toggle.focus();
            }
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
