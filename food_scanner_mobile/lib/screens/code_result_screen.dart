import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../models/product.dart';
import '../services/product_provider.dart';

/// Results that aren't food: other products, books, links, UPI payments,
/// Wi-Fi, contacts, GS1 expiry codes, plain text, unknown barcodes.
class CodeResultScreen extends StatelessWidget {
  final Product product;

  /// True when shown inside the Barcode tab (no back arrow).
  final bool embedded;

  const CodeResultScreen({Key? key, required this.product, this.embedded = false}) : super(key: key);

  static const _card = Color(0xFFFFFFFF);
  static const _accent = Color(0xFF1F6B45);

  IconData get _icon {
    switch (product.kind) {
      case 'product':
        return Icons.inventory_2_outlined;
      case 'book':
        return Icons.menu_book_outlined;
      default:
        return Icons.qr_code_2;
    }
  }

  void _copy(BuildContext context, String text, String what) {
    Clipboard.setData(ClipboardData(text: text));
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('$what copied'), duration: const Duration(seconds: 1)),
    );
  }

  Widget _heading(String text) => Padding(
        padding: const EdgeInsets.fromLTRB(20, 24, 20, 10),
        child: Text(text, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF17221C))),
      );

  Widget _factTable(BuildContext context, List<List<String>> facts) => Padding(
        padding: const EdgeInsets.symmetric(horizontal: 20),
        child: Container(
          width: double.infinity,
          decoration: BoxDecoration(color: _card, borderRadius: BorderRadius.circular(12)),
          child: Column(
            children: facts
                .map((f) => ListTile(
                      dense: true,
                      title: Text(f[0], style: const TextStyle(color: Color(0xFF4A5A50), fontSize: 12)),
                      subtitle: SelectableText(f[1], style: const TextStyle(color: Color(0xFF17221C), fontSize: 15)),
                      trailing: IconButton(
                        icon: const Icon(Icons.copy, size: 18, color: Color(0xFF6B7A70)),
                        tooltip: 'Copy',
                        onPressed: () => _copy(context, f[1], f[0]),
                      ),
                    ))
                .toList(),
          ),
        ),
      );

  @override
  Widget build(BuildContext context) {
    final provider = Provider.of<ProductProvider>(context);
    final isFav = provider.isFavorite(product.barcode);

    return Scaffold(
      backgroundColor: const Color(0xFFF2F4EE),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        automaticallyImplyLeading: false,
        leading: embedded
            ? null
            : IconButton(
                icon: const Icon(Icons.arrow_back, color: Color(0xFF17221C)),
                onPressed: () => Navigator.pop(context),
              ),
        actions: [
          IconButton(
            icon: Icon(isFav ? Icons.favorite : Icons.favorite_border,
                color: isFav ? Colors.red.shade700 : Color(0xFF17221C), size: 28),
            onPressed: () => provider.toggleFavorite(product),
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.only(bottom: 32),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: Container(
                margin: const EdgeInsets.symmetric(vertical: 16),
                height: 160,
                width: 160,
                decoration: BoxDecoration(color: _card, borderRadius: BorderRadius.circular(16)),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(16),
                  child: product.imageUrl != null
                      ? Image.network(product.imageUrl!,
                          fit: BoxFit.contain,
                          errorBuilder: (_, __, ___) => Icon(_icon, size: 72, color: Color(0xFF8A968E)))
                      : Icon(_icon, size: 72, color: Color(0xFF8A968E)),
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(product.kindLabel.toUpperCase(),
                      style: const TextStyle(color: _accent, fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1)),
                  const SizedBox(height: 4),
                  Text(product.name,
                      style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Color(0xFF17221C))),
                  if (product.brand != null) ...[
                    const SizedBox(height: 4),
                    Text(product.brand!, style: const TextStyle(fontSize: 16, color: _accent)),
                  ],
                ],
              ),
            ),
            if (product.warning != null)
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
                child: Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.red.shade700.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.red.shade700.withOpacity(0.5), width: 1.5),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.warning_amber_rounded, color: Colors.red.shade700),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(product.warning!,
                            style: const TextStyle(color: Color(0xFF17221C), fontWeight: FontWeight.bold, height: 1.4)),
                      ),
                    ],
                  ),
                ),
              ),
            if (product.facts.isNotEmpty) ...[
              _heading('Details'),
              _factTable(context, product.facts),
            ],
            ...product.sections.expand((s) => [
                  _heading(s[0]),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 20),
                    child: Text(s[1], style: const TextStyle(color: Color(0xFF3D4A42), fontSize: 14, height: 1.5)),
                  ),
                ]),
            if (product.link != null)
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
                child: OutlinedButton.icon(
                  icon: const Icon(Icons.link, color: _accent),
                  label: const Text('Copy link', style: TextStyle(color: _accent)),
                  onPressed: () => _copy(context, product.link!, 'Link'),
                ),
              ),
            if (product.database != null)
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
                child: Text('Source: ${product.database}${product.sourceUrl != null ? ' (${product.sourceUrl})' : ''}',
                    style: const TextStyle(color: Color(0xFF6B7A70), fontSize: 12)),
              ),
            ...product.notes.map((n) => Padding(
                  padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
                  child: Text(n, style: const TextStyle(color: Color(0xFF4A5A50), fontSize: 14, height: 1.4)),
                )),
            if (product.codeFacts.isNotEmpty) ...[
              _heading('Barcode details'),
              _factTable(context, product.codeFacts),
            ],
          ],
        ),
      ),
    );
  }
}
