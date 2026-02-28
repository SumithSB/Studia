import 'package:http/http.dart' as http;

Future<String> getTempPath() async {
  return 'recording_${DateTime.now().millisecondsSinceEpoch}.wav';
}

Future<List<int>> getRecordedBytes(String path) async {
  final response = await http.get(Uri.parse(path));
  return response.bodyBytes;
}
