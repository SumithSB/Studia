import 'dart:io';

import 'package:file_picker/file_picker.dart';
import 'package:get/get.dart';
import 'package:http/http.dart' as http;

import '../controllers/profile_controller.dart';
import '../services/api_service.dart';

class OnboardingController extends GetxController {
  final _api = Get.find<ApiService>();

  final resumeFiles = <File>[].obs;
  final linkedinFile = Rxn<File>();
  final isLoading = false.obs;
  final error = RxnString();

  Future<void> pickResumes() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf', 'docx', 'txt'],
      allowMultiple: true,
    );
    if (result == null) return;
    error.value = null;
    for (final f in result.files) {
      if (f.path != null) resumeFiles.add(File(f.path!));
    }
  }

  Future<void> pickLinkedIn() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['zip'],
      allowMultiple: false,
    );
    if (result == null || result.files.isEmpty) return;
    final f = result.files.single;
    if (f.path == null) return;
    linkedinFile.value = File(f.path!);
    error.value = null;
  }

  void removeResume(File f) => resumeFiles.remove(f);

  void removeLinkedIn() => linkedinFile.value = null;

  Future<void> submit() async {
    if (resumeFiles.isEmpty && linkedinFile.value == null) {
      error.value = 'Add at least one resume or the LinkedIn export.';
      return;
    }
    isLoading.value = true;
    error.value = null;
    try {
      final multipartResumes = <http.MultipartFile>[];
      for (final file in resumeFiles) {
        final bytes = await file.readAsBytes();
        final name = file.path.split(RegExp(r'[/\\]')).last;
        multipartResumes.add(
            http.MultipartFile.fromBytes('resumes', bytes, filename: name));
      }
      http.MultipartFile? linkedinZip;
      if (linkedinFile.value != null) {
        final bytes = await linkedinFile.value!.readAsBytes();
        final name = linkedinFile.value!.path.split(RegExp(r'[/\\]')).last;
        linkedinZip =
            http.MultipartFile.fromBytes('linkedin', bytes, filename: name);
      }
      await _api.uploadProfileFromFiles(
        resumeFiles: multipartResumes,
        linkedinZip: linkedinZip,
      );
      Get.find<ProfileController>().check();
    } catch (e) {
      error.value = e.toString().replaceFirst('Exception: ', '');
    } finally {
      isLoading.value = false;
    }
  }
}
