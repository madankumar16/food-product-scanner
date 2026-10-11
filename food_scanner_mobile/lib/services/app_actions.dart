import 'dart:io';

import 'package:flutter/material.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';
import 'package:url_launcher/url_launcher.dart';

import '../models/product.dart';
import 'api_service.dart';

/// App colours (same as the website).
class AppColors {
  static const bg = Color(0xFFF2F4EE);
  static const card = Colors.white;
  static const green = Color(0xFF1F6B45);
  static const greenSoft = Color(0xFFE8F2EC);
  static const camera = Color(0xFF121A16);
  static const mint = Color(0xFF86D9A4);
  static const ink = Color(0xFF17221C);
  static const text2 = Color(0xFF4A5A50);
  static const line = Color(0xFFDFE5DC);
}

/// Bottom-bar tabs: Home, Number, Barcode, Photo, Settings.
class AppNav extends ChangeNotifier {
  static const home = 0, number = 1, barcode = 2, photo = 3, settings = 4;
  int _index = home;
  int get index => _index;

  void go(int i) {
    if (i == _index) return;
    _index = i;
    notifyListeners();
  }
}

/// Open a page of the website (Nutri-Score calculator, privacy, terms...).
Future<void> openSitePage(BuildContext context, String path) async {
  final uri = Uri.parse('${ApiService.defaultBaseUrl}$path');
  final ok = await launchUrl(uri, mode: LaunchMode.inAppBrowserView);
  if (!ok && context.mounted) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Could not open $uri')));
  }
}

/// Build the PDF report on the server and hand it to the share sheet, where
/// it can be saved to Files/Drive, printed or sent.
Future<void> shareReport(BuildContext context, Product? product) async {
  final messenger = ScaffoldMessenger.of(context);
  if (product == null) {
    messenger.showSnackBar(const SnackBar(content: Text('Scan something first, then download its report.')));
    return;
  }
  if (product.raw == null) {
    messenger.showSnackBar(const SnackBar(content: Text('Scan this again to make a report (older scans have no report data).')));
    return;
  }
  messenger.showSnackBar(const SnackBar(content: Text('Making the PDF report...'), duration: Duration(seconds: 2)));
  try {
    final bytes = await ApiService().reportPdf(product.raw!);
    final dir = await getTemporaryDirectory();
    final safe = product.name.replaceAll(RegExp(r'[^A-Za-z0-9]+'), '_');
    final name = '${safe.isEmpty ? 'scan' : (safe.length > 60 ? safe.substring(0, 60) : safe)}_report.pdf';
    final file = File('${dir.path}/$name');
    await file.writeAsBytes(bytes, flush: true);
    await Share.shareXFiles([XFile(file.path, mimeType: 'application/pdf')], subject: '${product.name} report');
  } catch (e) {
    messenger.showSnackBar(SnackBar(content: Text(e.toString().replaceAll('Exception: ', ''))));
  }
}
