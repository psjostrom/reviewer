# Springa: API Contract & Schema

Check for backwards-incompatible changes: REST endpoint signatures, request/response shapes, database schema (Turso migrations), Nightscout-compatible endpoints (`/api/v1/entries`, `/api/v1/treatments`). If a POST body or query parameter changes, does every client (Strimma, Garmin apps) still work? Check that Nightscout compliance rules from CLAUDE.md are followed: `.json` suffix on GETs, MongoDB-style query params, correct data shapes.

Only return actual problems — no positive observations.
