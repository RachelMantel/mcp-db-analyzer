# Security Notes

## Transport security
- Prefer encrypted connections (TLS/SSL). Avoid plain-text DB connections.
- Ensure credentials are stored securely and not hard-coded in source.

## Operational safety
- The tools only read metadata; they do not modify schemas.
- Row-count stats can be expensive on large databases.

## Privacy
- The server returns schema metadata. Treat responses as sensitive if
  table/column names could reveal private business logic.
