import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/product.dart';
import '../services/product_provider.dart';
import 'product_detail_screen.dart';

class HistoryScreen extends StatelessWidget {
  const HistoryScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        backgroundColor: const Color(0xFFF2F4EE), // Dark slate
        appBar: AppBar(
          backgroundColor: const Color(0xFFFFFFFF),
          elevation: 0,
          title: const Text(
            'Scans & Favorites',
            style: TextStyle(
              fontWeight: FontWeight.bold,
              color: Color(0xFF17221C),
            ),
          ),
          bottom: const TabBar(
            labelColor: Color(0xFF1F6B45), // Light blue neon
            unselectedLabelColor: Color(0xFF4A5A50),
            indicatorColor: Color(0xFF1F6B45),
            tabs: [
              Tab(icon: Icon(Icons.history), text: 'History'),
              Tab(icon: Icon(Icons.favorite), text: 'Favorites'),
            ],
          ),
        ),
        body: const TabBarView(
          children: [
            HistoryTab(),
            FavoritesTab(),
          ],
        ),
      ),
    );
  }
}

class HistoryTab extends StatelessWidget {
  const HistoryTab({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final provider = Provider.of<ProductProvider>(context);

    if (provider.isLoading) {
      return const Center(child: CircularProgressIndicator(color: Color(0xFF1F6B45)));
    }

    if (provider.history.isEmpty) {
      return const EmptyStatePlaceholder(
        icon: Icons.qr_code_scanner,
        message: 'No scans yet.\nScan any barcode or QR code.',
      );
    }

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(12.0),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '${provider.history.length} scans',
                style: const TextStyle(color: Color(0xFF4A5A50), fontSize: 13),
              ),
              TextButton.icon(
                onPressed: () => _confirmClear(context, provider, true),
                icon: const Icon(Icons.delete_sweep, color: Colors.red.shade700, size: 18),
                label: const Text('Clear All', style: TextStyle(color: Colors.red.shade700)),
              ),
            ],
          ),
        ),
        Expanded(
          child: ListView.builder(
            itemCount: provider.history.length,
            padding: const EdgeInsets.only(bottom: 24),
            itemBuilder: (context, index) {
              final product = provider.history[index];
              return Dismissible(
                key: Key('hist_${product.barcode}_$index'),
                direction: DismissDirection.endToStart,
                background: Container(
                  alignment: Alignment.centerRight,
                  padding: const EdgeInsets.only(right: 20),
                  color: Colors.red.shade700,
                  child: const Icon(Icons.delete, color: Colors.white),
                ),
                onDismissed: (direction) {
                  provider.removeFromHistory(product.barcode);
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('${product.name} removed from history')),
                  );
                },
                child: ProductListTile(product: product),
              );
            },
          ),
        ),
      ],
    );
  }
}

class FavoritesTab extends StatelessWidget {
  const FavoritesTab({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final provider = Provider.of<ProductProvider>(context);

    if (provider.isLoading) {
      return const Center(child: CircularProgressIndicator(color: Color(0xFF1F6B45)));
    }

    if (provider.favorites.isEmpty) {
      return const EmptyStatePlaceholder(
        icon: Icons.favorite_border,
        message: 'Nothing saved yet.\nTap the heart on any result.',
      );
    }

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(12.0),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '${provider.favorites.length} saved',
                style: const TextStyle(color: Color(0xFF4A5A50), fontSize: 13),
              ),
              TextButton.icon(
                onPressed: () => _confirmClear(context, provider, false),
                icon: const Icon(Icons.favorite_border, color: Colors.red.shade700, size: 18),
                label: const Text('Remove All', style: TextStyle(color: Colors.red.shade700)),
              ),
            ],
          ),
        ),
        Expanded(
          child: ListView.builder(
            itemCount: provider.favorites.length,
            padding: const EdgeInsets.only(bottom: 24),
            itemBuilder: (context, index) {
              final product = provider.favorites[index];
              return Dismissible(
                key: Key('fav_${product.barcode}_$index'),
                direction: DismissDirection.endToStart,
                background: Container(
                  alignment: Alignment.centerRight,
                  padding: const EdgeInsets.only(right: 20),
                  color: Colors.red.shade700,
                  child: const Icon(Icons.heart_broken, color: Colors.white),
                ),
                onDismissed: (direction) {
                  provider.toggleFavorite(product);
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('${product.name} removed from favorites')),
                  );
                },
                child: ProductListTile(product: product),
              );
            },
          ),
        ),
      ],
    );
  }
}

