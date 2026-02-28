import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../controllers/chat_controller.dart';
import '../models/enums.dart';
import '../theme/app_theme.dart';
import 'topic_chip.dart';
import 'voice_button.dart';

class ChatInputBar extends GetView<ChatController> {
  const ChatInputBar({super.key, required this.textController});

  final TextEditingController textController;

  void _handleSend() {
    if (controller.handleSend(textController.text)) {
      textController.clear();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Obx(() {
      final loading = controller.isLoading.value;
      final mode = controller.inputMode.value;
      final topicId = controller.suggestedTopicId.value;
      final topicLabel = controller.suggestedTopicLabel.value;
      final toolStatus = controller.toolStatus.value;
      final attachments = controller.pendingAttachments;

      return Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Tool status bar
          if (toolStatus != null)
            Container(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
              decoration: const BoxDecoration(
                border: Border(top: BorderSide(color: kDivider)),
              ),
              child: Row(
                children: [
                  const SizedBox(
                    width: 12,
                    height: 12,
                    child: CircularProgressIndicator(
                      strokeWidth: 1.5,
                      color: kAccentPurple,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    toolStatus,
                    style: const TextStyle(
                      color: kAccentPurple,
                      fontSize: 12,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ),
            ),

          // Bottom input container
          Container(
            decoration: const BoxDecoration(
              border: Border(top: BorderSide(color: kDivider)),
            ),
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Suggested topic chip
                if (topicId != null && !loading)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 10),
                    child: Align(
                      alignment: Alignment.centerLeft,
                      child: TopicChip(
                        label: (topicLabel != null && topicLabel.isNotEmpty)
                            ? topicLabel
                            : topicId,
                        onTap: () {
                          textController.text = "Let's talk about "
                              "${(topicLabel != null && topicLabel.isNotEmpty) ? topicLabel : topicId}";
                          controller.dismissTopic();
                        },
                      ),
                    ),
                  ),

                // Mode toggle
                SegmentedButton<InputMode>(
                  segments: const [
                    ButtonSegment<InputMode>(
                      value: InputMode.chat,
                      icon: Icon(Icons.chat_bubble_outline, size: 16),
                      label: Text('Chat'),
                    ),
                    ButtonSegment<InputMode>(
                      value: InputMode.voice,
                      icon: Icon(Icons.mic_none, size: 16),
                      label: Text('Voice'),
                    ),
                  ],
                  selected: {mode},
                  onSelectionChanged: (Set<InputMode> s) =>
                      controller.setInputMode(s.first),
                ),
                const SizedBox(height: 12),

                if (mode == InputMode.chat) ...[
                  // Attachment chips
                  if (attachments.isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Wrap(
                        spacing: 6,
                        runSpacing: 6,
                        children: [
                          for (var i = 0; i < attachments.length; i++)
                            Chip(
                              label: Text(
                                attachments[i]
                                    .path
                                    .split(RegExp(r'[/\\]'))
                                    .last,
                                overflow: TextOverflow.ellipsis,
                                maxLines: 1,
                              ),
                              deleteIcon: const Icon(Icons.close, size: 16),
                              onDeleted: () =>
                                  controller.removeAttachment(i),
                            ),
                        ],
                      ),
                    ),
                  // Chat input row
                  Row(
                    children: [
                      IconButton(
                        icon: const Icon(Icons.attach_file_rounded),
                        onPressed:
                            loading ? null : controller.pickAttachments,
                        tooltip: 'Attach resume or LinkedIn',
                      ),
                      Expanded(
                        child: TextField(
                          controller: textController,
                          decoration: const InputDecoration(
                            hintText: 'Type a message...',
                          ),
                          onSubmitted: (_) => _handleSend(),
                          enabled: !loading,
                          maxLines: null,
                          textInputAction: TextInputAction.send,
                        ),
                      ),
                      const SizedBox(width: 8),
                      loading
                          ? const SizedBox(
                              width: 40,
                              height: 40,
                              child: Center(
                                child: SizedBox(
                                  width: 20,
                                  height: 20,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    color: kAccentPurple,
                                  ),
                                ),
                              ),
                            )
                          : IconButton(
                              icon: const Icon(
                                Icons.send_rounded,
                                color: kAccentPurple,
                              ),
                              onPressed: _handleSend,
                            ),
                      const SizedBox(width: 4),
                      VoiceButton(
                        state: controller.voiceState.value,
                        onPressed: controller.toggleVoice,
                      ),
                    ],
                  ),
                ] else ...[
                  // Voice mode: Cursor-style — mic primary, optional text
                  if (controller.voiceState.value == VoiceState.recording)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Text(
                        'Listening… Tap stop to send',
                        style: TextStyle(
                          fontSize: 13,
                          color: kTextSecondary,
                        ),
                      ),
                    )
                  else if (loading ||
                      controller.voiceState.value == VoiceState.processing)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Text(
                        'Thinking…',
                        style: TextStyle(
                          fontSize: 13,
                          color: kTextSecondary,
                        ),
                      ),
                    )
                  else
                    Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Text(
                        'Tap mic to speak',
                        style: TextStyle(
                          fontSize: 13,
                          color: kTextSecondary,
                        ),
                      ),
                    ),
                  Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: textController,
                          decoration: const InputDecoration(
                            hintText: 'Add a message (optional)',
                            isDense: true,
                          ),
                          onSubmitted: (_) => _handleSend(),
                          enabled: !loading,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Transform.scale(
                        scale: 1.2,
                        child: VoiceButton(
                          state: controller.voiceState.value,
                          onPressed: controller.toggleVoice,
                        ),
                      ),
                    ],
                  ),
                ],
              ],
            ),
          ),
        ],
      );
    });
  }
}
