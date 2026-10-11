// Settings: delete everything this site saved in the browser.
(function () {
    'use strict';
    var status = FPS.statusFn(document.getElementById('clear-status'));
    document.getElementById('clear-btn').addEventListener('click', function () {
        if (!window.confirm('Delete all scans and saved items from this device?')) return;
        if (FPS.store.clear()) status('Your scans have been deleted.', 'ok');
        else status('Could not delete. Try clearing this site\'s data in your browser settings.', 'err');
    });
})();
