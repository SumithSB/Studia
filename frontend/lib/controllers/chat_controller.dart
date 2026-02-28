import 'dart:io';

import 'package:file_picker/file_picker.dart';
import 'package:get/get.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import '../models/enums.dart';
import '../services/api_service.dart';
import '../services/audio_service.dart';
import '../services/speech_tts_service.dart';
import '../theme/app_theme.dart';

class ChatController extends GetxController {
  final _api = Get.find<ApiService>();
  final _audio = Get.find<AudioService>();
  final _speechTts = Get.find<SpeechTtsService>();

  final messages = <Map<String, String>>[].obs;
  final streamingContent = ''.obs;
  final isLoading = false.obs;
  final toolStatus = RxnString();
  final voiceState = VoiceState.idle.obs;
  final inputMode = InputMode.chat.obs;
  final pendingAttachments = <File>[].obs;
  final suggestedTopicId = RxnString();
  final suggestedTopicLabel = RxnString();
  final speakResponses = true.obs;

  String _sessionId = 'default';

  static const _maxAttachments = 5;

  @override
  void onInit() {
    super.onInit();
    _loadSession();
  }

  // ── Session ──────────────────────────────────────────────────────────────────

  Future<void> _loadSession() async {
    final prefs = await SharedPreferences.getInstance();
    final sid = prefs.getString('session_id');
    if (sid != null) {
      _sessionId = sid;
    } else {
      final newId = DateTime.now().millisecondsSinceEpoch.toString();
      await prefs.setString('session_id', newId);
      _sessionId = newId;
    }
    final modeIndex = prefs.getInt('input_mode');
    if (modeIndex != null &&
        modeIndex >= 0 &&
        modeIndex < InputMode.values.length) {
      inputMode.value = InputMode.values[modeIndex];
    }
    // Voice mode implies speak on; otherwise restore saved preference
    if (inputMode.value == InputMode.voice) {
      speakResponses.value = true;
      await _persistSpeakResponses(true);
    } else {
      final speak = prefs.getBool('speak_responses');
      if (speak != null) speakResponses.value = speak;
    }

    try {
      final history = await _api.getSessionHistory(_sessionId);
      messages.value = history
          .map((e) => {
                'role': e['role'] as String? ?? 'user',
                'content': e['content'] as String? ?? '',
              })
          .toList();
    } catch (_) {}
    _fetchSuggestedTopic();
  }

  // ── Preferences ──────────────────────────────────────────────────────────────

  Future<void> setInputMode(InputMode mode) async {
    inputMode.value = mode;
    if (mode == InputMode.voice) {
      speakResponses.value = true;
      await _persistSpeakResponses(true);
    }
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt('input_mode', mode.index);
  }

  Future<void> _persistSpeakResponses(bool value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('speak_responses', value);
  }

  Future<void> setSpeakResponses(bool value) async {
    speakResponses.value = value;
    await _persistSpeakResponses(value);
  }

  // ── Topic suggestion ─────────────────────────────────────────────────────────

  Future<void> _fetchSuggestedTopic() async {
    try {
      final p = await _api.getProgress();
      final next = p['suggested_next'] as String?;
      final nextLabel = p['suggested_next_label'] as String?;
      if (!isClosed) {
        suggestedTopicId.value =
            (next != null && next.isNotEmpty) ? next : null;
        suggestedTopicLabel.value =
            (nextLabel != null && nextLabel.isNotEmpty) ? nextLabel : null;
      }
    } catch (_) {
      if (!isClosed) {
        suggestedTopicId.value = null;
        suggestedTopicLabel.value = null;
      }
    }
  }

  void dismissTopic() {
    suggestedTopicId.value = null;
    suggestedTopicLabel.value = null;
  }

  // ── Attachments ───────────────────────────────────────────────────────────────

