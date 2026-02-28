import 'package:audioplayers/audioplayers.dart';
import 'package:record/record.dart';

import 'audio_service_io.dart' if (dart.library.html) 'audio_service_web.dart' as platform_impl;

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
    return platform_impl.getRecordedBytes(path);
  }

  Future<String> getTempPath() async {
    return platform_impl.getTempPath();
  }

  Future<void> stopPlayback() async {
    await _player.stop();
  }
}
