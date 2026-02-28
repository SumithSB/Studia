import 'dart:io';
import 'dart:typed_data';
import 'package:audioplayers/audioplayers.dart';
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';

class AudioService {
  final _recorder = AudioRecorder();
  final _player = AudioPlayer();

  Future<bool> hasPermission() async {
    return await _recorder.hasPermission();
  }

  Future<void> startRecording(String path) async {
    const config = RecordConfig(
      encoder: AudioEncoder.wav,
      sampleRate: 16000,
      numChannels: 1,
    );
    await _recorder.start(config, path: path);
  }

  Future<String?> stopRecording() async {
    return await _recorder.stop();
  }

  Future<List<int>> getRecordedBytes(String path) async {
    final file = File(path);
    return await file.readAsBytes();
  }

  Future<String> getTempPath() async {
    final dir = await getTemporaryDirectory();
    return '${dir.path}/recording_${DateTime.now().millisecondsSinceEpoch}.wav';
  }

  /// Play TTS audio bytes (e.g. from /tts). Runs asynchronously.
  Future<void> playTtsFromBytes(Uint8List bytes) async {
    if (bytes.isEmpty) return;
    try {
      await _player.setSource(BytesSource(bytes, mimeType: 'audio/wav'));
      await _player.resume();
    } catch (_) {}
  }
}
