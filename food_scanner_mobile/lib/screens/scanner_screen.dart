import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:provider/provider.dart';

import '../models/product.dart';
import '../services/api_service.dart';
import '../services/app_actions.dart';
import '../services/product_provider.dart';

/// Home tab: Scan button, live camera card, and the last scan.
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
  // repeats are filtered in _onDetect instead.
  final MobileScannerController _controller = MobileScannerController(
    detectionSpeed: DetectionSpeed.normal,
    autoStart: false,
  );
  bool _wantCamera = false; // the user pressed Scan
  bool _busy = false; // looking up a code, or an error dialog is open
  bool _torchOn = false;
  String? _lastCode;
  DateTime _lastCodeAt = DateTime.fromMillisecondsSinceEpoch(0);

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void didUpdateWidget(covariant ScannerScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.active != oldWidget.active) {
      widget.active ? _syncCamera() : _stop();
    }
  }

  // Turn the camera off while the app is in the background. Lifecycle changes
  // are ignored until the camera is set up (the permission prompt itself makes
  // the app "inactive").
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (!_controller.value.isInitialized) return;
    if (state == AppLifecycleState.resumed) {
      _syncCamera();
    } else if (state == AppLifecycleState.paused || state == AppLifecycleState.inactive) {
      _stop();
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _controller.dispose();
    super.dispose();
  }

  bool get _shouldRun => mounted && widget.active && _wantCamera && !_busy;

  Future<void> _syncCamera() async {
    if (_shouldRun) {
      try {
        await _controller.start();
      } catch (e) {
        debugPrint('Camera start failed: $e');
        if (mounted) {
          setState(() => _wantCamera = false);
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
              content: Text('Camera access was blocked or no camera was found. Use Photo or Number instead.')));
        }
      }
    } else {
      await _stop();
    }
  }

  Future<void> _stop() async {
    try {
      await _controller.stop();
    } catch (e) {
      debugPrint('Camera stop failed: $e');
    }
    _torchOn = false;
  }

  void _toggleCamera() {
    setState(() => _wantCamera = !_wantCamera);
    _syncCamera();
  }

  Future<void> _toggleTorch() async {
    try {
      await _controller.toggleTorch();
      setState(() => _torchOn = !_torchOn);
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('This camera has no flash.')));
    }
  }

  void _onDetect(BarcodeCapture capture) {
    if (!_shouldRun) return;
    final barcodes = capture.barcodes.where((b) => (b.rawValue ?? '').trim().isNotEmpty).toList();
    if (barcodes.isEmpty) return;
    final code = barcodes.first.rawValue!;
    // The camera reports the same code many times a second: handle it once,
    // but allow scanning it again a few seconds later.
    final now = DateTime.now();
    if (code == _lastCode && now.difference(_lastCodeAt) < const Duration(seconds: 3)) return;
    _lastCode = code;
    _lastCodeAt = now;
    _lookUp(code, barcodes.first.format.name);
  }

  Future<void> _lookUp(String code, String format) async {
    final provider = context.read<ProductProvider>();
    final nav = context.read<AppNav>();
    setState(() => _busy = true);
    await _stop();
    try {
      final product = await ApiService().scanCode(code, format: format);
      await provider.addToHistory(product);
      if (!mounted) return;
      setState(() => _wantCamera = false); // camera off; the result opens on the Barcode tab
      nav.go(AppNav.barcode);
    } catch (e) {
      if (!mounted) return;
      await showDialog(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Scan failed'),
          content: Text(e.toString().replaceAll('Exception: ', '')),
          actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('OK'))],
        ),
      );
    } finally {
      if (mounted) {
        setState(() => _busy = false);
        _lastCodeAt = DateTime.now(); // don't instantly re-read the code still in front of the camera
        await _syncCamera();
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<ProductProvider>();
    final last = provider.history.isNotEmpty ? provider.history.first : null;
    final live = _wantCamera && widget.active;

    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 4, 20, 24),
      children: [
        SizedBox(
          height: 80,
          child: FilledButton.icon(
            style: FilledButton.styleFrom(
              backgroundColor: AppColors.green,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
              textStyle: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            onPressed: _busy ? null : _toggleCamera,
            icon: Icon(live ? Icons.stop_circle_outlined : Icons.qr_code_scanner, size: 32),
            label: Text(live ? 'Stop' : 'Scan'),
          ),
        ),
        const SizedBox(height: 20),
        AspectRatio(
          aspectRatio: 1 / 0.92,
          child: ClipRRect(
            borderRadius: BorderRadius.circular(28),
            child: Container(
              color: AppColors.camera,
              child: Stack(
                fit: StackFit.expand,
                children: [
                  // Always in the tree so start() has a preview to attach to; it's dark until started.
                  MobileScanner(controller: _controller, onDetect: _onDetect),
                  const IgnorePointer(child: CustomPaint(painter: _ScanFramePainter())),
                  if (live)
                    Positioned(
                      left: 20,
                      top: 20,
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                        decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(99)),
                        child: const Row(children: [
                          Icon(Icons.circle, color: Color(0xFFEF5350), size: 12),
                          SizedBox(width: 8),
                          Text('Camera live', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
                        ]),
                      ),
                    ),
                  if (live)
                    Positioned(
                      right: 16,
                      top: 16,
                      child: IconButton.filled(
                        style: IconButton.styleFrom(
                          backgroundColor: _torchOn ? const Color(0xFFFDE68A) : Colors.white24,
                          foregroundColor: _torchOn ? AppColors.ink : Colors.white,
                          fixedSize: const Size(56, 56),
                        ),
                        tooltip: 'Flash',
                        onPressed: _toggleTorch,
                        icon: const Icon(Icons.flash_on_outlined),
                      ),
                    ),
                  Positioned(
                    left: 16,
                    right: 16,
                    bottom: 20,
                    child: Text(
                      _busy
                          ? 'Checking...'
                          : live
                              ? 'Hold steady — scanning automatically'
                              : 'Press Scan to turn on the camera',
                      textAlign: TextAlign.center,
                      style: const TextStyle(color: Color(0xFFE8EFE9), fontSize: 16),
                    ),
                  ),
                  if (_busy) const Center(child: CircularProgressIndicator(color: AppColors.mint)),
                ],
              ),
            ),
          ),
        ),
        const SizedBox(height: 20),
        LastScanCard(product: last),
      ],
    );
  }
}

