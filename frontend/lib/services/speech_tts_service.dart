import 'package:flutter_tts/flutter_tts.dart';
import 'package:speech_to_text/speech_to_text.dart';

/// On-device STT (speech_to_text) and TTS (flutter_tts). Backend stays text-only.
class SpeechTtsService {
  final SpeechToText _speech = SpeechToText();
  final FlutterTts _tts = FlutterTts();

  String _lastRecognized = '';
  bool _sttInitialized = false;

  /// Initialize STT; call once before first listen. Returns true if available.
  Future<bool> initStt() async {
    if (_sttInitialized) return true;
    _sttInitialized = await _speech.initialize();
    return _sttInitialized;
  }

  /// Start listening; accumulate transcript in onResult. Call [stopListening] to get final text.
  Future<void> startListening({
    required void Function(String partial) onResult,
  }) async {
    _lastRecognized = '';
    await _speech.listen(
      onResult: (result) {
        _lastRecognized = result.recognizedWords;
        onResult(result.recognizedWords);
      },
      listenFor: const Duration(minutes: 2),
      pauseFor: const Duration(seconds: 3),
      listenOptions: SpeechListenOptions(
        partialResults: true,
        listenMode: ListenMode.dictation,
      ),
    );
  }

  /// Stop listening and return the final transcript.
  Future<String> stopListening() async {
    await _speech.stop();
    return _lastRecognized.trim();
  }

  /// Whether the speech engine is currently listening.
  bool get isListening => _speech.isListening;

  /// Speak text using platform TTS. No backend; no audio bytes.
  Future<void> speak(String text) async {
    if (text.trim().isEmpty) return;
    await _tts.stop();
    await _tts.setSpeechRate(0.5);
    await _tts.speak(text);
  }

  /// Stop TTS playback.
  Future<void> stopTts() async {
    await _tts.stop();
  }
}
