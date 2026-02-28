import 'package:flutter/scheduler.dart';
import 'package:get/get.dart';

import '../models/topic.dart';
import '../services/api_service.dart';
import 'chat_controller.dart';

class ProgressController extends GetxController {
  final _api = Get.find<ApiService>();

  final isLoading = true.obs;
  final weakTopics = <Topic>[].obs;
  final strongTopics = <Topic>[].obs;
  final suggestedNext = RxnString();
  final suggestedNextLabel = RxnString();
  final error = RxnString();

  @override
  void onInit() {
    super.onInit();
    load();
  }

  Future<void> load() async {
    isLoading.value = true;
    error.value = null;
    try {
      final data = await _api.getProgress();
      weakTopics.value = ((data['weak'] as List?) ?? [])
          .map((e) => Topic.fromJson(e as Map<String, dynamic>))
          .toList();
      strongTopics.value = ((data['strong'] as List?) ?? [])
          .map((e) => Topic.fromJson(e as Map<String, dynamic>))
          .toList();
      suggestedNext.value = data['suggested_next'] as String?;
      suggestedNextLabel.value = data['suggested_next_label'] as String?;
    } catch (e) {
      error.value = e.toString();
    } finally {
      isLoading.value = false;
    }
  }

  void openTopic(String topicId) {
    Get.back();
    // After navigation animation, send initial message in ChatController
    SchedulerBinding.instance.addPostFrameCallback((_) {
      // ChatController is always alive (ChatScreen is shown inline in ProfileGate)
      final chat = Get.find<ChatController>();
      chat.sendMessage("Let's talk about $topicId");
    });
  }
}
