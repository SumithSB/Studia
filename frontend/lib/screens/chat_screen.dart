import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../widgets/message_bubble.dart';
import '../widgets/voice_button.dart';
import '../services/api_service.dart';
import '../services/audio_service.dart';
import 'progress_screen.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key, this.initialTopic});

  final String? initialTopic;

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final _api = ApiService();
  final _audio = AudioService();
  final _controller = TextEditingController();
  final _scrollController = ScrollController();

  List<Map<String, String>> _messages = [];
  String _streamingContent = '';
  bool _isLoading = false;
  VoiceState _voiceState = VoiceState.idle;
  String _sessionId = 'default';

  @override
  void initState() {
    super.initState();
    _loadSession();
    if (widget.initialTopic != null) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _sendMessage('Let\'s talk about ${widget.initialTopic}');
      });
    }
  }

  Future<void> _loadSession() async {
    final prefs = await SharedPreferences.getInstance();
    final sid = prefs.getString('session_id');
    if (sid != null) {
      setState(() => _sessionId = sid);
    } else {
      final newId = DateTime.now().millisecondsSinceEpoch.toString();
      await prefs.setString('session_id', newId);
      setState(() => _sessionId = newId);
    }
    try {
      final history = await _api.getSessionHistory(_sessionId);
      setState(() {
        _messages = history
            .map((e) => {
                  'role': e['role'] as String? ?? 'user',
                  'content': e['content'] as String? ?? '',
                })
            .toList();
      });
    } catch (_) {}
  }

  Future<void> _sendMessage(String text) async {
    if (text.trim().isEmpty || _isLoading) return;
    setState(() {
      _messages.add({'role': 'user', 'content': text});
      _isLoading = true;
      _streamingContent = '';
    });
    _controller.clear();

    try {
      await for (final event in _api.streamChat(text, _sessionId)) {
        if (!mounted) return;
        if (event['transcript'] != null) {
          // voice first event
          setState(() {
            _messages.add({'role': 'user', 'content': event['transcript']});
          });
        }
        if (event['token'] != null) {
          setState(() => _streamingContent += event['token']);
        }
        if (event['done'] == true) {
          setState(() {
            _messages.add({'role': 'assistant', 'content': _streamingContent});
            _streamingContent = '';
            _isLoading = false;
          });
        }
      }
    } catch (e) {
      setState(() {
        _messages.add({'role': 'assistant', 'content': 'Error: $e'});
        _isLoading = false;
        _streamingContent = '';
      });
    }
    if (mounted) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 200),
          curve: Curves.easeOut,
        );
      });
    }
  }

  Future<void> _toggleVoice() async {
    if (_voiceState == VoiceState.recording) {
      setState(() => _voiceState = VoiceState.processing);
      final path = await _audio.stopRecording();
      if (path != null) {
        final bytes = await _audio.getRecordedBytes(path);
        try {
          await for (final event in _api.streamVoice(bytes, _sessionId)) {
            if (!mounted) return;
            if (event['transcript'] != null) {
              setState(() {
                _messages.add({'role': 'user', 'content': event['transcript']});
              });
            }
            if (event['token'] != null) {
              setState(() => _streamingContent += event['token']);
            }
            if (event['done'] == true) {
              setState(() {
                _messages.add({'role': 'assistant', 'content': _streamingContent});
                _streamingContent = '';
                _voiceState = VoiceState.idle;
              });
            }
          }
        } catch (e) {
          setState(() {
            _messages.add({'role': 'assistant', 'content': 'Error: $e'});
            _voiceState = VoiceState.idle;
          });
        }
      } else {
        setState(() => _voiceState = VoiceState.idle);
      }
    } else if (_voiceState == VoiceState.idle) {
      final ok = await _audio.hasPermission();
      if (!ok) return;
      final path = await _audio.getTempPath();
      await _audio.startRecording(path);
      setState(() => _voiceState = VoiceState.recording);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Studia'),
        actions: [
          IconButton(
            icon: const Icon(Icons.analytics),
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => const ProgressScreen(),
                ),
              );
            },
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(8),
              itemCount: _messages.length + (_streamingContent.isNotEmpty ? 1 : 0),
              itemBuilder: (_, i) {
                if (i < _messages.length) {
                  final m = _messages[i];
                  return MessageBubble(
                    content: m['content']!,
                    isUser: m['role'] == 'user',
                  );
                }
                return MessageBubble(
                  content: _streamingContent,
                  isUser: false,
                );
              },
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    decoration: const InputDecoration(
                      hintText: 'Type a message...',
                      border: OutlineInputBorder(),
                    ),
                    onSubmitted: _sendMessage,
                    enabled: !_isLoading,
                  ),
                ),
                const SizedBox(width: 8),
                IconButton(
                  icon: const Icon(Icons.send),
                  onPressed: _isLoading
                      ? null
                      : () => _sendMessage(_controller.text),
                ),
                VoiceButton(state: _voiceState, onPressed: _toggleVoice),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
