import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class TopicChip extends StatelessWidget {
  const TopicChip({super.key, required this.label, required this.onTap});

  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        margin: const EdgeInsets.only(right: 8, bottom: 4),
        decoration: BoxDecoration(
          color: const Color(0xFF2D1F6E),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: kAccentPurple.withValues(alpha: 0.5),
            width: 1,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.auto_awesome_rounded, size: 13, color: kAccentPurple),
            const SizedBox(width: 6),
            Text(
              label,
              style: const TextStyle(
                color: kAccentPurple,
                fontSize: 13,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
