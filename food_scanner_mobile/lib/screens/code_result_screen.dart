import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../models/product.dart';
import '../services/product_provider.dart';

/// Results that aren't food: other products, books, links, UPI payments,
/// Wi-Fi, contacts, GS1 expiry codes, plain text, unknown barcodes.
class CodeResultScreen extends StatelessWidget {
  final Product product;

  const CodeResultScreen({Key? key, required this.product}) : super(key: key);

  static const _card = Color(0xFF1E293B);
  static const _accent = Color(0xFF38BDF8);

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
        child: Text(text, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white)),
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
                      title: Text(f[0], style: const TextStyle(color: Colors.white54, fontSize: 12)),
                      subtitle: SelectableText(f[1], style: const TextStyle(color: Colors.white, fontSize: 15)),
                      trailing: IconButton(
                        icon: const Icon(Icons.copy, size: 18, color: Colors.white38),
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
      backgroundColor: const Color(0xFF0F172A),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
        actions: [
          IconButton(
            icon: Icon(isFav ? Icons.favorite : Icons.favorite_border,
                color: isFav ? Colors.redAccent : Colors.white, size: 28),
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
                          errorBuilder: (_, __, ___) => Icon(_icon, size: 72, color: Colors.white30))
                      : Icon(_icon, size: 72, color: Colors.white30),
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
                      style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.white)),
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
                    color: Colors.redAccent.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.redAccent.withOpacity(0.5), width: 1.5),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.warning_amber_rounded, color: Colors.redAccent),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(product.warning!,
                            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, height: 1.4)),
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
                    child: Text(s[1], style: const TextStyle(color: Colors.white70, fontSize: 14, height: 1.5)),
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
                    style: const TextStyle(color: Colors.white38, fontSize: 12)),
              ),
            ...product.notes.map((n) => Padding(
                  padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
                  child: Text(n, style: const TextStyle(color: Colors.white60, fontSize: 14, height: 1.4)),
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
