import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;

const baseUrl = 'http://127.0.0.1:8000';

class ApiService {
  /// Returns true if profile.json exists (user has completed onboarding).
  Future<bool> hasProfile() async {
    final r = await http.get(Uri.parse('$baseUrl/profile/status'));
    if (r.statusCode != 200) return false;
    final map = jsonDecode(r.body) as Map<String, dynamic>;
    return map['exists'] == true;
  }

  /// Build profile from resume files and optional LinkedIn ZIP. Throws on error.
  Future<Map<String, dynamic>> uploadProfileFromFiles({
    required List<http.MultipartFile> resumeFiles,
    http.MultipartFile? linkedinZip,
  }) async {
    final uri = Uri.parse('$baseUrl/profile/from-uploads');
    final req = http.MultipartRequest('POST', uri);
    for (final f in resumeFiles) {
      req.files.add(f);
    }
    if (linkedinZip != null) req.files.add(linkedinZip);

    final streamed = await req.send();
    final response = await http.Response.fromStream(streamed);
    if (response.statusCode >= 400) {
      String msg = 'Failed to create profile';
      try {
        final body = jsonDecode(response.body) as Map<String, dynamic>;
        final d = body['detail'];
        msg = d is List ? d.join(' ') : (d?.toString() ?? msg);
      } catch (_) {}
      throw Exception(msg);
    }
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getProgress() async {
    final r = await http.get(Uri.parse('$baseUrl/progress'));
    if (r.statusCode != 200) throw Exception('Failed to load progress');
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<List<Map<String, dynamic>>> getSessionHistory(String sessionId) async {
    final r = await http.get(
      Uri.parse('$baseUrl/session/history').replace(
        queryParameters: {'session_id': sessionId},
      ),
    );
    if (r.statusCode != 200) throw Exception('Failed to load history');
    final list = jsonDecode(r.body) as List;
    return list.map((e) => e as Map<String, dynamic>).toList();
  }

  /// Generate TTS audio for client playback. Returns bytes or null on failure.
  Future<Uint8List?> getTtsAudio(String text) async {
    if (text.trim().isEmpty) return null;
    final r = await http.post(
      Uri.parse('$baseUrl/tts'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'text': text}),
    );
    if (r.statusCode != 200) return null;
    return r.bodyBytes;
  }

  Future<Map<String, dynamic>> research(String type, String value) async {
    final r = await http.post(
      Uri.parse('$baseUrl/research'),
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: 'type=${Uri.encodeComponent(type)}&value=${Uri.encodeComponent(value)}',
    );
    if (r.statusCode != 200) throw Exception('Research failed');
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Stream<Map<String, dynamic>> streamChat(String message, String sessionId) async* {
    final client = http.Client();
    final req = http.Request('POST', Uri.parse('$baseUrl/chat'));
    req.headers['Accept'] = 'text/event-stream';
    req.headers['Content-Type'] = 'application/json';
    req.body = jsonEncode({'message': message, 'session_id': sessionId});

    final streamed = await client.send(req);
    var buffer = '';
    await for (final chunk in streamed.stream.transform(utf8.decoder)) {
      buffer += chunk;
      final lines = buffer.split('\n');
      buffer = lines.removeLast();
      for (final line in lines) {
        if (line.startsWith('data: ')) {
          final data = line.substring(6);
          if (data.isEmpty || data == '[DONE]') continue;
          try {
            yield jsonDecode(data) as Map<String, dynamic>;
          } catch (_) {}
        }
      }
    }
  }

  Stream<Map<String, dynamic>> streamVoice(
    List<int> audioBytes,
    String sessionId,
  ) async* {
    final uri = Uri.parse('$baseUrl/voice');
    final req = http.MultipartRequest('POST', uri);
    req.fields['session_id'] = sessionId;
    req.files.add(http.MultipartFile.fromBytes(
      'audio',
      audioBytes,
      filename: 'audio.wav',
    ));

    final client = http.Client();
    final streamed = await client.send(req);
    var buffer = '';
    await for (final chunk in streamed.stream.transform(utf8.decoder)) {
      buffer += chunk;
      final lines = buffer.split('\n');
      buffer = lines.removeLast();
      for (final line in lines) {
        if (line.startsWith('data: ')) {
          final data = line.substring(6);
          if (data.isEmpty) continue;
          try {
            yield jsonDecode(data) as Map<String, dynamic>;
          } catch (_) {}
        }
      }
    }
  }
}
