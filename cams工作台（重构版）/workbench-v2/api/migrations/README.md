# Schema migrations

The local pilot uses SQLAlchemy metadata against SQLite. `001_initial` is
recorded in `schema_migrations` by `init_db()`. Subsequent production changes
must be additive migration modules and must update this ledger; no migration
may rewrite immutable version snapshots or release manifests.

For PostgreSQL, set `DATABASE_URL` to a SQLAlchemy PostgreSQL URL before the
first `init_db()` run. The models deliberately avoid SQLite-specific columns.
