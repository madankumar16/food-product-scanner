// Result page: shows the latest scan from this browser's storage.
(function () {
    'use strict';
    var box = document.getElementById('result');
    var status = FPS.statusFn(document.getElementById('status'));
    var latest = FPS.store.recent()[0];
    if (latest && latest.data) {
        FPS.render(box, latest.data, { status: status });
    }
})();
