class Product {
  final String barcode;
  final String name;
  final String brand;
  final String vegStatus;
  final String safetyColor;
  final int safetyScore;
  final List<String> ingredients;
  final List<Map<String, dynamic>> healthWarnings;
  final String? imageUrl;
  final String? nutriscore;
  final int? novaGroup;
  final String? ecoscore;
  final String? nutriscoreCategory;
  final String? expertSummary;
  final List<String> allergens;

  Product({
    required this.barcode,
    required this.name,
    required this.brand,
    required this.vegStatus,
    required this.safetyColor,
    required this.safetyScore,
    required this.ingredients,
    required this.healthWarnings,
    this.imageUrl,
    this.nutriscore,
    this.novaGroup,
    this.ecoscore,
    this.nutriscoreCategory,
    this.expertSummary,
    required this.allergens,
  });

  factory Product.fromJson(Map<String, dynamic> json, String barcodeVal) {
    final dashboard = json['dashboard'] ?? {};
    final off = json['open_food_facts'] ?? {};
    final ai = json['ai_analysis'] ?? {};

    // Parse ingredients safely
    final rawIngredients = dashboard['Ingredients'] ?? [];
    final List<String> parsedIngredients = rawIngredients is List
        ? List<String>.from(rawIngredients.map((x) => x.toString()))
        : [];

    // Parse health warnings safely
    final rawWarnings = dashboard['Health Warnings'] ?? [];
    final List<Map<String, dynamic>> parsedWarnings = [];
    if (rawWarnings is List) {
      for (var warning in rawWarnings) {
        if (warning is Map<String, dynamic>) {
          parsedWarnings.add(warning);
        }
      }
    }

    // Parse allergens
    final rawAllergens = off['allergens'] ?? ai['allergens'] ?? [];
    final List<String> parsedAllergens = rawAllergens is List
        ? List<String>.from(rawAllergens.map((x) => x.toString()))
        : [];

    return Product(
      barcode: barcodeVal.isNotEmpty ? barcodeVal : (off['barcode']?.toString() ?? ''),
      name: dashboard['Product Name']?.toString() ?? 'Unknown Product',
      brand: dashboard['Brand']?.toString() ?? 'Unknown Brand',
      vegStatus: dashboard['Veg Status']?.toString() ?? 'Unknown',
      safetyColor: dashboard['Safety Color']?.toString() ?? 'YELLOW',
      safetyScore: (dashboard['Safety Score'] as num?)?.toInt() ?? 0,
      ingredients: parsedIngredients,
      healthWarnings: parsedWarnings,
      imageUrl: off['image_url']?.toString(),
      nutriscore: off['nutriscore']?.toString() ?? json['nutriscore']?.toString(),
      novaGroup: (off['nova_group'] as num?)?.toInt(),
      ecoscore: off['ecoscore']?.toString(),
      nutriscoreCategory: off['nutriscore_category']?.toString(),
      expertSummary: ai['expert_summary']?.toString(),
      allergens: parsedAllergens,
    );
  }

  Map<String, dynamic> toJson() {
    return {
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
    };
  }

  factory Product.fromLocalJson(Map<String, dynamic> json) {
    return Product(
      barcode: json['barcode']?.toString() ?? '',
      name: json['name']?.toString() ?? 'Unknown Product',
      brand: json['brand']?.toString() ?? 'Unknown Brand',
      vegStatus: json['vegStatus']?.toString() ?? 'Unknown',
      safetyColor: json['safetyColor']?.toString() ?? 'YELLOW',
      safetyScore: (json['safetyScore'] as num?)?.toInt() ?? 0,
      ingredients: List<String>.from(json['ingredients'] ?? []),
      healthWarnings: (json['healthWarnings'] as List?)?.map((x) => Map<String, dynamic>.from(x)).toList() ?? [],
      imageUrl: json['imageUrl']?.toString(),
      nutriscore: json['nutriscore']?.toString(),
      novaGroup: (json['novaGroup'] as num?)?.toInt(),
      ecoscore: json['ecoscore']?.toString(),
      nutriscoreCategory: json['nutriscoreCategory']?.toString(),
      expertSummary: json['expertSummary']?.toString(),
      allergens: List<String>.from(json['allergens'] ?? []),
    );
  }
}
