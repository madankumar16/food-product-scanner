import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/product.dart';

class ProductProvider with ChangeNotifier {
  List<Product> _history = [];
  List<Product> _favorites = [];
  List<String> _selectedAllergens = [];
  String _dietaryPreference = 'none'; // 'none', 'vegan', 'vegetarian'
  bool _isLoading = true;

  List<Product> get history => _history;
  List<Product> get favorites => _favorites;
  List<String> get selectedAllergens => _selectedAllergens;
  String get dietaryPreference => _dietaryPreference;
  bool get isLoading => _isLoading;

  ProductProvider() {
    loadData();
  }

  Future<void> loadData() async {
    _isLoading = true;
    notifyListeners();

    try {
      final prefs = await SharedPreferences.getInstance();
      
      // Load history
      final historyStr = prefs.getString('scan_history');
      if (historyStr != null) {
        final List<dynamic> decoded = jsonDecode(historyStr);
        _history = decoded.map((x) => Product.fromLocalJson(x)).toList();
      }

      // Load favorites
      final favoritesStr = prefs.getString('favorites');
      if (favoritesStr != null) {
        final List<dynamic> decoded = jsonDecode(favoritesStr);
        _favorites = decoded.map((x) => Product.fromLocalJson(x)).toList();
      }

      // Load allergens and diet settings
      _selectedAllergens = prefs.getStringList('selected_allergens') ?? [];
      _dietaryPreference = prefs.getString('dietary_preference') ?? 'none';
    } catch (e) {
      debugPrint("Error loading local storage data: $e");
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> toggleAllergen(String allergen) async {
    if (_selectedAllergens.contains(allergen)) {
      _selectedAllergens.remove(allergen);
    } else {
      _selectedAllergens.add(allergen);
    }
    notifyListeners();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList('selected_allergens', _selectedAllergens);
  }

  Future<void> setDietaryPreference(String preference) async {
    _dietaryPreference = preference;
    notifyListeners();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('dietary_preference', _dietaryPreference);
  }

  List<String> checkProductWarnings(Product product) {
    final List<String> warnings = [];
    if (!product.isFood) return warnings; // diet and allergen checks only apply to food
    final vegStatus = product.vegStatus ?? 'Not confirmed';

    // Check Dietary Suitability
    final vegLower = vegStatus.toLowerCase();
    if (_dietaryPreference == 'vegan') {
      if (vegLower != 'vegan') {
        warnings.add('Diet Alert: Product is not certified Vegan (Status: $vegStatus)');
      }
    } else if (_dietaryPreference == 'vegetarian') {
      if (vegLower != 'vegan' && vegLower != 'vegetarian') {
        warnings.add('Diet Alert: Product is not certified Vegetarian (Status: $vegStatus)');
      }
    }

    // Check Allergens
    for (final allergen in _selectedAllergens) {
      final allergyLower = allergen.toLowerCase();
      
      // Match against parsed allergens or warnings
      final hasAllergen = product.allergens.any((x) => x.toLowerCase().contains(allergyLower)) ||
                          product.healthWarnings.any((x) => x['ingredient'].toString().toLowerCase().contains(allergyLower));
      
      if (hasAllergen) {
        warnings.add('Allergen Warning: Contains $allergen or related components!');
        continue;
      }
      
      // Fallback: check ingredients list text
      final hasInIngredients = product.ingredients.any((x) => x.toLowerCase().contains(allergyLower));
      if (hasInIngredients) {
        warnings.add('Allergen Warning: $allergen detected in ingredients list!');
      }
    }

    return warnings;
  }

  Future<void> addToHistory(Product product) async {
    // Remove if already exists (to move it to top)
    _history.removeWhere((x) => x.barcode == product.barcode);
    _history.insert(0, product);
    
    // Limit history size to 50 items
    if (_history.length > 50) {
      _history = _history.sublist(0, 50);
    }
    
    notifyListeners();
    await _saveHistory();
  }

  Future<void> removeFromHistory(String barcode) async {
    _history.removeWhere((x) => x.barcode == barcode);
    notifyListeners();
    await _saveHistory();
  }

  Future<void> toggleFavorite(Product product) async {
    final index = _favorites.indexWhere((x) => x.barcode == product.barcode);
    if (index >= 0) {
      _favorites.removeAt(index);
    } else {
      _favorites.insert(0, product);
    }
    notifyListeners();
    await _saveFavorites();
  }

  bool isFavorite(String barcode) {
    return _favorites.any((x) => x.barcode == barcode);
  }

  Future<void> clearHistory() async {
    _history.clear();
    notifyListeners();
    await _saveHistory();
  }

  Future<void> clearFavorites() async {
    _favorites.clear();
    notifyListeners();
    await _saveFavorites();
  }

  Future<void> _saveHistory() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final data = _history.map((x) => x.toJson()).toList();
      await prefs.setString('scan_history', jsonEncode(data));
    } catch (e) {
      debugPrint("Error saving scan history: $e");
    }
  }

  Future<void> _saveFavorites() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final data = _favorites.map((x) => x.toJson()).toList();
      await prefs.setString('favorites', jsonEncode(data));
    } catch (e) {
      debugPrint("Error saving favorites: $e");
    }
  }
}
