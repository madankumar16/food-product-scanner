import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/product_provider.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final provider = Provider.of<ProductProvider>(context);
    
    final commonAllergens = [
      'Gluten',
      'Dairy',
      'Peanuts',
      'Nuts',
      'Eggs',
      'Soy',
      'Fish',
      'Shellfish',
    ];

    return Scaffold(
      backgroundColor: const Color(0xFF0F172A),
      appBar: AppBar(
        backgroundColor: const Color(0xFF1E293B),
        elevation: 0,
        title: const Text(
          'Dietary Profile',
          style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Diet & Allergen Alerts',
              style: TextStyle(
                color: Colors.white,
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Customize your alerts. If a scanned product violates your profile, we will show a prominent alert card on the scan results.',
              style: TextStyle(color: Colors.white54, fontSize: 13, height: 1.4),
            ),
            const SizedBox(height: 24),
            
            // Section 1: Dietary Requirement
            const Text(
              'DIETARY REQUIREMENT',
              style: TextStyle(
                color: Color(0xFF38BDF8),
                fontSize: 12,
                fontWeight: FontWeight.bold,
                letterSpacing: 1.2,
              ),
            ),
            const SizedBox(height: 10),
            Container(
              decoration: BoxDecoration(
                color: const Color(0xFF1E293B),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Column(
                children: [
                  _buildDietRadio(context, provider, 'none', 'No Dietary Preference', 'Check ingredients manually'),
                  const Divider(color: Colors.white10, height: 1),
                  _buildDietRadio(context, provider, 'vegetarian', 'Vegetarian Diet', 'Flag products containing meat, poultry, or fish'),
                  const Divider(color: Colors.white10, height: 1),
                  _buildDietRadio(context, provider, 'vegan', 'Vegan Diet', 'Flag products containing meat, dairy, eggs, honey, etc.'),
                ],
              ),
            ),

            const SizedBox(height: 28),

            // Section 2: Allergen Alerts
            const Text(
              'ALLERGEN WARNINGS',
              style: TextStyle(
                color: Color(0xFF38BDF8),
                fontSize: 12,
                fontWeight: FontWeight.bold,
                letterSpacing: 1.2,
              ),
            ),
            const SizedBox(height: 10),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 12),
              decoration: BoxDecoration(
                color: const Color(0xFF1E293B),
                borderRadius: BorderRadius.circular(12),
              ),
              child: GridView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: commonAllergens.length,
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2,
                  childAspectRatio: 2.8,
                  crossAxisSpacing: 8,
                  mainAxisSpacing: 8,
                ),
                itemBuilder: (context, index) {
                  final allergen = commonAllergens[index];
                  final isEnabled = provider.selectedAllergens.contains(allergen);

                  return InkWell(
                    onTap: () => provider.toggleAllergen(allergen),
                    borderRadius: BorderRadius.circular(10),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12),
                      decoration: BoxDecoration(
                        color: isEnabled
                            ? Colors.redAccent.withOpacity(0.1)
                            : const Color(0xFF0F172A),
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(
                          color: isEnabled ? Colors.redAccent.withOpacity(0.5) : Colors.transparent,
                          width: 1,
                        ),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Expanded(
                            child: Text(
                              allergen,
                              style: TextStyle(
                                color: isEnabled ? Colors.redAccent : Colors.white70,
                                fontWeight: isEnabled ? FontWeight.bold : FontWeight.normal,
                                fontSize: 14,
                              ),
                            ),
                          ),
                          Icon(
                            isEnabled ? Icons.warning_amber_rounded : Icons.check_circle_outline,
                            color: isEnabled ? Colors.redAccent : Colors.white30,
                            size: 20,
                          ),
                        ],
                      ),
                    ),
                  );
                },
              ),
            ),
            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }

  Widget _buildDietRadio(
    BuildContext context,
    ProductProvider provider,
    String value,
    String title,
    String subtitle,
  ) {
    final isSelected = provider.dietaryPreference == value;
    return RadioListTile<String>(
      value: value,
      groupValue: provider.dietaryPreference,
      onChanged: (val) {
        if (val != null) {
          provider.setDietaryPreference(val);
        }
      },
      activeColor: const Color(0xFF38BDF8),
      title: Text(
        title,
        style: TextStyle(
          color: isSelected ? const Color(0xFF38BDF8) : Colors.white,
          fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
          fontSize: 15,
        ),
      ),
      subtitle: Text(
        subtitle,
        style: const TextStyle(color: Colors.white38, fontSize: 12),
      ),
    );
  }
}
