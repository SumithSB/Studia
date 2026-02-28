import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:google_fonts/google_fonts.dart';

import '../controllers/onboarding_controller.dart';
import '../theme/app_theme.dart';
import '../widgets/app_logo.dart';

class OnboardingScreen extends GetView<OnboardingController> {
  const OnboardingScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            AppLogo(size: 28),
            SizedBox(width: 10),
            Text('Studia'),
          ],
        ),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Container(height: 1, color: kDivider),
        ),
      ),
      body: Obx(() {
        final loading = controller.isLoading.value;
        final resumeFiles = controller.resumeFiles;
        final linkedinFile = controller.linkedinFile.value;
        final error = controller.error.value;

        return SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 24),

              // Intro text
              Text(
                'To personalize your interview prep, upload your resumes and optional LinkedIn export. Studia will build your profile automatically.',
                style: GoogleFonts.inter(
                  color: kTextSecondary,
                  fontSize: 15,
                  height: 1.6,
                ),
              ),
              const SizedBox(height: 32),

              // Resumes section
              Text(
                'RESUMES',
                style: GoogleFonts.inter(
                  color: kTextSecondary,
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  letterSpacing: 1.2,
                ),
              ),
              const SizedBox(height: 10),
              _UploadZone(
                icon: Icons.upload_file_rounded,
                title: 'Add resume files',
                subtitle: 'PDF, DOCX, or TXT',
                hasFiles: resumeFiles.isNotEmpty,
                badgeCount:
                    resumeFiles.isNotEmpty ? resumeFiles.length : null,
                onTap: loading ? null : controller.pickResumes,
              ),
              if (resumeFiles.isNotEmpty) ...[
                const SizedBox(height: 8),
                ...resumeFiles.map(
                  (f) => _FileRow(
                    name: f.path.split(RegExp(r'[/\\]')).last,
                    onRemove: () => controller.removeResume(f),
                  ),
                ),
              ],

              const SizedBox(height: 28),

              // LinkedIn section
              Text(
                'LINKEDIN EXPORT (OPTIONAL)',
                style: GoogleFonts.inter(
                  color: kTextSecondary,
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  letterSpacing: 1.2,
                ),
              ),
              const SizedBox(height: 6),
              Text(
                'Settings & Privacy → Data Privacy → Get a copy of your data',
                style: GoogleFonts.inter(
                    color: kTextSecondary, fontSize: 12),
              ),
              const SizedBox(height: 10),
              _UploadZone(
                icon: Icons.folder_zip_rounded,
                title: linkedinFile == null
                    ? 'Choose LinkedIn ZIP'
                    : linkedinFile.path
                        .split(RegExp(r'[/\\]'))
                        .last,
                subtitle: linkedinFile == null
                    ? 'ZIP file from LinkedIn'
                    : 'Tap to change',
                hasFiles: linkedinFile != null,
                onTap: loading ? null : controller.pickLinkedIn,
                trailing: linkedinFile != null
                    ? GestureDetector(
                        onTap: controller.removeLinkedIn,
                        child: const Icon(Icons.close,
                            size: 18, color: kTextSecondary),
                      )
                    : null,
              ),

              const SizedBox(height: 36),

              // Error
              if (error != null) ...[
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: kError.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(10),
                    border:
                        Border.all(color: kError.withValues(alpha: 0.4)),
                  ),
                  child: Text(
                    error,
                    style: const TextStyle(color: kError, fontSize: 14),
                  ),
                ),
                const SizedBox(height: 16),
              ],

              // Submit button
              FilledButton(
                onPressed: loading ? null : controller.submit,
                style: FilledButton.styleFrom(
                  backgroundColor: kAccentPurple,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14),
                  ),
                ),
                child: loading
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : Text(
                        'Create my profile',
                        style: GoogleFonts.inter(
                          fontSize: 15,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
              ),

              const SizedBox(height: 32),
            ],
          ),
        );
      }),
    );
  }
}

// ── Upload zone card ──────────────────────────────────────────────────────────

class _UploadZone extends StatelessWidget {
  const _UploadZone({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.hasFiles,
    this.badgeCount,
    this.onTap,
    this.trailing,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final bool hasFiles;
  final int? badgeCount;
  final VoidCallback? onTap;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          color: kCard,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: hasFiles ? kAccentPurple : kDivider,
            width: hasFiles ? 1.5 : 1,
          ),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: kAccentPurple.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(icon, color: kAccentPurple, size: 20),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    title,
                    style: const TextStyle(
                      color: kTextPrimary,
                      fontSize: 14,
                      fontWeight: FontWeight.w500,
                    ),
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 2),
                  Text(
                    subtitle,
                    style:
                        const TextStyle(color: kTextSecondary, fontSize: 12),
                  ),
                ],
              ),
            ),
            if (trailing != null) ...[
              const SizedBox(width: 8),
              trailing!,
            ] else if (badgeCount != null) ...[
              const SizedBox(width: 8),
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: kAccentPurple.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  '$badgeCount',
                  style: const TextStyle(
                    color: kAccentPurple,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

// ── Selected file row ─────────────────────────────────────────────────────────

class _FileRow extends StatelessWidget {
  const _FileRow({required this.name, required this.onRemove});

  final String name;
  final VoidCallback onRemove;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(top: 6),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: kBackground,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: kDivider),
      ),
      child: Row(
        children: [
          const Icon(Icons.insert_drive_file_rounded,
              size: 16, color: kTextSecondary),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              name,
              style: const TextStyle(color: kTextPrimary, fontSize: 13),
              overflow: TextOverflow.ellipsis,
            ),
          ),
          GestureDetector(
            onTap: onRemove,
            child: const Icon(Icons.close, size: 16, color: kTextSecondary),
          ),
        ],
      ),
    );
  }
}
