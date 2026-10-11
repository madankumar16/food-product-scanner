/// One scan result from the server. `kind` says what was scanned:
/// 'food' (full food details), 'product' (cosmetics, pet food, household...),
/// 'book', or 'code' (anything else: links, UPI, Wi-Fi, text, unknown barcodes).
/// Fields the server didn't send stay null/empty. Nothing is filled in with
/// made-up defaults.
class Product {
  final String kind;
  final String barcode; // the scanned text; also the history key
  final String name;
  final String? brand;
  final String? vegStatus;
  final String? safetyColor;
  final int? safetyScore;
  final List<String> ingredients;
  final List<Map<String, dynamic>> healthWarnings;
  final String? imageUrl;
  final String? nutriscore;
  final int? novaGroup;
  final String? ecoscore;
  final String? nutriscoreCategory;
  final String? expertSummary;
  final List<String> allergens;

  // Used by every kind
  final String? warning; // e.g. "Expired on ..." or a payment/link caution
  final List<String> notes;
  final List<List<String>> codeFacts; // barcode type, check digit, expiry...
  final List<List<String>> facts; // product/book details or decoded QR content
  final List<List<String>> sections; // [heading, text], e.g. ingredients
  final String? link; // https link from a QR code, or a map link
  final String? database; // where the details came from
  final String? sourceUrl;

  Product({
    this.kind = 'food',
    required this.barcode,
    required this.name,
    this.brand,
    this.vegStatus,
    this.safetyColor,
    this.safetyScore,
    this.ingredients = const [],
    this.healthWarnings = const [],
    this.imageUrl,
    this.nutriscore,
    this.novaGroup,
    this.ecoscore,
    this.nutriscoreCategory,
    this.expertSummary,
    this.allergens = const [],
    this.warning,
    this.notes = const [],
    this.codeFacts = const [],
    this.facts = const [],
    this.sections = const [],
    this.link,
    this.database,
    this.sourceUrl,
  });

  bool get isFood => kind == 'food';

  String get kindLabel => const {
        'food': 'Food',
        'product': 'Product',
        'book': 'Book',
        'code': 'Code',
      }[kind] ??
      'Code';

  static String? _str(dynamic v) => v is String && v.trim().isNotEmpty ? v : null;

  static List<String> _strings(dynamic v) =>
      v is List ? v.whereType<String>().toList() : <String>[];

  static List<List<String>> _pairs(dynamic v) {
    if (v is! List) return [];
    return v
        .whereType<List>()
        .where((p) => p.length >= 2 && p[0] is String && p[1] is String && (p[1] as String).isNotEmpty)
        .map((p) => [p[0] as String, p[1] as String])
        .toList();
  }

  static String? _https(dynamic v) {
    final s = _str(v);
    return s != null && (s.startsWith('https://') || s.startsWith('http://')) ? s : null;
  }