class ProductListTile extends StatelessWidget {
  final Product product;

  const ProductListTile({Key? key, required this.product}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    Color safetyColor;
    switch ((product.safetyColor ?? '').toUpperCase()) {
      case 'GREEN':
        safetyColor = Colors.green.shade800;
        break;
      case 'YELLOW':
        safetyColor = Colors.amber.shade900;
        break;
      case 'RED':
        safetyColor = Colors.red.shade700;
        break;
      default:
        safetyColor = Colors.grey;
    }

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      color: const Color(0xFFFFFFFF),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: ListTile(
        contentPadding: const EdgeInsets.all(12),
        leading: ClipRRect(
          borderRadius: BorderRadius.circular(8),
          child: product.imageUrl != null && product.imageUrl!.isNotEmpty
              ? Image.network(
                  product.imageUrl!,
                  width: 50,
                  height: 50,
                  fit: BoxFit.cover,
                  errorBuilder: (context, error, stackTrace) =>
                      Icon(_iconFor(product), color: Color(0xFF4A5A50), size: 30),
                )
              : Icon(_iconFor(product), color: Color(0xFF4A5A50), size: 30),
        ),
        title: Text(
          product.name,
          style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF17221C)),
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 4),
            Text(product.brand ?? product.kindLabel, style: const TextStyle(color: Color(0xFF4A5A50), fontSize: 13)),
            const SizedBox(height: 6),
            if (product.isFood) Row(
              children: [
                Container(
                  width: 10,
                  height: 10,
                  decoration: BoxDecoration(color: safetyColor, shape: BoxShape.circle),
                ),
                const SizedBox(width: 6),
                Text(
                  product.safetyScore != null ? 'Score: ${product.safetyScore}/100' : 'No score',
                  style: TextStyle(color: safetyColor, fontSize: 12, fontWeight: FontWeight.bold),
                ),
                if (product.nutriscore != null) ...[
                  const SizedBox(width: 12),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: Color(0xFFE8F2EC),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      'Nutri-Score: ${product.nutriscore}',
                      style: const TextStyle(color: Color(0xFF3D4A42), fontSize: 11, fontWeight: FontWeight.bold),
                    ),
                  ),
                ]
              ],
            )
          ],
        ),
        trailing: const Icon(Icons.chevron_right, color: Color(0xFF8A968E)),
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => ProductDetailScreen(product: product),
            ),
          );
        },
      ),
    );
  }
}

class EmptyStatePlaceholder extends StatelessWidget {
  final IconData icon;
  final String message;

  const EmptyStatePlaceholder({
    Key? key,
    required this.icon,
    required this.message,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, size: 64, color: Color(0xFFB5BFB8)),
          const SizedBox(height: 16),
          Text(
            message,
            textAlign: TextAlign.center,
            style: const TextStyle(color: Color(0xFF8A968E), fontSize: 15, height: 1.4),
          ),
        ],
      ),
    );
  }
}

IconData _iconFor(Product p) {
  switch (p.kind) {
    case 'food':
      return Icons.fastfood;
    case 'product':
      return Icons.inventory_2_outlined;
    case 'book':
      return Icons.menu_book_outlined;
    default:
      return Icons.qr_code_2;
  }
}

void _confirmClear(BuildContext context, ProductProvider provider, bool isHistory) {
  showDialog(
    context: context,
    builder: (context) => AlertDialog(
      backgroundColor: const Color(0xFFFFFFFF),
      title: Text(
        isHistory ? 'Clear Scan History?' : 'Clear Favorites?',
        style: const TextStyle(color: Color(0xFF17221C), fontWeight: FontWeight.bold),
      ),
      content: Text(
        isHistory
            ? 'Delete all scans from this phone?'
            : 'Remove everything you saved?',
        style: const TextStyle(color: Color(0xFF3D4A42)),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Cancel', style: TextStyle(color: Color(0xFF4A5A50))),
        ),
        TextButton(
          onPressed: () {
            if (isHistory) {
              provider.clearHistory();
            } else {
              provider.clearFavorites();
            }
            Navigator.pop(context);
          },
          child: const Text('Clear All', style: TextStyle(color: Colors.red.shade700)),
        ),
      ],
    ),
  );
}
