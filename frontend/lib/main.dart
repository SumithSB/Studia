import 'package:flutter/material.dart';
import 'package:get/get.dart';

import 'controllers/chat_controller.dart';
import 'controllers/onboarding_controller.dart';
import 'controllers/profile_controller.dart';
import 'routes/app_routes.dart';
import 'screens/chat_screen.dart';
import 'screens/onboarding_screen.dart';
import 'services/api_service.dart';
import 'services/audio_service.dart';
import 'services/speech_tts_service.dart';
import 'theme/app_theme.dart';

void main() {
  // Permanent app-scoped singletons — available before any route loads
  Get.put(ApiService(), permanent: true);
  Get.put(AudioService(), permanent: true);
  Get.put(SpeechTtsService(), permanent: true);

  // ProfileController drives the ProfileGate home widget
  Get.put(ProfileController());

  // Lazy controllers — created on first access
  Get.lazyPut(() => OnboardingController());
  Get.lazyPut(() => ChatController());

  runApp(const StudiaApp());
}

class StudiaApp extends StatelessWidget {
  const StudiaApp({super.key});

  @override
  Widget build(BuildContext context) {
    return GetMaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Studia',
      theme: AppTheme.dark,
      darkTheme: AppTheme.dark,
      themeMode: ThemeMode.dark,
      home: const _ProfileGate(),
      getPages: AppPages.pages,
    );
  }
}

/// Routes to ChatScreen or OnboardingScreen based on profile existence.
class _ProfileGate extends GetView<ProfileController> {
  const _ProfileGate();

  @override
  Widget build(BuildContext context) {
    return Obx(() {
      final hasProfile = controller.hasProfile.value;
      final error = controller.error.value;

      // Loading
      if (hasProfile == null) {
        return const Scaffold(
          backgroundColor: kBackground,
          body: Center(
            child: CircularProgressIndicator(color: kAccentPurple),
          ),
        );
      }

      // Backend unreachable
      if (error != null) {
        return Scaffold(
          backgroundColor: kBackground,
          body: Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.wifi_off_rounded,
                    size: 48, color: kTextSecondary),
                const SizedBox(height: 16),
                Text(
                  'Could not reach backend',
                  style: Theme.of(context)
                      .textTheme
                      .titleMedium
                      ?.copyWith(color: kTextPrimary),
                ),
                const SizedBox(height: 6),
                Text(
                  '$error',
                  style:
                      const TextStyle(color: kTextSecondary, fontSize: 12),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 20),
                TextButton(
                  onPressed: controller.check,
                  child: const Text('Retry',
                      style: TextStyle(color: kAccentPurple)),
                ),
              ],
            ),
          ),
        );
      }

      if (hasProfile) {
        return const ChatScreen();
      }
      return const OnboardingScreen();
    });
  }
}
