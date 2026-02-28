import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:google_fonts/google_fonts.dart';

import '../controllers/progress_controller.dart';
import '../models/topic.dart';
import '../theme/app_theme.dart';
import '../widgets/app_logo.dart';

class ProgressScreen extends GetView<ProgressController> {
  const ProgressScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            AppLogo(size: 28),
            SizedBox(width: 10),
            Text('Progress'),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed: controller.load,
            tooltip: 'Refresh',
          ),
        ],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Container(height: 1, color: kDivider),
        ),
      ),
      body: Obx(() {
        final error = controller.error.value;
        final loading = controller.isLoading.value;

        if (error != null) {
          return Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.error_outline, size: 40, color: kError),
                const SizedBox(height: 12),
                Text('Error: $error',
                    style: const TextStyle(color: kTextSecondary)),
                const SizedBox(height: 16),
                TextButton(
                  onPressed: controller.load,
                  child: const Text('Retry',
                      style: TextStyle(color: kAccentPurple)),
                ),
              ],
            ),
          );
        }

        if (loading) {
          return const Center(
            child: CircularProgressIndicator(color: kAccentPurple),
          );
        }

        final weak = controller.weakTopics;
        final strong = controller.strongTopics;
        final suggested = controller.suggestedNext.value;
        final suggestedLabel = controller.suggestedNextLabel.value;

        return RefreshIndicator(
          onRefresh: controller.load,
          color: kAccentPurple,
          backgroundColor: kCard,
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              if (suggested != null && suggested.isNotEmpty)
                _SuggestedNextCard(
                  topicId: suggested,
                  label: (suggestedLabel != null && suggestedLabel.isNotEmpty)
                      ? suggestedLabel
                      : suggested,
                  onTap: () => controller.openTopic(suggested),
                ),

              const SizedBox(height: 24),
              _SectionHeader(
                  label: 'Weak Areas',
                  icon: Icons.trending_down_rounded,
                  color: kError),
              const SizedBox(height: 8),
              ...weak.map((t) => _TopicTile(
                    topic: t,
                    onTap: () => controller.openTopic(t.id),
                  )),
              if (weak.isEmpty)
                const _EmptySection(
                    label: 'No weak areas yet — keep practicing!'),

              const SizedBox(height: 24),
              _SectionHeader(
                  label: 'Strong Areas',
                  icon: Icons.trending_up_rounded,
                  color: kSuccess),
              const SizedBox(height: 8),
              ...strong.map((t) => _TopicTile(
                    topic: t,
                    onTap: () => controller.openTopic(t.id),
                  )),
              if (strong.isEmpty)
                const _EmptySection(
                    label: 'No strong areas yet — start a topic!'),

              const SizedBox(height: 32),
            ],
          ),
        );
      }),
    );
  }
}

// ── Suggested next card ───────────────────────────────────────────────────────

class _SuggestedNextCard extends StatelessWidget {
  const _SuggestedNextCard({
    required this.topicId,
    required this.label,
    required this.onTap,
  });

  final String topicId;
  /// Human-readable label to display (e.g. "Async Programming"); falls back to topicId if not set.
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        decoration: BoxDecoration(
          color: const Color(0xFF1E1830),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: kAccentPurple),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: kAccentPurple.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Icon(Icons.auto_awesome_rounded,
                  color: kAccentPurple, size: 20),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Suggested Next',
                    style: GoogleFonts.inter(
                      color: kTextSecondary,
                      fontSize: 12,
                      letterSpacing: 0.5,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    label,
                    style: GoogleFonts.inter(
                      color: kTextPrimary,
                      fontSize: 15,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),
            const Icon(Icons.arrow_forward_ios_rounded,
                size: 14, color: kAccentPurple),
          ],
        ),
      ),
    );
  }
}

// ── Section header ────────────────────────────────────────────────────────────

class _SectionHeader extends StatelessWidget {
  const _SectionHeader({
    required this.label,
    required this.icon,
    required this.color,
  });

  final String label;
  final IconData icon;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, size: 16, color: color),
        const SizedBox(width: 8),
        Text(
          label.toUpperCase(),
          style: GoogleFonts.inter(
            color: kTextSecondary,
            fontSize: 12,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.8,
          ),
        ),
      ],
    );
  }
}

// ── Empty section placeholder ─────────────────────────────────────────────────

class _EmptySection extends StatelessWidget {
  const _EmptySection({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: Text(
        label,
        style: const TextStyle(color: kTextSecondary, fontSize: 14),
      ),
    );
  }
}

// ── Topic tile ────────────────────────────────────────────────────────────────

class _TopicTile extends StatelessWidget {
  const _TopicTile({required this.topic, required this.onTap});

  final Topic topic;
  final VoidCallback onTap;

  Color _barColor() {
    if (topic.score < 0.4) return kError;
    if (topic.score < 0.7) return kAccentBlue;
    return kSuccess;
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          color: kCard,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: kDivider),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Text(
                    topic.label,
                    style: const TextStyle(
                      color: kTextPrimary,
                      fontSize: 14,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Text(
                  '${(topic.score * 100).toInt()}%',
                  style: TextStyle(
                    color: _barColor(),
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            TweenAnimationBuilder<double>(
              tween: Tween(begin: 0.0, end: topic.score),
              duration: const Duration(milliseconds: 800),
              curve: Curves.easeOut,
              builder: (_, value, __) => ClipRRect(
                borderRadius: BorderRadius.circular(4),
                child: LinearProgressIndicator(
                  value: value,
                  minHeight: 5,
                  backgroundColor: kBackground,
                  valueColor: AlwaysStoppedAnimation<Color>(_barColor()),
                ),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Practice this topic →',
              style: TextStyle(
                color: kAccentPurple.withValues(alpha: 0.9),
                fontSize: 12,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
