import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../controllers/chat_controller.dart';
import '../routes/app_routes.dart';
import '../theme/app_theme.dart';
import '../widgets/app_logo.dart';
import '../widgets/chat_input_bar.dart';
import '../widgets/message_list.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  late final ChatController _ctrl;
  final _textController = TextEditingController();
  final _scrollController = ScrollController();
  late final Worker _messagesWorker;
  late final Worker _streamingWorker;

  @override
  void initState() {
    super.initState();
    _ctrl = Get.find<ChatController>();
    _messagesWorker = ever(_ctrl.messages, (_) => _scrollToBottom());
    _streamingWorker = ever(_ctrl.streamingContent, (_) => _scrollToBottom());
  }

  @override
  void dispose() {
    _messagesWorker.dispose();
    _streamingWorker.dispose();
    _textController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scrollController.hasClients) return;
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 200),
        curve: Curves.easeOut,
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            AppLogo(size: 28),
            SizedBox(width: 10),
            Text('Studia'),
          ],
        ),
        actions: [
          // Volume toggle — reactive to speakResponses state
          Obx(() => IconButton(
                icon: Icon(
                  _ctrl.speakResponses.value
                      ? Icons.volume_up_rounded
                      : Icons.volume_off_rounded,
                  color: _ctrl.speakResponses.value
                      ? kAccentPurple
                      : kTextSecondary,
                ),
                onPressed: () =>
                    _ctrl.setSpeakResponses(!_ctrl.speakResponses.value),
                tooltip: _ctrl.speakResponses.value
                    ? 'Speaking on'
                    : 'Speaking off',
              )),
          IconButton(
            icon: const Icon(Icons.bar_chart_rounded),
            onPressed: () => Get.toNamed(Routes.progress),
            tooltip: 'Progress',
          ),
        ],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Container(height: 1, color: kDivider),
        ),
      ),
      body: Column(
        children: [
          Expanded(
            child: MessageList(scrollController: _scrollController),
          ),
          ChatInputBar(textController: _textController),
        ],
      ),
    );
  }
}
