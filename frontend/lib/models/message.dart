class Message {
  final String role;
  final String content;
  final String? topicId;

  Message({required this.role, required this.content, this.topicId});

  factory Message.fromJson(Map<String, dynamic> json) {
    return Message(
      role: json['role'] as String? ?? 'user',
      content: json['content'] as String? ?? '',
      topicId: json['topic_detected'] as String?,
    );
  }
}
