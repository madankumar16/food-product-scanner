import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/product.dart';
import '../services/product_provider.dart';
import '../widgets/nutriscore_widget.dart';
import 'code_result_screen.dart';

class ProductDetailScreen extends StatelessWidget {
  final Product product;

  const ProductDetailScreen({Key? key, required this.product}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    if (!product.isFood) return CodeResultScreen(product: product);
    final provider = Provider.of<ProductProvider>(context);
    final vegStatus = product.vegStatus ?? 'Not confirmed';
    final isNonVeg = vegStatus.toLowerCase().contains('non');
    final isVeg = !isNonVeg && (vegStatus == 'Vegetarian' || vegStatus == 'Vegan');
    final isFav = provider.isFavorite(product.barcode);
    final alerts = provider.checkProductWarnings(product);

    Color safetyColor;
    switch ((product.safetyColor ?? '').toUpperCase()) {
      case 'GREEN':
        safetyColor = Colors.greenAccent.shade400;
        break;
      case 'YELLOW':
        safetyColor = Colors.yellowAccent.shade400;
        break;
      case 'RED':
        safetyColor = Colors.redAccent;
        break;
      default:
        safetyColor = Colors.grey;
    }

    return Scaffold(
      backgroundColor: const Color(0xFF0F172A), // Dark slate
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
        actions: [
          IconButton(
            icon: Icon(
              isFav ? Icons.favorite : Icons.favorite_border,
              color: isFav ? Colors.redAccent : Colors.white,
              size: 28,
            ),
            onPressed: () {
              provider.toggleFavorite(product);
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text(
                    isFav
                        ? '${product.name} removed from favorites'
                        : '${product.name} added to favorites',
                  ),
                  duration: const Duration(seconds: 1),
                ),
              );
            },
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Product Header Image & Basic Info
            Center(
              child: Container(
                margin: const EdgeInsets.symmetric(vertical: 16),
                height: 180,
                width: 180,
                decoration: BoxDecoration(
                  color: const Color(0xFF1E293B),
                  borderRadius: BorderRadius.circular(16),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.3),
                      blurRadius: 15,
                      offset: const Offset(0, 8),
                    )
                  ],
                ),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(16),
                  child: product.imageUrl != null && product.imageUrl!.isNotEmpty
                      ? Image.network(
                          product.imageUrl!,
                          fit: BoxFit.contain,
                          errorBuilder: (context, error, stackTrace) =>
                              const Icon(Icons.fastfood, size: 80, color: Colors.white30),
                        )
                      : const Icon(Icons.fastfood, size: 80, color: Colors.white30),
                ),
              ),
            ),
            
            // Name & Brand
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    product.name,
                    style: const TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    product.brand ?? 'Brand not available',
                    style: const TextStyle(
                      fontSize: 16,
                      color: Color(0xFF38BDF8), // Neon blue
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    'Barcode: ${product.barcode}',
                    style: const TextStyle(fontSize: 13, color: Colors.white38),
                  ),
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
                  child: Text(product.warning!,
                      style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, height: 1.4)),
                ),
              ),

            // Real-Time Dietary Profile Warnings / Alerts Block
            if (alerts.isNotEmpty) ...[
              const SizedBox(height: 16),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.redAccent.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.redAccent.withOpacity(0.5), width: 1.5),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          const Icon(Icons.warning_amber_rounded, color: Colors.redAccent, size: 24),
                          const SizedBox(width: 8),
                          const Text(
                            'Dietary Warning!',
                            style: TextStyle(
                              color: Colors.redAccent,
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 10),
                      ...alerts.map((alert) => Padding(
                            padding: const EdgeInsets.only(bottom: 6.0),
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text('• ', style: TextStyle(color: Colors.redAccent, fontSize: 16)),
                                Expanded(
                                  child: Text(
                                    alert,
                                    style: const TextStyle(color: Colors.white, fontSize: 13, height: 1.3),
                                  ),
                                ),
                              ],
                            ),
                          )),
                    ],
                  ),
                ),
              ),
            ],

            const SizedBox(height: 20),

            // Scores Section (Safety Rating & NutriScore)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Safety Card
                  Expanded(
                    child: Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: const Color(0xFF1E293B),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Ingredient score',
                            style: TextStyle(color: Colors.white70, fontSize: 13),
                          ),
                          const SizedBox(height: 8),
                          Row(
                            children: [
                              Container(
                                width: 12,
                                height: 12,
                                decoration: BoxDecoration(
                                  color: safetyColor,
                                  shape: BoxShape.circle,
                                ),
                              ),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  product.safetyColor ?? 'Not available',
                                  style: TextStyle(
                                    color: safetyColor,
                                    fontSize: 16,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 4),
                          Text(
                            product.safetyScore != null ? 'Score: ${product.safetyScore}/100' : 'No ingredients to score',
                            style: const TextStyle(color: Colors.white54, fontSize: 12),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(width: 16),
                  // Nutri-Score Card
                  Expanded(
                    child: Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: const Color(0xFF1E293B),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: NutriScoreWidget(scoreLetter: product.nutriscore),
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 20),

            // Veg Status
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                decoration: BoxDecoration(
                  color: const Color(0xFF1E293B),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  children: [
                    Icon(
                      isNonVeg ? Icons.restaurant : (isVeg ? Icons.eco : Icons.help_outline),
                      color: isNonVeg ? Colors.orangeAccent : (isVeg ? Colors.greenAccent : Colors.white54),
                    ),
                    const SizedBox(width: 12),
                    const Text(
                      'Dietary Suitability: ',
                      style: TextStyle(color: Colors.white70, fontSize: 14),
                    ),
                    Text(
                      vegStatus,
                      style: TextStyle(
                        color: isNonVeg ? Colors.orangeAccent : (isVeg ? Colors.greenAccent : Colors.white54),
                        fontSize: 14,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 24),

            // Health Warnings / Allergens
            if (product.allergens.isNotEmpty || product.healthWarnings.isNotEmpty) ...[
              const Padding(
                padding: EdgeInsets.symmetric(horizontal: 20),
                child: Text(
                  '⚠️ Health Alerts',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
                ),
              ),
              const SizedBox(height: 10),
              if (product.allergens.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 4),
                  child: Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: product.allergens.map((allergen) {
                      return Chip(
                        label: Text(allergen),
                        backgroundColor: Colors.redAccent.withOpacity(0.25),
                        labelStyle: const TextStyle(color: Colors.redAccent, fontWeight: FontWeight.bold, fontSize: 12),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      );
                    }).toList(),
                  ),
                ),
              ...product.healthWarnings.map((warning) {
                final ing = warning['ingredient']?.toString() ?? '';
                final conditions = (warning['conditions'] as List?)?.join(', ') ?? 'Contains allergen';
                return Card(
                  margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 6),
                  color: const Color(0xFF2D1E24), // Mild reddish-dark card
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  child: ListTile(
                    leading: const Icon(Icons.warning_amber_rounded, color: Colors.redAccent),
                    title: Text(ing, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                    subtitle: Text(conditions, style: const TextStyle(color: Colors.white70)),
                  ),
                );
              }),
              const SizedBox(height: 24),
            ],

            // Ingredients
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 20),
              child: Text(
                '📝 Ingredients',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
              ),
            ),
            const SizedBox(height: 10),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: const Color(0xFF1E293B),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  product.ingredients.isEmpty
                      ? 'No ingredients list available. Check the pack.'
                      : product.ingredients.join(', '),
                  style: const TextStyle(color: Colors.white70, fontSize: 14, height: 1.5),
                ),
              ),
            ),

            const SizedBox(height: 24),

            if (product.codeFacts.isNotEmpty) ...[
              const Padding(
                padding: EdgeInsets.symmetric(horizontal: 20),
                child: Text('Barcode details',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white)),
              ),
              const SizedBox(height: 10),
              ...product.codeFacts.map((f) => Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 2),
                    child: Text('${f[0]}: ${f[1]}', style: const TextStyle(color: Colors.white70, fontSize: 14)),
                  )),
              const SizedBox(height: 24),
            ],

            // AI Expert Summary
            if (product.expertSummary != null && product.expertSummary!.isNotEmpty) ...[
              const Padding(
                padding: EdgeInsets.symmetric(horizontal: 20),
                child: Text(
                  '🤖 AI Expert Summary',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
                ),
              ),
              const SizedBox(height: 10),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: const Color(0xFF1E293B),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: const Color(0xFF0284C7).withOpacity(0.3)), // subtle neon border
                  ),
                  child: Text(
                    product.expertSummary!,
                    style: const TextStyle(color: Colors.white70, fontSize: 14, height: 1.5),
                  ),
                ),
              ),
              const SizedBox(height: 32),
            ],
          ],
        ),
      ),
    );
  }
}
