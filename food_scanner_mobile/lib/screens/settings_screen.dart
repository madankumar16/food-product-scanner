import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../services/app_actions.dart';
import '../services/product_provider.dart';
import 'history_screen.dart';
import 'profile_screen.dart';

/// Settings tab: alerts, tools, your data, and the legal pages.
class SettingsScreen extends StatelessWidget {
  const SettingsScreen({Key? key}) : super(key: key);

  Widget _section(String title, List<Widget> tiles) => Container(
        margin: const EdgeInsets.only(bottom: 16),
        decoration: BoxDecoration(
          color: AppColors.card,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: AppColors.line),
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 4),
            child: Text(title, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w600, color: AppColors.ink)),
          ),
          ...tiles,
          const SizedBox(height: 8),
        ]),
      );

  Widget _tile(String label, VoidCallback onTap, {IconData icon = Icons.chevron_right}) => ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 20),
        title: Text(label, style: const TextStyle(fontWeight: FontWeight.w600, color: AppColors.ink)),
        trailing: Icon(icon, color: AppColors.text2),
        onTap: onTap,
      );

  @override
  Widget build(BuildContext context) {
    void push(Widget screen) => Navigator.push(context, MaterialPageRoute(builder: (_) => screen));
    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 4, 20, 24),
      children: [
        const Padding(
          padding: EdgeInsets.only(bottom: 16),
          child: Text('Settings', style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: AppColors.ink)),
        ),
        _section('Tools', [
          _tile('Diet and allergy alerts', () => push(const ProfileScreen())),
          _tile('History', () => push(const HistoryScreen())),
          _tile('Nutri-Score calculator', () => openSitePage(context, '/nutri-score'), icon: Icons.open_in_new),
        ]),
        _section('Your data', [
          const Padding(
            padding: EdgeInsets.fromLTRB(20, 4, 20, 8),
            child: Text('No account and no tracking. Your scans are saved only on this phone.',
                style: TextStyle(color: AppColors.text2, height: 1.4)),
          ),
          _tile('Delete my scans', () async {
            final ok = await showDialog<bool>(
              context: context,
              builder: (c) => AlertDialog(
                title: const Text('Delete all scans?'),
                content: const Text('This removes your history and saved items from this phone.'),
                actions: [
                  TextButton(onPressed: () => Navigator.pop(c, false), child: const Text('Cancel')),
                  TextButton(onPressed: () => Navigator.pop(c, true), child: const Text('Delete')),
                ],
              ),
            );
            if (ok == true && context.mounted) {
              final provider = context.read<ProductProvider>();
              await provider.clearHistory();
              await provider.clearFavorites();
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Your scans have been deleted.')));
              }
            }
          }, icon: Icons.delete_outline),
        ]),
        _section('Legal', [
          _tile('Privacy policy', () => openSitePage(context, '/privacy'), icon: Icons.open_in_new),
          _tile('Terms of use', () => openSitePage(context, '/terms'), icon: Icons.open_in_new),
          _tile('Cookies', () => openSitePage(context, '/cookies'), icon: Icons.open_in_new),
        ]),
        const Text(
          'Product data: Open Food Facts, Open Beauty Facts, Open Pet Food Facts, Open Products Facts (ODbL) and Open Library.',
          style: TextStyle(color: AppColors.text2, fontSize: 12),
        ),
      ],
    );
  }
}
