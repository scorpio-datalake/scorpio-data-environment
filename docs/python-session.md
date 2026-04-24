# Scorpio Python session (Epic 1)

The `scorpio` package under `python/scorpio/` exposes a **session** entry point aligned with `Planning/Phase1.md` — Epic 1 (Python-native session) and the coordinator **REST shim** tracked for Epic 7/8 (Compose comments reference replacing `http-echo` stubs).

## Product scope (lake, not Parquet-only)

Epic 1 requires that the session and catalog story stay consistent with broader lake plans:

- [docs/data-sources-databases-sftp.md](data-sources-databases-sftp.md) — databases / SFTP (ELT vs federation vs custom `TableProvider`).
- [docs/table-formats-metastore-scope.md](table-formats-metastore-scope.md) — Hive / Iceberg / Delta and metastore scope.

The MVP `scorpio.catalog.Catalog` keeps **client-side** registrations (`register_parquet`, `register_uri`) so names and hooks do not contradict those documents; pushing catalog state to distributed engines is deferred to later epics.

## Public API (overview)

| Symbol | Role |
|--------|------|
| `Session.connect(...)` | Short constructor using env + optional overrides. |
| `Session.builder()` / `SessionBuilder` | Fluent configuration. |
| `Session.local(...)` | Catalog-only; `sql()` is unavailable (raises `ScorpioNotImplementedError`). |
| `session.catalog` | `Catalog` instance (thread-safe in-process registry). |
| `session.sql(query)` | `POST /v1/sql` on coordinator; decodes **Arrow IPC stream** or JSON tabular payload to `pyarrow.Table`. |
| `session.ping()` | `GET /` (or health) — returns `True` on HTTP 2xx. |
| `session.start()` | Eager `POST /v1/sessions`. |
| `session.stop()` | Best-effort `POST /v1/sessions/{id}/close`. |
| `session.config()` | Redacted mapping for logging/tests. |
| `session.version()` | Python package version plus optional `GET /v1/version` body. |
| `session.verify_scheduler_reachable()` | gRPC channel readiness to `SCORPIO_SCHEDULER_HOST:SCORPIO_SCHEDULER_PORT` (TCP / protocol handshake only; RPC stubs live under `docs/grpc-codegen.md`). |

## Coordinator REST contract (MVP)

Until the real coordinator ships, the Compose stack may still use `hashicorp/http-echo` for port **8080** (`deploy/docker-compose/docker-compose.scorpio-stack.yml`). The Python client expects the following routes when you run against a real API:

| Method | Path | Notes |
|--------|------|--------|
| `GET` | `/` or `/health` | Liveness for `ping()`. |
| `GET` | `/v1/version` | Optional; surfaced in `version()["coordinator"]`. |
| `POST` | `/v1/sessions` | JSON body may include `tenant_id`; response `{"session_id":"..."}`. |
| `POST` | `/v1/sql` | JSON body `{"session_id","sql","tenant_id"}`; response **Arrow IPC stream** (preferred) or JSON `{"columns":[...],"rows":[[...],...]}`. |
| `POST` | `/v1/sessions/{id}/close` | Session teardown. |

All mutating coordinator calls send header **`X-Scorpio-Tenant-Id`** when `SCORPIO_TENANT_ID` (or builder `tenant_id`) is set. Optional **`Authorization: Bearer …`** is sent when `SCORPIO_AUTH_BEARER` is set (placeholder for OAuth2 / service tokens).

## Environment variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `SCORPIO_COORDINATOR_URL` | Base URL for REST coordinator (no trailing slash required). | `http://127.0.0.1:8080` |
| `SCORPIO_TENANT_ID` | Tenant binding (`X-Scorpio-Tenant-Id`). | unset |
| `SCORPIO_AUTH_BEARER` | Bearer token for `Authorization` (secret — do not log). | unset |
| `SCORPIO_SCHEDULER_HOST` | Scheduler hostname for gRPC reachability check. | unset |
| `SCORPIO_SCHEDULER_PORT` | Scheduler gRPC port (e.g. **50050** in Compose). | unset |
| `SCORPIO_CONNECT_TIMEOUT` | Seconds for gRPC `channel_ready_future` in `verify_scheduler_reachable`. | `10` |
| `SCORPIO_REQUEST_TIMEOUT` | Per-request HTTP timeout (seconds). | `120` |
| `SCORPIO_HTTP_RETRIES` | Retries for connection errors and HTTP **503**. | `3` |
| `SCORPIO_HTTP_RETRY_BACKOFF_SEC` | Linear backoff multiplier between retries. | `0.4` |
| `SCORPIO_INTEGRATION` | Set to `1` to enable optional `pytest` integration tests against a live stack. | unset |

See also [docs/deployment.md](deployment.md) for Compose ports and image wiring.

## Distributed SQL acceptance

Phase 1 acceptance calls for a Python **distributed** SQL path (executor participation). Today:

- The **Rust** `scorpio` client exercises the full DataFusion / Ballista scheduler path (see `engine/README.md`).
- The **Python** session implements the **coordinator HTTP contract** and Arrow/JSON decoding so a future API (Epic 8) can front the same engine without redesign.
- Opt-in integration: run Compose with a coordinator implementing the routes above, export `SCORPIO_INTEGRATION=1`, and run `pytest` from `python/scorpio/` (see `tests/test_session_http_roundtrip.py` marker `integration`).

## Tests

From `python/scorpio/` after `pip install -e ".[dev]"`:

```bash
pytest
```

CI: `.github/workflows/scorpio-python.yml`.
