import 'dart:io';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';

import '../services/api_service.dart';
import '../services/app_actions.dart';
import '../services/product_provider.dart';

/// Photo tab: take a photo or pick one; the server finds the code in it
/// (it reads small, blurry or damaged codes better than the live camera).
class PhotoScreen extends StatefulWidget {
  const PhotoScreen({Key? key}) : super(key: key);

  @override
  State<PhotoScreen> createState() => _PhotoScreenState();
}

class _PhotoScreenState extends State<PhotoScreen> {
  final ImagePicker _picker = ImagePicker();
  XFile? _photo;
  bool _busy = false;
  String? _error;

  Future<void> _pick(ImageSource source) async {
    try {
      final photo = await _picker.pickImage(source: source, maxWidth: 2000, maxHeight: 2000, imageQuality: 90);
      if (photo != null) {
        setState(() {
          _photo = photo;
          _error = null;
        });
      }
    } catch (e) {
      setState(() => _error = source == ImageSource.camera
          ? 'Could not open the camera. Allow camera access in your phone settings, or choose from the gallery.'
          : 'Could not open your photos.');
    }
  }

  Future<void> _check() async {
    final photo = _photo;
    if (photo == null) return;
    final provider = context.read<ProductProvider>();
    final nav = context.read<AppNav>();
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final product = await ApiService().scanPhoto(photo.path);
      await provider.addToHistory(product);
      if (!mounted) return;
      setState(() => _photo = null);
      nav.go(AppNav.barcode);
    } catch (e) {
      if (mounted) setState(() => _error = e.toString().replaceAll('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final shape = RoundedRectangleBorder(borderRadius: BorderRadius.circular(14));
    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 4, 20, 24),
      children: [
        const Text('Photo', style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: AppColors.ink)),
        const SizedBox(height: 4),
        const Text('Take a photo of a barcode or QR code. Our server reads small or blurry codes better than the live camera.',
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
              Row(children: [
                Expanded(
                  child: SizedBox(
                    height: 52,
                    child: FilledButton.icon(
                      style: FilledButton.styleFrom(backgroundColor: AppColors.green, shape: shape),
                      onPressed: _busy ? null : () => _pick(ImageSource.camera),
                      icon: const Icon(Icons.photo_camera_outlined),
                      label: const Text('Take photo'),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: SizedBox(
                    height: 52,
                    child: OutlinedButton.icon(
                      style: OutlinedButton.styleFrom(foregroundColor: AppColors.green, shape: shape),
                      onPressed: _busy ? null : () => _pick(ImageSource.gallery),
                      icon: const Icon(Icons.photo_library_outlined),
                      label: const Text('Gallery'),
                    ),
                  ),
                ),
              ]),
              if (_photo != null) ...[
                const SizedBox(height: 16),
                ClipRRect(
                  borderRadius: BorderRadius.circular(14),
                  child: Image.file(File(_photo!.path), height: 220, fit: BoxFit.contain),
                ),
              ],
              const SizedBox(height: 16),
              SizedBox(
                height: 52,
                child: FilledButton(
                  style: FilledButton.styleFrom(backgroundColor: AppColors.green, shape: shape),
                  onPressed: _busy || _photo == null ? null : _check,
                  child: _busy
                      ? const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2.5, color: Colors.white))
                      : const Text('Check this photo', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                ),
              ),
              if (_error != null) ...[
                const SizedBox(height: 12),
                Text(_error!, style: TextStyle(color: Colors.red.shade700, fontWeight: FontWeight.w600)),
              ],
            ],
          ),
        ),
        const SizedBox(height: 16),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(color: AppColors.greenSoft, borderRadius: BorderRadius.circular(16)),
          child: const Text('The photo is checked on our server and then deleted. We don\'t keep it.',
              style: TextStyle(color: AppColors.text2, height: 1.4)),
        ),
      ],
    );
  }
}
