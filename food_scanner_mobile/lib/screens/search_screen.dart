import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../services/api_service.dart';
import '../services/app_actions.dart';
import '../services/product_provider.dart';

/// Number tab: type a barcode number, ISBN or any code text.
class SearchScreen extends StatefulWidget {
  const SearchScreen({Key? key}) : super(key: key);

  @override
  State<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  final TextEditingController _controller = TextEditingController();
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _check() async {
    final code = _controller.text.trim();
    if (code.isEmpty) {
      setState(() => _error = 'Type the numbers under the barcode, or the text of the code.');
      return;
    }
    final provider = context.read<ProductProvider>();
    final nav = context.read<AppNav>();
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final product = await ApiService().scanCode(code, format: 'typed');
      await provider.addToHistory(product);
      if (!mounted) return;
      _controller.clear();
      FocusScope.of(context).unfocus();
      nav.go(AppNav.barcode);
    } catch (e) {
      if (mounted) setState(() => _error = e.toString().replaceAll('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 4, 20, 24),
      children: [
        const Text('Number', style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: AppColors.ink)),
        const SizedBox(height: 4),
        const Text('Type the digits under a barcode, an ISBN, or any text or link from a code.',
            style: TextStyle(color: AppColors.text2, fontSize: 16)),
        const SizedBox(height: 20),
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: AppColors.card,
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: AppColors.line),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              TextField(
                controller: _controller,
                enabled: !_busy,
                autocorrect: false,
                textInputAction: TextInputAction.search,
                onSubmitted: (_) => _check(),
                decoration: InputDecoration(
                  labelText: 'Barcode number or code text',
                  hintText: 'e.g. 8901058000290',
                  errorText: _error,
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),
                ),
              ),
              const SizedBox(height: 16),
              SizedBox(
                height: 52,
                child: FilledButton(
                  style: FilledButton.styleFrom(
                    backgroundColor: AppColors.green,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                  ),
                  onPressed: _busy ? null : _check,
                  child: _busy
                      ? const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2.5, color: Colors.white))
                      : const Text('Check it', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(color: AppColors.greenSoft, borderRadius: BorderRadius.circular(16)),
          child: const Text(
            'Product details come from Open Food Facts, Open Beauty Facts, Open Pet Food Facts, Open Products Facts '
            'and Open Library. Everything else is read from the code itself. Always read the pack if you have an allergy.',
            style: TextStyle(color: AppColors.text2, height: 1.4),
          ),
        ),
      ],
    );
  }
}
