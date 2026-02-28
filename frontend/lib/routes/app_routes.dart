import 'package:get/get.dart';

import '../controllers/progress_controller.dart';
import '../screens/progress_screen.dart';

abstract class Routes {
  static const progress = '/progress';
}

class ProgressBinding extends Bindings {
  @override
  void dependencies() {
    // fenix: true recreates the controller if previously deleted, giving
    // fresh data each time the user opens the Progress screen.
    Get.lazyPut(() => ProgressController(), fenix: true);
  }
}

abstract class AppPages {
  static final pages = [
    GetPage(
      name: Routes.progress,
      page: () => const ProgressScreen(),
      binding: ProgressBinding(),
    ),
  ];
}
