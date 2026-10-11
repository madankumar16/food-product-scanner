// Scan page: camera (in-browser reading of any barcode or QR code), photo upload, typed code.
(function () {
    'use strict';
    var status = FPS.statusFn(document.getElementById('status'));
    var resultBox = document.getElementById('result');
    var resultPanel = document.getElementById('result-panel');
    var busy = false;

    // ---------- tabs (arrow keys move between them) ----------
    var tabs = Array.prototype.slice.call(document.querySelectorAll('[role="tab"]'));
    function select(tab) {
        tabs.forEach(function (t) {
            var on = t === tab;
            t.setAttribute('aria-selected', on ? 'true' : 'false');
            t.tabIndex = on ? 0 : -1;
            document.getElementById(t.getAttribute('aria-controls')).classList.toggle('is-hidden', !on);
        });
        if (tab.id !== 'tab-camera') stopCamera();
    }
    tabs.forEach(function (tab, i) {
        tab.addEventListener('click', function () { select(tab); });
        tab.addEventListener('keydown', function (e) {
            var next = e.key === 'ArrowRight' ? tabs[(i + 1) % tabs.length] : e.key === 'ArrowLeft' ? tabs[(i - 1 + tabs.length) % tabs.length] : null;
            if (next) { e.preventDefault(); select(next); next.focus(); }
        });
    });

    // ---------- talking to the server ----------
    async function send(body, isForm) {
        if (busy) return;
        busy = true;
        status('Checking…');
        try {
            var res = await fetch('/scan', isForm ? { method: 'POST', body: body }
                                                 : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
            var data = {};
            try { data = await res.json(); } catch (e) { /* not JSON */ }
            if (res.ok && data.success) {
                FPS.store.addRecent(data);
                FPS.render(resultBox, data, { status: status });
                status('Found it.', 'ok');
                resultPanel.focus({ preventScroll: false });
            } else {
                status(FPS.str(data.error, 'Something went wrong. Please try again.'), 'err');
            }
        } catch (e) {
            status('Could not reach the server. Check your connection and try again.', 'err');
        }
        busy = false;
    }

    // ---------- typed barcode ----------
    var form = document.getElementById('barcode-form');
    var input = document.getElementById('barcode-input');
    form.addEventListener('submit', function (e) {
        e.preventDefault();
        var code = input.value.trim();
        if (!code) {
            status('Type the numbers under the barcode, or the text of the code.', 'err');
            input.setAttribute('aria-invalid', 'true');
            input.focus();
            return;
        }
        input.removeAttribute('aria-invalid');
        send({ code: code, format: 'typed' });
    });

    // ---------- photo ----------
    var photoInput = document.getElementById('photo-input');
    var preview = document.getElementById('photo-preview');
    var photoBtn = document.getElementById('photo-btn');
    var drop = document.getElementById('drop');
    var chosen = null;

    function choose(file) {
        if (!file) return;
        if (!/^image\/(jpeg|png|webp)$/.test(file.type)) { status('Please choose a JPEG, PNG or WebP photo.', 'err'); return; }
        chosen = file;
        if (preview.src) URL.revokeObjectURL(preview.src);
        preview.src = URL.createObjectURL(file);
        preview.classList.remove('is-hidden');
        photoBtn.disabled = false;
        status('Photo ready.');
    }
    photoInput.addEventListener('change', function () { choose(photoInput.files[0]); });
    ['dragenter', 'dragover'].forEach(function (ev) { drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.add('dragging'); }); });
    ['dragleave', 'drop'].forEach(function (ev) { drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.remove('dragging'); }); });
    drop.addEventListener('drop', function (e) { choose(e.dataTransfer.files[0]); });

    // Shrink big phone photos before upload: faster, cheaper, under the 4 MB limit.
    function shrink(file) {
        return new Promise(function (resolve) {
            var img = new Image();
            img.onload = function () {
                var scale = Math.min(1, 2000 / Math.max(img.width, img.height));
                var c = document.createElement('canvas');
                c.width = Math.round(img.width * scale); c.height = Math.round(img.height * scale);
                c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
                c.toBlob(function (b) { resolve(b || file); }, 'image/jpeg', 0.88);
            };
            img.onerror = function () { resolve(file); };
            img.src = preview.src;
        });
    }
    photoBtn.addEventListener('click', async function () {
        if (!chosen) return;
        photoBtn.disabled = true;
        var fd = new FormData();
        fd.append('image', await shrink(chosen), 'photo.jpg');
        await send(fd, true);
        photoBtn.disabled = false;
    });

    // ---------- live camera (decoding happens in the browser) ----------
    var cameraBtn = document.getElementById('camera-btn');
    var cameraLabel = document.getElementById('camera-label');
    var placeholder = document.getElementById('camera-placeholder');
    var scanner = null, running = false, lastCode = null;

    async function startCamera() {
        if (typeof Html5Qrcode === 'undefined') { status('The scanner could not load. Use "Type it" instead.', 'err'); return; }
        if (!window.isSecureContext) { status('The camera only works over https.', 'err'); return; }
        cameraBtn.disabled = true;
        status('Asking for camera permission…');
        // No format list: every barcode and 2D code the library knows (QR, Data Matrix, PDF417,
        // Aztec, EAN/UPC, Code 128/39/93, ITF, Codabar, GS1 DataBar...).
        scanner = scanner || new Html5Qrcode('reader', {
            verbose: false,
            experimentalFeatures: { useBarCodeDetectorIfSupported: true }
        });
        try {
            await scanner.start({ facingMode: 'environment' }, {
                fps: 10,
                qrbox: function (w, h) { var s = Math.floor(Math.min(w, h) * 0.8); return { width: Math.min(w - 20, Math.floor(s * 1.25)), height: s }; }
            }, onCode, function () {});
            running = true;
            placeholder.classList.add('is-hidden');
            cameraLabel.textContent = 'Stop camera';
            status('Point the camera at any barcode or QR code.');
        } catch (e) {
            status('Camera access was blocked or no camera was found. Try "Photo" or "Type it".', 'err');
        }
        cameraBtn.disabled = false;
    }
    async function stopCamera() {
        if (!scanner || !running) return;
        try { await scanner.stop(); } catch (e) { /* already stopped */ }
        running = false;
        placeholder.classList.remove('is-hidden');
        cameraLabel.textContent = 'Start camera';
    }
    function onCode(text, result) {
        var code = String(text || '');
        if (!code.trim() || code === lastCode || busy) return;
        lastCode = code;
        setTimeout(function () { lastCode = null; }, 4000);
        var format = result && result.result && result.result.format && result.result.format.formatName;
        stopCamera();
        send({ code: code, format: typeof format === 'string' ? format : null });
    }
    cameraBtn.addEventListener('click', function () { if (running) stopCamera(); else startCamera(); });
    window.addEventListener('pagehide', stopCamera);
})();
