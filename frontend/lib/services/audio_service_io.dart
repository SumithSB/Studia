import 'dart:io';

import 'package:path_provider/path_provider.dart';

Future<String> getTempPath() async {
  final dir = await getTemporaryDirectory();
  return '${dir.path}/recording_${DateTime.now().millisecondsSinceEpoch}.wav';
}

Future<List<int>> getRecordedBytes(String path) async {
  final file = File(path);
  return await file.readAsBytes();
}
