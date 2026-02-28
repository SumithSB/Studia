import 'package:flutter/material.dart';
import 'screens/chat_screen.dart';
import 'screens/progress_screen.dart';

void main() {
  runApp(const InterviewStudyBuddyApp());
}

class InterviewStudyBuddyApp extends StatelessWidget {
  const InterviewStudyBuddyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Studia',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
        useMaterial3: true,
      ),
      home: const ChatScreen(),
      routes: {
        '/chat': (_) => const ChatScreen(),
        '/progress': (_) => const ProgressScreen(),
      },
    );
  }
}