  factory Product.fromJson(Map<String, dynamic> json, String scanned) {
    final kind = _str(json['kind']) ?? 'food';
    final code = json['code'] is Map ? Map<String, dynamic>.from(json['code']) : <String, dynamic>{};
    final codeText = _str(code['text']) ?? scanned;
    final common = (
      warning: _str(json['warning']),
      notes: _strings(json['notes']),
      codeFacts: _pairs(code['facts']),
    );

    if (kind != 'food') {
      final item = json['item'] is Map ? Map<String, dynamic>.from(json['item']) : null;
      final content = json['content'] is Map ? Map<String, dynamic>.from(json['content']) : null;
      return Product(
        kind: kind,
        barcode: codeText,
        name: _str(item?['title']) ?? _str(content?['title']) ?? _str(json['title']) ?? 'Scanned code',
        brand: _str(item?['subtitle']),
        imageUrl: _str(item?['image_url']),
        facts: _pairs(item?['facts'] ?? content?['facts']),
        sections: _pairs(item?['sections']),
        link: _https(content?['link']),
        database: _str(item?['database']),
        sourceUrl: _https(item?['url']),
        warning: common.warning,
        notes: common.notes,
        codeFacts: common.codeFacts,
      );
    }

    final dashboard = json['dashboard'] is Map ? Map<String, dynamic>.from(json['dashboard']) : <String, dynamic>{};
    final off = json['open_food_facts'] is Map ? Map<String, dynamic>.from(json['open_food_facts']) : <String, dynamic>{};
    final ai = json['ai_analysis'] is Map ? Map<String, dynamic>.from(json['ai_analysis']) : <String, dynamic>{};
    final warnings = (dashboard['Health Warnings'] is List ? dashboard['Health Warnings'] as List : [])
        .whereType<Map>()
        .map((w) => Map<String, dynamic>.from(w))
        .toList();

    return Product(
      kind: 'food',
      barcode: _str(off['barcode']) ?? codeText,
      name: _str(dashboard['Product Name']) ?? 'Name not available',
      brand: _str(dashboard['Brand']),
      vegStatus: _str(dashboard['Veg Status']),
      safetyColor: _str(dashboard['Safety Color']),
      safetyScore: (dashboard['Safety Score'] as num?)?.toInt(),
      ingredients: _strings(dashboard['Ingredients']),
      healthWarnings: warnings,
      imageUrl: _str(off['image_url']),
      nutriscore: _str(off['nutriscore']),
      novaGroup: (off['nova_group'] as num?)?.toInt(),
      ecoscore: _str(off['ecoscore']),
      nutriscoreCategory: _str(off['nutriscore_category']),
      expertSummary: _str(ai['expert_summary']),
      allergens: _strings(off['allergens'] ?? ai['allergens']),
      warning: common.warning,
      notes: common.notes,
      codeFacts: common.codeFacts,
    );
  }

  Map<String, dynamic> toJson() => {
        'kind': kind,
        'barcode': barcode,
        'name': name,
        'brand': brand,
        'vegStatus': vegStatus,
        'safetyColor': safetyColor,
        'safetyScore': safetyScore,
        'ingredients': ingredients,
        'healthWarnings': healthWarnings,
        'imageUrl': imageUrl,
        'nutriscore': nutriscore,
        'novaGroup': novaGroup,
        'ecoscore': ecoscore,
        'nutriscoreCategory': nutriscoreCategory,
        'expertSummary': expertSummary,
        'allergens': allergens,
        'warning': warning,
        'notes': notes,
        'codeFacts': codeFacts,
        'facts': facts,
        'sections': sections,
        'link': link,
        'database': database,
        'sourceUrl': sourceUrl,
      };

  factory Product.fromLocalJson(Map<String, dynamic> json) => Product(
        kind: _str(json['kind']) ?? 'food',
        barcode: _str(json['barcode']) ?? '',
        name: _str(json['name']) ?? 'Scanned code',
        brand: _str(json['brand']),
        vegStatus: _str(json['vegStatus']),
        safetyColor: _str(json['safetyColor']),
        safetyScore: (json['safetyScore'] as num?)?.toInt(),
        ingredients: _strings(json['ingredients']),
        healthWarnings: (json['healthWarnings'] is List ? json['healthWarnings'] as List : [])
            .whereType<Map>()
            .map((x) => Map<String, dynamic>.from(x))
            .toList(),
        imageUrl: _str(json['imageUrl']),
        nutriscore: _str(json['nutriscore']),
        novaGroup: (json['novaGroup'] as num?)?.toInt(),
        ecoscore: _str(json['ecoscore']),
        nutriscoreCategory: _str(json['nutriscoreCategory']),
        expertSummary: _str(json['expertSummary']),
        allergens: _strings(json['allergens']),
        warning: _str(json['warning']),
        notes: _strings(json['notes']),
        codeFacts: _pairs(json['codeFacts']),
        facts: _pairs(json['facts']),
        sections: _pairs(json['sections']),
        link: _https(json['link']),
        database: _str(json['database']),
        sourceUrl: _https(json['sourceUrl']),
      );
}
