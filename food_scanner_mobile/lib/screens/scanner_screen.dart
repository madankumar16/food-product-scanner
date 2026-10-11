import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import '../services/api_service.dart';
import '../services/product_provider.dart';
import 'product_detail_screen.dart';

class ScannerScreen extends StatefulWidget {
  /// False while another tab is showing: the camera is switched off so it
  /// can't pick up codes in the background.
  final bool active;

  const ScannerScreen({Key? key, this.active = true}) : super(key: key);

  @override
  State<ScannerScreen> createState() => _ScannerScreenState();
}

class _ScannerScreenState extends State<ScannerScreen> with WidgetsBindingObserver {
  // No format list: reads every 1D barcode and 2D code (QR, Data Matrix, PDF417, Aztec...).
  // `normal` speed (not `noDuplicates`) so the same product can be scanned again;
  // repeats are filtered below instead.
  final MobileScannerController _scannerController = MobileScannerController(
    detectionSpeed: DetectionSpeed.normal,
    autoStart: false,
  );
  final TextEditingController _barcodeInputController = TextEditingController();
  bool _isLoading = false;
  bool _isFlashOn = false;
  bool _showingResult = false; // a result screen or error dialog is open
  String? _lastCode;
  DateTime _lastCodeAt = DateTime.fromMillisecondsSinceEpoch(0);

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    // Start once the camera preview widget is on screen.
    WidgetsBinding.instance.addPostFrameCallback((_) => _startCamera());
  }

  // Turn the camera off while the app is in the background.
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    // Ignore lifecycle changes until the camera is set up (the permission prompt
    // itself makes the app "inactive").
    if (!_scannerController.value.isInitialized) return;
    if (state == AppLifecycleState.resumed) {
      _startCamera();
    } else if (state == AppLifecycleState.paused || state == AppLifecycleState.inactive) {
      _stopCamera();
    }
  }

  @override
  void didUpdateWidget(covariant ScannerScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.active != oldWidget.active) {
      widget.active ? _startCamera() : _stopCamera();
    }
  }

  Future<void> _startCamera() async {
    if (!mounted || !widget.active || _showingResult) return;
    try {
      await _scannerController.start();
    } catch (e) {
      debugPrint('Camera start failed: $e'); // already running, or no permission
    }
  }

  Future<void> _stopCamera() async {
    try {
      await _scannerController.stop();
    } catch (e) {
      debugPrint('Camera stop failed: $e');
    }
  }

  void _onDetect(BarcodeCapture capture, ProductProvider provider) {
    if (!widget.active || _isLoading || _showingResult) return;
    final barcodes = capture.barcodes.where((b) => (b.rawValue ?? '').trim().isNotEmpty).toList();
    if (barcodes.isEmpty) return;
    final code = barcodes.first.rawValue!;
    // The camera reports the same code many times a second: handle it once,
    // but allow scanning it again a few seconds later.
    final now = DateTime.now();
    if (code == _lastCode && now.difference(_lastCodeAt) < const Duration(seconds: 3)) return;
    _lastCode = code;
    _lastCodeAt = now;
    _processBarcode(code, provider, format: barcodes.first.format.name);
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _scannerController.dispose();
    _barcodeInputController.dispose();
    super.dispose();
  }

  Future<void> _processBarcode(String barcode, ProductProvider provider, {String? format}) async {
    if (_isLoading || barcode.trim().isEmpty) return;

    setState(() {
      _isLoading = true;
      _showingResult = true;
    });
    await _stopCamera();

    try {
      final product = await ApiService().scanCode(barcode, format: format ?? 'typed');

      // Save to local scan history
      await provider.addToHistory(product);

      if (!mounted) return;

      // Clear manual input
      _barcodeInputController.clear();

      setState(() => _isLoading = false);
      // Navigate to details screen; the camera stays off until the user comes back.
      await Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => ProductDetailScreen(product: product),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() => _isLoading = false);
      // Wait for the dialog to close before the camera starts again.
      await showDialog(
        context: context,
        builder: (context) => AlertDialog(
          backgroundColor: const Color(0xFF1E293B),
          title: const Text('Scan failed', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
          content: Text(e.toString().replaceAll('Exception: ', ''), style: const TextStyle(color: Colors.white70)),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('OK', style: TextStyle(color: Color(0xFF38BDF8))),
            ),
          ],
        ),
      );
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
          _showingResult = false;
        });
        _lastCodeAt = DateTime.now(); // don't instantly re-read the code still in front of the camera
        await _startCamera();
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final provider = Provider.of<ProductProvider>(context);

    return Scaffold(
      backgroundColor: const Color(0xFF0F172A),
      body: Stack(
        children: [
          // 1. Mobile Scanner Viewport
          MobileScanner(
            controller: _scannerController,
            onDetect: (capture) => _onDetect(capture, provider),
          ),

          // 2. Scanner Target Overlay Frame (Glassmorphism + Neon overlay)
          Container(
            color: Colors.black.withOpacity(0.5),
          ),

          // Clear scanning viewport cut-out
          Center(
            child: Container(
              width: 260,
              height: 200,
              decoration: BoxDecoration(
                border: Border.all(color: const Color(0xFF38BDF8), width: 2), // Neon border
                borderRadius: BorderRadius.circular(16),
                color: Colors.transparent,
              ),
            ),
          ),

          // 3. Scan Interface UI Controls
          SafeArea(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                // Top control row
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'Scan before use',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      IconButton(
                        icon: Icon(
                          _isFlashOn ? Icons.flash_on : Icons.flash_off,
                          color: _isFlashOn ? Colors.yellowAccent : Colors.white,
                        ),
                        onPressed: () {
                          _scannerController.toggleTorch();
                          setState(() {
                            _isFlashOn = !_isFlashOn;
                          });
                        },
                      ),
                    ],
                  ),
                ),

                // Bottom Simulator & Manual Entry Panel
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: const BoxDecoration(
                    color: Color(0xFF1E293B),
                    borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
                  ),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Text(
                        'Or type a barcode number, ISBN or any text',
                        style: TextStyle(
                          color: Colors.white70,
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Expanded(
                            child: TextField(
                              controller: _barcodeInputController,
                              style: const TextStyle(color: Colors.white),
                              decoration: InputDecoration(
                                hintText: 'e.g. 8901058000290',
                                hintStyle: const TextStyle(color: Colors.white30),
                                filled: true,
                                fillColor: const Color(0xFF0F172A),
                                contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                                border: OutlineInputBorder(
                                  borderRadius: BorderRadius.circular(10),
                                  borderSide: BorderSide.none,
                                ),
                              ),
                              keyboardType: TextInputType.text,
                            ),
                          ),
                          const SizedBox(width: 10),
                          ElevatedButton(
                            style: ElevatedButton.styleFrom(
                              backgroundColor: const Color(0xFF0284C7),
                              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                            ),
                            onPressed: () {
                              _processBarcode(_barcodeInputController.text, provider);
                            },
                            child: const Icon(Icons.arrow_forward, color: Colors.white),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),

          // 4. Loading Spinner Glass Overlay
          if (_isLoading)
            Container(
              color: Colors.black.withOpacity(0.7),
              child: const Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    CircularProgressIndicator(color: Color(0xFF38BDF8)),
                    SizedBox(height: 16),
                    Text(
                      'Checking...',
                      style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }
}
