import 'package:flutter/material.dart';

enum VoiceState { idle, recording, processing }

class VoiceButton extends StatelessWidget {
  final VoiceState state;
  final VoidCallback onPressed;

  const VoiceButton({super.key, required this.state, required this.onPressed});

  @override
  Widget build(BuildContext context) {
    IconData icon;
    String label;
    Color color;

    switch (state) {
      case VoiceState.idle:
        icon = Icons.mic;
        label = '';
        color = Colors.grey;
        break;
      case VoiceState.recording:
        icon = Icons.stop;
        label = 'Recording...';
        color = Colors.red;
        break;
      case VoiceState.processing:
        icon = Icons.hourglass_empty;
        label = 'Processing...';
        color = Colors.orange;
        break;
    }

    return GestureDetector(
      onTap: onPressed,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: color, size: 28),
          if (label.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text(label, style: TextStyle(color: color, fontSize: 12)),
            ),
        ],
      ),
    );
  }
}
