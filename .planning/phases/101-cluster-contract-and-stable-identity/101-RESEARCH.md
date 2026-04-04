# 101 Research

- The query index already had the right persistence boundary for recurring pattern mining.
- The main technical risk was circularity between a new cluster module and the index package. The
  final implementation kept cluster logic in its own module and used lazy index-package exports so
  stable cluster helpers remain importable without recursive package initialization.
- The insight fixture workspace already contained enough repeated prompt/failure/transition shapes
  to prove deterministic cluster identity over both runs and comparisons.
