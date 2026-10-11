// Scanning: live camera on Home, typed codes on Number, photos on Photo.
// Each part only runs if its elements are on the page.
// A successful scan is saved in this browser and shown on the Result page.
(function () {
    'use strict';
    var status = FPS.statusFn(document.getElementById('status'));
    var busy = false;

    // ---------- talking to the server ----------
    async function send(body, isForm) {
        if (busy) return false;
        busy = true;
        status('Checking…');
        try {
            var res = await fetch('/scan', isForm ? { method: 'POST', body: body }
                                                 : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
            var data = {};
            try { data = await res.json(); } catch (e) { /* not JSON */ }
            if (res.ok && data.success) {
                FPS.store.addRecent(data);
                status('Found it. Opening the result…', 'ok');
                window.location.href = '/result';
                return true;
            }
            status(FPS.str(data.error, 'Something went wrong. Please try again.'), 'err');
        } catch (e) {
            status('Could not reach the server. Check your connection and try again.', 'err');
        }
        busy = false;
        return false;
    }

    // Shrink big phone photos before upload: faster, and under the 4 MB limit.
    function shrink(source) {
        return new Promise(function (resolve) {
            var url = URL.createObjectURL(source);
            var img = new Image();
            img.onload = function () {
                var scale = Math.min(1, 2000 / Math.max(img.width, img.height));
                var c = document.createElement('canvas');
                c.width = Math.round(img.width * scale); c.height = Math.round(img.height * scale);
                c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
                URL.revokeObjectURL(url);
                c.toBlob(function (b) { resolve(b || source); }, 'image/jpeg', 0.9);
            };
            img.onerror = function () { URL.revokeObjectURL(url); resolve(source); };
            img.src = url;
        });
    }
    function okType(file) { return file && /^image\/(jpeg|png|webp)$/.test(file.type); }
    async function sendPhoto(file) {
        var fd = new FormData();
        fd.append('image', await shrink(file), 'photo.jpg');
        return send(fd, true);
    }

    // ---------- typed code (Number page) ----------
    var form = document.getElementById('barcode-form');
    if (form) {
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
    }

    // ---------- photo: camera or gallery (Photo page) ----------
    var photoInput = document.getElementById('photo-input');
    var cameraInput = document.getElementById('camera-input');
    if (photoInput) {
        var preview = document.getElementById('photo-preview');
        var photoBtn = document.getElementById('photo-btn');
        var drop = document.getElementById('drop');
        var chosen = null;
        var choose = function (file) {
            if (!file) return;
            if (!okType(file)) { status('Please choose a JPEG, PNG or WebP photo.', 'err'); return; }
            chosen = file;
            if (preview.src) URL.revokeObjectURL(preview.src);
            preview.src = URL.createObjectURL(file);
            preview.classList.remove('is-hidden');
            photoBtn.disabled = false;
            status('Photo ready.');
        };
        photoInput.addEventListener('change', function () { choose(photoInput.files[0]); });
        if (cameraInput) cameraInput.addEventListener('change', function () { choose(cameraInput.files[0]); });
        ['dragenter', 'dragover'].forEach(function (ev) { drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.add('dragging'); }); });
        ['dragleave', 'drop'].forEach(function (ev) { drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.remove('dragging'); }); });
        drop.addEventListener('drop', function (e) { choose(e.dataTransfer.files[0]); });
        photoBtn.addEventListener('click', async function () {
            if (!chosen) return;
            photoBtn.disabled = true;
            if (!(await sendPhoto(chosen))) photoBtn.disabled = false;
        });
    }

    // ---------- live camera (Home) ----------
    var cameraBtn = document.getElementById('camera-btn');
    if (!cameraBtn) return;
    var cameraLabel = document.getElementById('camera-label');
    var cameraBox = document.getElementById('camera-box');
    var livePill = document.getElementById('live-pill');
    var hint = document.getElementById('camera-hint');
    var torchBtn = document.getElementById('torch-btn');
    var scanner = null, running = false, lastCode = null, torchOn = false;
    var candidate = null, candidateHits = 0;

    // Every symbology people meet in daily life. Left out on purpose: UPC/EAN
    // add-on extensions (they read the small 2/5-digit block as its own code)
    // and MaxiCode (parcel labels; the browser decoder can't read it anyway).
    function cameraFormats() {
        var F = Html5QrcodeSupportedFormats;
        return [F.QR_CODE, F.DATA_MATRIX, F.AZTEC, F.PDF_417,
                F.EAN_13, F.EAN_8, F.UPC_A, F.UPC_E,
                F.CODE_128, F.CODE_39, F.CODE_93, F.ITF, F.CODABAR, F.RSS_14, F.RSS_EXPANDED]
            .filter(function (f) { return f !== undefined; });
    }

    // EAN/UPC have a check digit and 2D codes have error correction, so one
    // read is enough. Other 1D codes (Code 39, ITF, Codabar...) have no
    // reliable check, and a blurry frame can produce a wrong value, so they
    // must read the same twice in a row.
    var SELF_CHECKING = /^(QR_CODE|DATA_MATRIX|AZTEC|PDF_417|EAN_13|EAN_8|UPC_A|UPC_E|RSS_14|RSS_EXPANDED|CODE_128)$/;
    function gtinOk(digits) {
        if (!/^(\d{8}|\d{12,14})$/.test(digits)) return false;
        var sum = 0;
        for (var i = digits.length - 2, w = 3; i >= 0; i--, w = 4 - w) sum += (+digits[i]) * w;
        return (10 - sum % 10) % 10 === +digits[digits.length - 1];
    }

    function setLive(on) {
        running = on;
        cameraBox.classList.toggle('live', on);
        livePill.classList.toggle('is-hidden', !on);
        cameraLabel.textContent = on ? 'Stop' : 'Scan';
        hint.textContent = on ? 'Hold steady — scanning automatically' : 'Press Scan to turn on the camera';
        if (!on) { torchBtn.classList.add('is-hidden'); torchOn = false; torchBtn.setAttribute('aria-pressed', 'false'); }
    }

    async function startCamera() {
        if (typeof Html5Qrcode === 'undefined') { status('The scanner could not load. Use Photo or Number instead.', 'err'); return; }
        if (!window.isSecureContext) { status('The camera only works over https.', 'err'); return; }
        cameraBtn.disabled = true;
        status('Asking for camera permission…');
        scanner = scanner || new Html5Qrcode('reader', {
            formatsToSupport: cameraFormats(),
            verbose: false,
            experimentalFeatures: { useBarCodeDetectorIfSupported: true }
        });
        candidate = null;
        try {
            // No scan box: the whole picture is searched; the frame on screen is a guide.
            await scanner.start({ facingMode: 'environment' }, { fps: 10 }, onCode, function () {});
            setLive(true);
            status('');
            // Show the flash button only if this camera has a torch.
            try {
                var caps = scanner.getRunningTrackCapabilities();
                if (caps && caps.torch) torchBtn.classList.remove('is-hidden');
            } catch (e) { /* not supported */ }
        } catch (e) {
            status('Camera access was blocked or no camera was found. Use Photo or Number instead.', 'err');
        }
        cameraBtn.disabled = false;
    }
    async function stopCamera() {
        if (!scanner || !running) return;
        setLive(false);
        try { await scanner.stop(); } catch (e) { /* already stopped */ }
    }
    torchBtn.addEventListener('click', async function () {
        if (!running) return;
        try {
            await scanner.applyVideoConstraints({ advanced: [{ torch: !torchOn }] });
            torchOn = !torchOn;
            torchBtn.setAttribute('aria-pressed', torchOn ? 'true' : 'false');
        } catch (e) {
            status('This camera has no flash.', 'err');
            torchBtn.classList.add('is-hidden');
        }
    });
    function onCode(text, result) {
        var code = String(text || '');
        if (!code.trim() || code === lastCode || busy || !running) return;
        var format = result && result.result && result.result.format && result.result.format.formatName;
        format = typeof format === 'string' ? format : '';
        // EAN/UPC whose check digit fails is a misread: wait for a clean frame.
        if (/^(EAN_13|EAN_8|UPC_A)$/.test(format) && !gtinOk(code)) return;
        if (!SELF_CHECKING.test(format)) {
            if (code !== candidate) { candidate = code; candidateHits = 1; return; }
            if (++candidateHits < 2) return;
        }
        candidate = null;
        lastCode = code;
        setTimeout(function () { lastCode = null; }, 4000);
        stopCamera();
        send({ code: code, format: format || null });
    }
    cameraBtn.addEventListener('click', function () { if (running) stopCamera(); else startCamera(); });
    window.addEventListener('pagehide', stopCamera);
})();
