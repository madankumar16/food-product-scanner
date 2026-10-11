import 'dart:convert';
import 'dart:typed_data';
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
    final http.Response response;
    try {
      response = await http
          .post(
            Uri.parse('$_baseUrl/scan'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'code': code, 'format': format}),
          )
          .timeout(const Duration(seconds: 25));
    } catch (e) {
      throw Exception('Could not reach the server. Check your internet connection and try again.');
    }
    return _toProduct(response, code);
  }

  /// Send a photo; the server finds any barcode or QR code in it.
  Future<Product> scanPhoto(String path) async {
    final http.Response response;
    try {
      final request = http.MultipartRequest('POST', Uri.parse('$_baseUrl/scan'))
        ..files.add(await http.MultipartFile.fromPath('image', path, filename: 'photo.jpg'));
      response = await http.Response.fromStream(await request.send().timeout(const Duration(seconds: 40)));
    } catch (e) {
      throw Exception('Could not send the photo. Check your internet connection and try again.');
    }
    return _toProduct(response, '');
  }

  /// PDF report of a scan result (the server builds it and keeps nothing).
  Future<Uint8List> reportPdf(Map<String, dynamic> result) async {
    final http.Response response;
    try {
      response = await http
          .post(
            Uri.parse('$_baseUrl/api/report/pdf'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(result),
          )
          .timeout(const Duration(seconds: 25));
    } catch (e) {
      throw Exception('Could not reach the server. Check your internet connection and try again.');
    }
    if (response.statusCode == 200 && response.bodyBytes.length > 4) return response.bodyBytes;
    throw Exception('The report could not be created. Please try again.');
  }

  Product _toProduct(http.Response response, String scanned) {
    Map<String, dynamic> data = {};
    try {
      final decoded = jsonDecode(response.body);
      if (decoded is Map<String, dynamic>) data = decoded;
    } catch (_) {
      // not JSON
    }
    if (response.statusCode == 200 && data['success'] == true) {
      return Product.fromJson(data, scanned);
    }
    throw Exception(data['error'] is String ? data['error'] : 'Server error (${response.statusCode}). Please try again.');
  }

  /// Older name, kept for callers that only send numbers.
  Future<Product> scanBarcode(String barcode) => scanCode(barcode, format: 'typed');
}
