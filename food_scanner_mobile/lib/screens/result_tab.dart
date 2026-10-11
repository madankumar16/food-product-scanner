import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../services/app_actions.dart';
import '../services/product_provider.dart';
import 'product_detail_screen.dart';

/// Barcode tab: the details of the latest scan.
class ResultTab extends StatelessWidget {
  const ResultTab({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<ProductProvider>();
    if (provider.history.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            const Icon(Icons.qr_code_2, size: 72, color: AppColors.line),
            const SizedBox(height: 12),
            const Text('No scan yet', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: AppColors.ink)),
            const SizedBox(height: 4),
            const Text('Scan a barcode or QR code and its details show here.',
                textAlign: TextAlign.center, style: TextStyle(color: AppColors.text2)),
            const SizedBox(height: 16),
            FilledButton(
              style: FilledButton.styleFrom(backgroundColor: AppColors.green),
              onPressed: () => context.read<AppNav>().go(AppNav.home),
              child: const Text('Go to Scan'),
            ),
          ]),
        ),
      );
    }
    final product = provider.history.first;
    // A key per scan so the screen rebuilds cleanly for each new result.
    return ProductDetailScreen(key: ValueKey('${product.barcode}-${product.name}'), product: product, embedded: true);
  }
}
