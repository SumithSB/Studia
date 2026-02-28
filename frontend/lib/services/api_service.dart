import 'dart:convert';
import 'package:http/http.dart' as http;

const baseUrl = 'http://127.0.0.1:8000';

class ApiService {
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
