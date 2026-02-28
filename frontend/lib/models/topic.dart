class Topic {
  final String id;
  final String label;
  final double score;

  Topic({required this.id, required this.label, required this.score});

  factory Topic.fromJson(Map<String, dynamic> json) {
    return Topic(
      id: json['id'] as String? ?? '',
      label: json['label'] as String? ?? '',
      score: (json['score'] as num?)?.toDouble() ?? 0.0,
    );
  }
}
