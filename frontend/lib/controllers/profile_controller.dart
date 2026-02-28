import 'package:get/get.dart';
import '../services/api_service.dart';

class ProfileController extends GetxController {
  final _api = Get.find<ApiService>();

  final hasProfile = Rxn<bool>(); // null = loading, true/false = result
  final error = Rxn<Object>();

  @override
  void onInit() {
    super.onInit();
    check();
  }

  Future<void> check() async {
    hasProfile.value = null;
    error.value = null;
    try {
      hasProfile.value = await _api.hasProfile();
    } catch (e) {
      error.value = e;
      hasProfile.value = false;
    }
  }
}
