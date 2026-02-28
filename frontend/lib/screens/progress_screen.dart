import 'package:flutter/material.dart';
import '../models/topic.dart';
import '../services/api_service.dart';
import 'chat_screen.dart';

class ProgressScreen extends StatefulWidget {
  const ProgressScreen({super.key});

  @override
  State<ProgressScreen> createState() => _ProgressScreenState();
}

class _ProgressScreenState extends State<ProgressScreen> {
  final _api = ApiService();
  Map<String, dynamic>? _progress;
  String _error = '';

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final p = await _api.getProgress();
      setState(() {
        _progress = p;
        _error = '';
      });
    } catch (e) {
      setState(() {
        _progress = null;
        _error = e.toString();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Progress'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _load,
          ),
        ],
      ),
      body: _error.isNotEmpty
          ? Center(child: Text('Error: $_error'))
          : _progress == null
              ? const Center(child: CircularProgressIndicator())
              : RefreshIndicator(
                  onRefresh: _load,
                  child: ListView(
                    padding: const EdgeInsets.all(16),
                    children: [
                      if ((_progress!['suggested_next'] as String?)?.isNotEmpty ?? false)
                        Card(
                          child: ListTile(
                            title: const Text('Suggested Next'),
                            subtitle: Text(_progress!['suggested_next']),
                            trailing: const Icon(Icons.arrow_forward),
                            onTap: () {
                              Navigator.pushReplacement(
                                context,
                                MaterialPageRoute(
                                  builder: (_) => ChatScreen(
                                    initialTopic: _progress!['suggested_next'],
                                  ),
                                ),
                              );
                            },
                          ),
                        ),
                      const SizedBox(height: 16),
                      const Text('Weak Areas', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                      ...((_progress!['weak'] as List?) ?? [])
                          .map((e) => Topic.fromJson(e as Map<String, dynamic>))
                          .map((t) => _TopicTile(topic: t, onTap: () => _openTopic(t.id))),
                      const SizedBox(height: 16),
                      const Text('Strong Areas', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                      ...((_progress!['strong'] as List?) ?? [])
                          .map((e) => Topic.fromJson(e as Map<String, dynamic>))
                          .map((t) => _TopicTile(topic: t, onTap: () => _openTopic(t.id))),
                    ],
                  ),
                ),
    );
  }

  void _openTopic(String id) {
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(
        builder: (_) => ChatScreen(initialTopic: id),
      ),
    );
  }
}

class _TopicTile extends StatelessWidget {
  final Topic topic;
  final VoidCallback onTap;

  const _TopicTile({required this.topic, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return ListTile(
      title: Text(topic.label),
      subtitle: LinearProgressIndicator(value: topic.score),
      trailing: Text('${(topic.score * 100).toInt()}%'),
      onTap: onTap,
    );
  }
}