/// Mint corner brackets and a scan line, like a viewfinder.
class _ScanFramePainter extends CustomPainter {
  const _ScanFramePainter();

  @override
  void paint(Canvas canvas, Size size) {
    final p = Paint()
      ..color = AppColors.mint
      ..strokeWidth = 5
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;
    final r = Rect.fromLTRB(size.width * .18, size.height * .22, size.width * .82, size.height * .74);
    final cw = r.width * .18, ch = r.height * .22;
    for (final c in [
      [r.topLeft, Offset(cw, 0), Offset(0, ch)],
      [r.topRight, Offset(-cw, 0), Offset(0, ch)],
      [r.bottomLeft, Offset(cw, 0), Offset(0, -ch)],
      [r.bottomRight, Offset(-cw, 0), Offset(0, -ch)],
    ]) {
      canvas.drawLine(c[0], c[0] + c[1], p);
      canvas.drawLine(c[0], c[0] + c[2], p);
    }
    final y = r.center.dy;
    canvas.drawLine(Offset(r.left + r.width * .06, y), Offset(r.right - r.width * .06, y), p..strokeWidth = 3);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

/// The card under the camera: ingredient score, Nutri-Score A–E and sugar,
/// fat and salt for food; title and warning for anything else. Only shows
/// what the scan actually contained.
class LastScanCard extends StatelessWidget {
  final Product? product;

  const LastScanCard({Key? key, required this.product}) : super(key: key);

  static const _grades = ['A', 'B', 'C', 'D', 'E'];
  static const _soft = [Color(0xFFA3C9B1), Color(0xFFB8D99A), Color(0xFFF2DC8C), Color(0xFFF1C39B), Color(0xFFEBA8A3)];
  static const _strong = [Color(0xFF166534), Color(0xFF4D8A1F), Color(0xFF8A6D00), Color(0xFFA34A12), Color(0xFFA42121)];

  String _grams(Map<String, dynamic> n, String key) {
    final v = n[key];
    return v is num ? '${v.toStringAsFixed(v < 10 ? 1 : 0)} g' : 'Not listed';
  }

  @override
  Widget build(BuildContext context) {
    final p = product;
    final eyebrow = TextStyle(color: AppColors.text2, fontSize: 13, fontWeight: FontWeight.w600, letterSpacing: 1.2);
    final children = <Widget>[];

    if (p == null) {
      children.addAll([
        Text('LAST SCAN', style: eyebrow),
        const SizedBox(height: 4),
        const Text('No scan yet', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: AppColors.ink)),
        const SizedBox(height: 4),
        const Text('Scan any barcode or QR code and the result shows here.', style: TextStyle(color: AppColors.text2)),
      ]);
    } else {
      children.add(Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('LAST SCAN · ${p.kindLabel.toUpperCase()}', style: eyebrow),
              const SizedBox(height: 4),
              Text(p.name, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: AppColors.ink)),
              if (!p.isFood && p.brand != null) Text(p.brand!, style: const TextStyle(color: AppColors.text2)),
            ]),
          ),
          if (p.isFood && p.safetyScore != null)
            Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
              Text.rich(TextSpan(children: [
                TextSpan(
                    text: '${p.safetyScore}',
                    style: const TextStyle(fontSize: 48, fontWeight: FontWeight.bold, color: AppColors.green, height: 1)),
                const TextSpan(text: '/100', style: TextStyle(fontSize: 16, color: AppColors.text2)),
              ])),
              const Text('Ingredient score', style: TextStyle(fontSize: 12, color: AppColors.text2)),
            ]),
        ],
      ));
      if (p.warning != null) {
        children.add(Padding(
          padding: const EdgeInsets.only(top: 12),
          child: Text(p.warning!, style: TextStyle(color: Colors.red.shade700, fontWeight: FontWeight.bold)),
        ));
      }
      if (p.isFood) {
        final grade = (p.nutriscore ?? '').toUpperCase();
        children.add(const SizedBox(height: 16));
        children.add(Row(
          children: List.generate(5, (i) {
            final on = _grades[i] == grade;
            return Expanded(
              child: Container(
                height: 46,
                margin: EdgeInsets.only(right: i < 4 ? 6 : 0),
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: on ? _strong[i] : _soft[i],
                  borderRadius: BorderRadius.circular(12),
                  border: on ? Border.all(color: AppColors.ink, width: 3) : null,
                ),
                child: Text(_grades[i],
                    style: TextStyle(
                        fontSize: 20, fontWeight: FontWeight.bold, color: on ? Colors.white : AppColors.ink.withOpacity(.55))),
              ),
            );
          }),
        ));
        if (!_grades.contains(grade)) {
          children.add(const Padding(
            padding: EdgeInsets.only(top: 8),
            child: Text('Nutri-Score: not enough nutrition data.', style: TextStyle(color: AppColors.text2)),
          ));
        }
        final off = p.raw?['open_food_facts'];
        final n = off is Map && off['nutriments'] is Map ? Map<String, dynamic>.from(off['nutriments']) : <String, dynamic>{};
        children.add(const SizedBox(height: 16));
        children.add(Row(
          children: [
            for (final m in const [['Sugar', 'sugars_100g'], ['Fat', 'fat_100g'], ['Salt', 'salt_100g']])
              Expanded(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(m[0], style: const TextStyle(color: AppColors.text2)),
                  Text(_grams(n, m[1]),
                      style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppColors.ink)),
                ]),
              ),
          ],
        ));
      } else {
        children.add(const Padding(
          padding: EdgeInsets.only(top: 8),
          child: Text('Open the Barcode tab for the details.', style: TextStyle(color: AppColors.text2)),
        ));
      }
    }

    return Material(
      color: AppColors.card,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
        side: const BorderSide(color: AppColors.line),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(20),
        onTap: p == null ? null : () => context.read<AppNav>().go(AppNav.barcode),
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: children),
        ),
      ),
    );
  }
}