  Future<void> pickAttachments() async {
    if (isLoading.value) return;
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf', 'docx', 'doc', 'txt', 'zip'],
      allowMultiple: true,
    );
    if (result == null || result.files.isEmpty) return;
    for (final f in result.files) {
      if (pendingAttachments.length >= _maxAttachments) break;
      if (f.path != null) pendingAttachments.add(File(f.path!));
    }
  }

  void removeAttachment(int index) {
    pendingAttachments.removeAt(index);
  }

  // ── Send orchestration ────────────────────────────────────────────────────────

  /// Returns true if a send was initiated (caller should clear the text field).
  bool handleSend(String text) {
    if (isLoading.value) return false;
    if (pendingAttachments.isNotEmpty) {
      _uploadThenSend(text);
      return true;
    }
    final trimmed = text.trim();
    if (trimmed.isEmpty) return false;
    sendMessage(trimmed);
    return true;
  }

  Future<void> _uploadThenSend(String userTypedText) async {
    if (pendingAttachments.isEmpty || isLoading.value) return;
    isLoading.value = true;
    try {
      final resumeFiles = <http.MultipartFile>[];
      File? linkedinFile;
      for (final f in pendingAttachments) {
        final name = f.path.split(RegExp(r'[/\\]')).last;
        final lower = name.toLowerCase();
        if (lower.endsWith('.zip')) {
          linkedinFile ??= f;
        } else {
          final bytes = await f.readAsBytes();
          resumeFiles
              .add(http.MultipartFile.fromBytes('resumes', bytes, filename: name));
        }
      }
      http.MultipartFile? linkedinZip;
      if (linkedinFile != null) {
        final bytes = await linkedinFile.readAsBytes();
        final name = linkedinFile.path.split(RegExp(r'[/\\]')).last;
        linkedinZip =
            http.MultipartFile.fromBytes('linkedin', bytes, filename: name);
      }
      await _api.uploadProfileFromFiles(
          resumeFiles: resumeFiles, linkedinZip: linkedinZip);
      if (isClosed) return;
      pendingAttachments.clear();
      Get.snackbar(
        'Done',
        'Profile updated from your uploads.',
        backgroundColor: kCard,
        colorText: kTextPrimary,
        duration: const Duration(seconds: 3),
      );
      final message = userTypedText.isNotEmpty
          ? userTypedText
          : "I've uploaded my resume / LinkedIn — please use it for our conversation.";
      sendMessage(message);
    } catch (e) {
      if (isClosed) return;
      isLoading.value = false;
      Get.snackbar(
        'Upload failed',
        '$e',
        backgroundColor: kCard,
        colorText: kTextPrimary,
        duration: const Duration(seconds: 3),
      );
    }
  }

  // ── Chat streaming ────────────────────────────────────────────────────────────

  Future<void> sendMessage(String text) async {
    if (text.trim().isEmpty || isLoading.value) return;
    messages.add({'role': 'user', 'content': text});
    isLoading.value = true;
    streamingContent.value = '';
    toolStatus.value = null;
    suggestedTopicId.value = null;
    suggestedTopicLabel.value = null;

    try {
      await for (final event in _api.streamChat(text, _sessionId)) {
        if (isClosed) return;
        if (event['tool_call'] != null) {
          final tool = event['tool_call'] as String? ?? '';
          final args = event['args'] as Map<String, dynamic>?;
          toolStatus.value = _toolStatusLabel(tool, args);
        }
        if (event['token'] != null) {
          toolStatus.value = null;
          streamingContent.value += event['token'] as String;
        }
        if (event['done'] == true) {
          final content = streamingContent.value;
          messages.add({'role': 'assistant', 'content': content});
          streamingContent.value = '';
          toolStatus.value = null;
          isLoading.value = false;
          _fetchSuggestedTopic();
          // In Voice mode, speak replies; in Chat mode, text only.
          if (inputMode.value == InputMode.voice) {
            _playTtsIfEnabled(content);
          }
        }
      }
    } catch (e) {
      if (isClosed) return;
      messages.add({'role': 'assistant', 'content': 'Error: $e'});
      isLoading.value = false;
      streamingContent.value = '';
      toolStatus.value = null;
    }
  }

  // ── Voice ─────────────────────────────────────────────────────────────────────
  // On-device STT (speech_to_text) then streamChat; TTS via flutter_tts. Backend text-only.

  Future<void> toggleVoice() async {
    if (voiceState.value == VoiceState.recording) {
      voiceState.value = VoiceState.processing;
      final transcript = await _speechTts.stopListening();
      if (transcript.isEmpty) {
        voiceState.value = VoiceState.idle;
        _voiceErrorSnackbar('Could not hear you. Please speak clearly and try again.');
        return;
      }
      messages.add({'role': 'user', 'content': transcript});
      try {
        isLoading.value = true;
        streamingContent.value = '';
        toolStatus.value = null;
        suggestedTopicId.value = null;
        suggestedTopicLabel.value = null;

        bool didDone = false;
        await for (final event in _api.streamChat(transcript, _sessionId)) {
          if (isClosed) return;
          if (event['tool_call'] != null) {
            final tool = event['tool_call'] as String? ?? '';
            final args = event['args'] as Map<String, dynamic>?;
            toolStatus.value = _toolStatusLabel(tool, args);
          }
          if (event['token'] != null) {
            toolStatus.value = null;
            streamingContent.value += event['token'] as String;
          }
          if (event['done'] == true) {
            didDone = true;
            final content = streamingContent.value;
            messages.add({'role': 'assistant', 'content': content});
            streamingContent.value = '';
            toolStatus.value = null;
            isLoading.value = false;
            voiceState.value = VoiceState.idle;
            _fetchSuggestedTopic();
            _playTtsIfEnabled(content);
            return;
          }
        }
        if (!didDone && streamingContent.value.trim().isNotEmpty) {
          final content = streamingContent.value;
          messages.add({'role': 'assistant', 'content': content});
          streamingContent.value = '';
          _fetchSuggestedTopic();
          _playTtsIfEnabled(content);
        }
      } catch (e) {
        if (isClosed) return;
        messages.add({'role': 'assistant', 'content': 'Error: $e'});
        _voiceErrorSnackbar('Voice request failed');
      } finally {
        if (!isClosed) {
          voiceState.value = VoiceState.idle;
          isLoading.value = false;
          streamingContent.value = '';
          toolStatus.value = null;
        }
      }
    } else if (voiceState.value == VoiceState.idle) {
      final ok = await _audio.hasPermission();
      if (!ok) {
        _voiceErrorSnackbar('Microphone access is required for voice');
        return;
      }
      try {
        await _audio.stopPlayback();
        await _speechTts.stopTts();
        final available = await _speechTts.initStt();
        if (!available) {
          _voiceErrorSnackbar('Speech recognition not available');
          return;
        }
        await _speechTts.startListening(onResult: (_) {});
        voiceState.value = VoiceState.recording;
      } catch (e) {
        _voiceErrorSnackbar('Could not start listening: $e');
      }
    }
  }

  void _voiceErrorSnackbar(String message) {
    Get.snackbar(
      'Voice',
      message,
      backgroundColor: kCard,
      colorText: kTextPrimary,
      duration: const Duration(seconds: 3),
    );
  }

  // ── TTS ───────────────────────────────────────────────────────────────────────
  // On-device TTS (flutter_tts). No backend.

  Future<void> _playTtsIfEnabled(String content) async {
    if (!speakResponses.value) return;
    if (content.trim().isEmpty) return;
    try {
      await _speechTts.speak(content);
    } catch (e) {
      if (isClosed) return;
      if (inputMode.value == InputMode.voice) {
        _voiceErrorSnackbar('Could not play voice: $e');
      }
    }
  }

  // ── Helpers ──────────────────────────────────────────────────────────────────

  static String _toolStatusLabel(String tool, Map<String, dynamic>? args) {
    switch (tool) {
      case 'research_company':
        final company = args?['company']?.toString() ?? '';
        return company.isEmpty
            ? 'Researching company...'
            : 'Researching $company...';
      case 'parse_jd':
        return 'Analyzing job description...';
      case 'get_progress':
        return 'Checking your progress...';
      case 'lookup_curriculum':
        return 'Looking up topics...';
      case 'update_topic_score':
        return 'Updating topic...';
      default:
        return 'Working...';
    }
  }
}
