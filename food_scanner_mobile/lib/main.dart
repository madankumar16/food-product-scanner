import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'screens/history_screen.dart';
import 'screens/photo_screen.dart';
import 'screens/result_tab.dart';
import 'screens/scanner_screen.dart';
import 'screens/search_screen.dart';
import 'screens/settings_screen.dart';
import 'services/app_actions.dart';
import 'services/product_provider.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => ProductProvider()),
        ChangeNotifierProvider(create: (_) => AppNav()),
      ],
      child: const FoodScannerApp(),
    ),
  );
}

class FoodScannerApp extends StatelessWidget {
  const FoodScannerApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Scan Before Use',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(seedColor: AppColors.green, primary: AppColors.green, surface: AppColors.bg),
        scaffoldBackgroundColor: AppColors.bg,
        appBarTheme: const AppBarTheme(backgroundColor: AppColors.bg, foregroundColor: AppColors.ink, elevation: 0),
      ),
      home: const MainNavigationShell(),
    );
  }
}

enum _MenuItem { pdf, history, nutriScore }

class MainNavigationShell extends StatelessWidget {
  const MainNavigationShell({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final nav = context.watch<AppNav>();
    final provider = context.watch<ProductProvider>();
    final latest = provider.history.isNotEmpty ? provider.history.first : null;

    return Scaffold(
      appBar: AppBar(
        toolbarHeight: 92,
        titleSpacing: 20,
        title: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Scan Before Use', style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: AppColors.ink)),
            Text('Point at a barcode or label', style: TextStyle(fontSize: 16, color: AppColors.text2)),
          ],
        ),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 16),
            child: PopupMenuButton<_MenuItem>(
              tooltip: 'More options',
              offset: const Offset(0, 60),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
              color: Colors.white,
              style: IconButton.styleFrom(
                backgroundColor: Colors.white,
                side: const BorderSide(color: AppColors.line),
                fixedSize: const Size(52, 52),
              ),
              icon: const Icon(Icons.more_vert, color: AppColors.ink),
              onSelected: (item) {
                switch (item) {
                  case _MenuItem.pdf:
                    shareReport(context, latest);
                  case _MenuItem.history:
                    Navigator.push(context, MaterialPageRoute(builder: (_) => const HistoryScreen()));
                  case _MenuItem.nutriScore:
                    openSitePage(context, '/nutri-score');
                }
              },
              itemBuilder: (_) => [
                PopupMenuItem(
                  value: _MenuItem.pdf,
                  enabled: latest != null,
                  child: const ListTile(leading: Icon(Icons.download, color: AppColors.green), title: Text('Download PDF report')),
                ),
                const PopupMenuItem(
                  value: _MenuItem.history,
                  child: ListTile(leading: Icon(Icons.history, color: AppColors.green), title: Text('History')),
                ),
                const PopupMenuItem(
                  value: _MenuItem.nutriScore,
                  child: ListTile(leading: Icon(Icons.eco_outlined, color: AppColors.green), title: Text('Nutri-Score calculator')),
                ),
              ],
            ),
          ),
        ],
      ),
      body: IndexedStack(
        index: nav.index,
        children: [
          // The camera only runs while Home is showing.
          ScannerScreen(active: nav.index == AppNav.home),
          const SearchScreen(),
          const ResultTab(),
          const PhotoScreen(),
          const SettingsScreen(),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: nav.index,
        onDestinationSelected: nav.go,
        backgroundColor: Colors.white,
        indicatorColor: AppColors.greenSoft,
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home), label: 'Home'),
          NavigationDestination(icon: Icon(Icons.tag), label: 'Number'),
          NavigationDestination(icon: Icon(Icons.view_week_outlined), selectedIcon: Icon(Icons.view_week), label: 'Barcode'),
          NavigationDestination(icon: Icon(Icons.photo_camera_outlined), selectedIcon: Icon(Icons.photo_camera), label: 'Photo'),
          NavigationDestination(icon: Icon(Icons.settings_outlined), selectedIcon: Icon(Icons.settings), label: 'Settings'),
        ],
      ),
    );
  }
}
