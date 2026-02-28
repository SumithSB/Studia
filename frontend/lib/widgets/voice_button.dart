import 'package:flutter/material.dart';
import '../models/enums.dart';
import '../theme/app_theme.dart';

class VoiceButton extends StatefulWidget {
  const VoiceButton({
    super.key,
    required this.state,
    required this.onPressed,
  });

  final VoiceState state;
  final VoidCallback onPressed;

  @override
  State<VoiceButton> createState() => _VoiceButtonState();
}

class _VoiceButtonState extends State<VoiceButton>
    with SingleTickerProviderStateMixin {
  late final AnimationController _pulse;
  late final Animation<double> _scale;

  @override
  void initState() {
    super.initState();
    _pulse = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    );
    _scale = Tween<double>(begin: 1.0, end: 1.22).animate(
      CurvedAnimation(parent: _pulse, curve: Curves.easeInOut),
    );
    if (widget.state == VoiceState.recording) {
      _pulse.repeat(reverse: true);
    }
  }

  @override
  void didUpdateWidget(VoiceButton old) {
    super.didUpdateWidget(old);
    if (widget.state == VoiceState.recording && !_pulse.isAnimating) {
      _pulse.repeat(reverse: true);
    } else if (widget.state != VoiceState.recording && _pulse.isAnimating) {
      _pulse.stop();
      _pulse.reset();
    }
  }

  @override
  void dispose() {
    _pulse.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: widget.state == VoiceState.processing ? null : widget.onPressed,
      child: AnimatedBuilder(
        animation: _pulse,
        builder: (context, child) {
          final scale = widget.state == VoiceState.recording ? _scale.value : 1.0;
          return Transform.scale(scale: scale, child: child);
        },
        child: _buildButtonContent(),
      ),
    );
  }

  Widget _buildButtonContent() {
    switch (widget.state) {
      case VoiceState.idle:
        return _CircleButton(
          icon: Icons.mic_rounded,
          iconColor: kTextSecondary,
          bgColor: kCard,
          borderColor: kDivider,
        );

      case VoiceState.recording:
        return _CircleButton(
          icon: Icons.stop_rounded,
          iconColor: kError,
          bgColor: const Color(0xFF2A1212),
          borderColor: kError,
          glowColor: kError.withValues(alpha: 0.3),
        );

      case VoiceState.processing:
        return Container(
          width: 48,
          height: 48,
          decoration: BoxDecoration(
            color: kCard,
            shape: BoxShape.circle,
            border: Border.all(color: kDivider),
          ),
          child: const Padding(
            padding: EdgeInsets.all(14),
            child: CircularProgressIndicator(
              strokeWidth: 2,
              color: kAccentPurple,
            ),
          ),
        );
    }
  }
}

class _CircleButton extends StatelessWidget {
  const _CircleButton({
    required this.icon,
    required this.iconColor,
    required this.bgColor,
    required this.borderColor,
    this.glowColor,
  });

  final IconData icon;
  final Color iconColor;
  final Color bgColor;
  final Color borderColor;
  final Color? glowColor;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 48,
      height: 48,
      decoration: BoxDecoration(
        color: bgColor,
        shape: BoxShape.circle,
        border: Border.all(color: borderColor, width: 1.5),
        boxShadow: glowColor != null
            ? [BoxShadow(color: glowColor!, blurRadius: 12, spreadRadius: 2)]
            : null,
      ),
      child: Icon(icon, color: iconColor, size: 22),
    );
  }
}
