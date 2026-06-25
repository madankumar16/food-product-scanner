// HTML5 Barcode Scanner Handler - wraps html5-qrcode library for real-time camera decoding

let html5QrCode = null;
let currentCameraId = null;
let cameraDevices = [];
let isScanning = false;

document.addEventListener('DOMContentLoaded', function() {
    // Bind camera switcher button
    const switchCameraBtn = document.getElementById('switchCameraBtn');
    if (switchCameraBtn) {
        switchCameraBtn.addEventListener('click', switchCamera);
    }
});

async function startLiveCamera() {
    try {
        if (isScanning) {
            console.log('Scanner already running');
            return true;
        }

        const qrReader = document.getElementById('qr-reader');
        if (!qrReader) return false;

        // Reset scanning state
        isScanning = true;
        
        // Initialize Html5Qrcode
        if (!html5QrCode) {
            html5QrCode = new Html5Qrcode("qr-reader");
        }

        // Get available cameras
        cameraDevices = await Html5Qrcode.getCameras();
        if (!cameraDevices || cameraDevices.length === 0) {
            throw new Error("No cameras found");
        }

        // Find back camera if available, otherwise use the first one
        let selectedCamera = cameraDevices[0];
        const backCamera = cameraDevices.find(device => 
            device.label.toLowerCase().includes('back') || 
            device.label.toLowerCase().includes('environment') ||
            device.label.toLowerCase().includes('rear')
        );
        if (backCamera) {
            selectedCamera = backCamera;
        }
        currentCameraId = selectedCamera.id;

        // Configure scanner
        const config = {
            fps: 15,
            qrbox: function(width, height) {
                // Barcode scanner box (wider than tall)
                const sizeW = Math.min(width, 450) * 0.8;
                const sizeH = Math.min(height, 250) * 0.45;
                return { width: sizeW, height: sizeH };
            },
            aspectRatio: 1.333333
        };

        // Start scanning
        await html5QrCode.start(
            currentCameraId,
            config,
            onBarcodeDetected,
            onBarcodeError
        );

        console.log("Real-time HTML5 barcode scanner started on camera:", selectedCamera.label);
        return true;
    } catch (error) {
        console.error("Failed to start barcode scanner:", error);
        isScanning = false;
        alert("Camera Error: " + error.message + "\n\nPlease ensure you have granted camera permissions.");
        return false;
    }
}

function stopLiveCamera() {
    try {
        isScanning = false;
        if (html5QrCode && html5QrCode.isScanning) {
            html5QrCode.stop().then(() => {
                console.log("HTML5 barcode scanner stopped");
            }).catch(err => {
                console.error("Error stopping scanner:", err);
            });
        }
    } catch (error) {
        console.error("Error in stopLiveCamera:", error);
    }
}

// Switch between cameras
async function switchCamera() {
    if (!html5QrCode || cameraDevices.length <= 1) {
        console.log("Cannot switch camera: not initialized or only 1 camera available");
        return;
    }

    try {
        // Stop current scanner
        await html5QrCode.stop();
        
        // Find next camera in list
        const currentIndex = cameraDevices.findIndex(device => device.id === currentCameraId);
        const nextIndex = (currentIndex + 1) % cameraDevices.length;
        const nextCamera = cameraDevices[nextIndex];
        currentCameraId = nextCamera.id;

        // Configure and restart scanner
        const config = {
            fps: 15,
            qrbox: function(width, height) {
                const sizeW = Math.min(width, 450) * 0.8;
                const sizeH = Math.min(height, 250) * 0.45;
                return { width: sizeW, height: sizeH };
            },
            aspectRatio: 1.333333
        };

        await html5QrCode.start(
            currentCameraId,
            config,
            onBarcodeDetected,
            onBarcodeError
        );
        console.log("Switched scanner to camera:", nextCamera.label);
    } catch (error) {
        console.error("Failed to switch camera:", error);
        alert("Failed to switch camera: " + error.message);
    }
}

// Beep sound effect on barcode match
function playBeep() {
    try {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioCtx.createOscillator();
        const gainNode = audioCtx.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(audioCtx.destination);

        oscillator.type = 'sine';
        oscillator.frequency.setValueAtTime(880, audioCtx.currentTime); // A5 note (crisp beep)
        gainNode.gain.setValueAtTime(0.1, audioCtx.currentTime);

        oscillator.start();
        oscillator.stop(audioCtx.currentTime + 0.15); // Beep duration 150ms
    } catch (e) {
        console.warn("Failed to play beep audio:", e);
    }
}

// Scan success callback
function onBarcodeDetected(decodedText, decodedResult) {
    if (!isScanning) return;
    
    console.log(`Barcode found: ${decodedText}`, decodedResult);
    playBeep();
    
    // Set isScanning to false to prevent multiple triggers
    isScanning = false;
    
    // Stop scanner and send barcode to server
    if (html5QrCode) {
        html5QrCode.stop().then(() => {
            // Trigger backend lookup
            handleBarcodeScan(decodedText);
        }).catch(err => {
            console.error("Error stopping scanner after detection:", err);
            // Fallback: trigger backend anyway
            handleBarcodeScan(decodedText);
        });
    } else {
        handleBarcodeScan(decodedText);
    }
}

function onBarcodeError(errorMessage) {
    // Noise/parsing errors occur frequently while scanning, ignore them to keep scanner active
}

async function handleBarcodeScan(barcode) {
    // Show loading overlay
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) loadingOverlay.style.display = 'flex';
    
    try {
        const response = await fetch('/scan', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                type: 'barcode',
                barcode: barcode
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Call dashboard function to show results
            if (typeof showScanResults === 'function') {
                showScanResults(result.result, result.scan_id);
            }
            if (typeof updateRecentScans === 'function') {
                updateRecentScans();
            }
            if (typeof updateStats === 'function') {
                updateStats();
            }
        } else {
            alert(`Product Not Found: ${result.error || 'The scanned product is not in the global database.'}\n\nYou can try manual barcode search or entry.`);
            // Restart scanning after alert is closed
            startLiveCamera();
        }
    } catch (error) {
        console.error('Barcode scanner API error:', error);
        alert('An error occurred during barcode analysis. Please check your connection.');
        // Restart scanning after alert is closed
        startLiveCamera();
    } finally {
        if (loadingOverlay) loadingOverlay.style.display = 'none';
    }
}