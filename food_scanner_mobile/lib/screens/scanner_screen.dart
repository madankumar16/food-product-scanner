import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import '../services/api_service.dart';
import '../services/product_provider.dart';
import 'product_detail_screen.dart';

class ScannerScreen extends StatefulWidget {
  const ScannerScreen({Key? key}) : super(key: key);

  @override
  State<ScannerScreen> createState() => _ScannerScreenState();
}

class _ScannerScreenState extends State<ScannerScreen> {
  final MobileScannerController _scannerController = MobileScannerController();
  final TextEditingController _barcodeInputController = TextEditingController();
  bool _isLoading = false;
  bool _isFlashOn = false;

  @override
  void dispose() {
    _scannerController.dispose();
    _barcodeInputController.dispose();
    super.dispose();
  }

  Future<void> _processBarcode(String barcode, ProductProvider provider) async {
    if (_isLoading || barcode.trim().isEmpty) return;

    setState(() {
      _isLoading = true;
    });

    try {
      // Pause scanner temporarily
      _scannerController.stop();

      // Retrieve backend base URL
      final apiService = ApiService(); // Uses default http://10.0.2.2:5000
      final product = await apiService.scanBarcode(barcode.trim());

      // Save to local scan history
      await provider.addToHistory(product);

      if (!mounted) return;
      
      // Clear manual input
      _barcodeInputController.clear();

      // Navigate to details screen
      await Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => ProductDetailScreen(product: product),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      showDialog(
        context: context,
        builder: (context) => AlertDialog(
          backgroundColor: const Color(0xFF1E293B),
          title: const Text('Scan Failed', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
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
        });
        // Restart scanner
        _scannerController.start();
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
            onDetect: (capture) {
              final List<Barcode> barcodes = capture.barcodes;
              if (barcodes.isNotEmpty && barcodes.first.rawValue != null) {
                final String code = barcodes.first.rawValue!;
                _processBarcode(code, provider);
              }
            },
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
              mainAxisAlignment: MainAxisAlignment.between,
              children: [
                // Top control row
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.between,
                    children: [
                      const Text(
                        'Align Barcode to Scan',
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
                        'Simulator / Manual Barcode Input',
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
                                hintText: 'Enter barcode number...',
                                hintStyle: const TextStyle(color: Colors.white30),
                                filled: true,
                                fillColor: const Color(0xFF0F172A),
                                contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                                border: OutlineInputBorder(
                                  borderRadius: BorderRadius.circular(10),
                                  borderSide: BorderSide.none,
                                ),
                              ),
                              keyboardType: TextInputType.number,
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
                      const SizedBox(height: 16),
                      
                      // Quick test codes
                      const Text(
                        'Quick Simulators:',
                        style: TextStyle(color: Colors.white38, fontSize: 12),
                      ),
                      const SizedBox(height: 8),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                        children: [
                          _buildQuickTestButton('Nutella', '3017620425035', provider),
                          _buildQuickTestButton('Coca-Cola', '5449000000996', provider),
                          _buildQuickTestButton('Oreo', '7622210449283', provider),
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
                      'Identifying product...',
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

  Widget _buildQuickTestButton(String label, String code, ProductProvider provider) {
    return ElevatedButton(
      style: ElevatedButton.styleFrom(
        backgroundColor: const Color(0xFF334155),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      ),
      onPressed: () => _processBarcode(code, provider),
      child: Text(
        label,
        style: const TextStyle(color: Colors.white70, fontSize: 12, fontWeight: FontWeight.bold),
      ),
    );
  }
}
