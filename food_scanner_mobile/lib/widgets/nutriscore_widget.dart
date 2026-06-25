import 'package:flutter/material.dart';

class NutriScoreWidget extends StatelessWidget {
  final String? scoreLetter;

  const NutriScoreWidget({Key? key, this.scoreLetter}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final cleanLetter = scoreLetter?.trim().toUpperCase() ?? 'N/A';
    
    if (cleanLetter == 'N/A') {
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: Colors.grey.shade800,
          borderRadius: BorderRadius.circular(8),
        ),
        child: const Text(
          'Nutri-Score: N/A',
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
        ),
      );
    }

    final grades = ['A', 'B', 'C', 'D', 'E'];
    final colors = [
      const Color(0xFF038141), // A: Dark Green
      const Color(0xFF85BB2F), // B: Light Green
      const Color(0xFFFEC902), // C: Yellow
      const Color(0xFFEE8100), // D: Orange
      const Color(0xFFE63E11), // E: Red
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Nutri-Score',
          style: TextStyle(
            color: Colors.white70,
            fontSize: 14,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 8),
        Row(
          mainAxisSize: MainAxisSize.min,
          children: List.generate(grades.length, (index) {
            final grade = grades[index];
            final color = colors[index];
            final isActive = grade == cleanLetter;

            return Container(
              margin: const EdgeInsets.only(right: 4),
              width: isActive ? 45 : 32,
              height: isActive ? 45 : 32,
              decoration: BoxDecoration(
                color: color.withOpacity(isActive ? 1.0 : 0.25),
                borderRadius: BorderRadius.circular(isActive ? 8 : 6),
                border: Border.all(
                  color: isActive ? Colors.white : Colors.transparent,
                  width: isActive ? 2.0 : 0.0,
                ),
                boxShadow: isActive
                    ? [
                        BoxShadow(
                          color: color.withOpacity(0.5),
                          blurRadius: 10,
                          spreadRadius: 2,
                        )
                      ]
                    : null,
              ),
              child: Center(
                child: Text(
                  grade,
                  style: TextStyle(
                    color: isActive ? Colors.white : Colors.white.withOpacity(0.4),
                    fontSize: isActive ? 22 : 15,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            );
          }),
        ),
      ],
    );
  }
}
