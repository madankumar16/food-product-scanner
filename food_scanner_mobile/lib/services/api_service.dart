import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/product.dart';

class ApiService {
  /// The live site. For a local server, run with
  /// --dart-define=API_BASE_URL=http://10.0.2.2:5000 (Android emulator).
  static const String defaultBaseUrl =
      String.fromEnvironment('API_BASE_URL', defaultValue: 'https://fopack-scanner.vercel.app');

  String _baseUrl = defaultBaseUrl;

  ApiService({String? baseUrl}) {
    if (baseUrl != null) {
      _baseUrl = baseUrl;
    }
  }

  String get baseUrl => _baseUrl;

  void setBaseUrl(String url) {
    _baseUrl = url;
  }

  /// Send any scanned code (barcode number, QR text, typed text) with the
  /// format the scanner reported, e.g. 'qrCode', 'ean13', or 'typed'.
  Future<Product> scanCode(String code, {String? format}) async {
    final url = Uri.parse('$_baseUrl/scan');
    final http.Response response;
    try {
      response = await http
          .post(
            url,
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'code': code, 'format': format}),
          )
          .timeout(const Duration(seconds: 25));
    } catch (e) {
      throw Exception('Could not reach the server. Check your internet connection and try again.');
    }

    Map<String, dynamic> data = {};
    try {
      final decoded = jsonDecode(response.body);
      if (decoded is Map<String, dynamic>) data = decoded;
    } catch (_) {
      // not JSON
    }
    if (response.statusCode == 200 && data['success'] == true) {
      return Product.fromJson(data, code);
    }
    throw Exception(data['error'] is String ? data['error'] : 'Server error (${response.statusCode}). Please try again.');
  }

  /// Older name, kept for callers that only send numbers.
  Future<Product> scanBarcode(String barcode) => scanCode(barcode, format: 'typed');
}
