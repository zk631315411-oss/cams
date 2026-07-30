# 001 Initial schema

Creates users, questions, immutable versions, edit tasks, reviews, position
snapshots, releases, release items, and audit events. Markdown bodies remain
filesystem content under `content/questions`; SQLite stores metadata and
version indexes only.
