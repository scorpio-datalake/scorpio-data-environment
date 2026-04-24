# Scorpio's Python API — session (Epic 1)

The `scorpio` package under `python/scorpio/` is **Scorpio's Python API** (also referred to in code and HTTP headers as **`scorpio-python-api`**): a **thin client** over the **Rust** Scorpio coordinator/engine. It does **not** run queries or scans in Python; all SQL goes to the coordinator (`POST /v1/sql`) per Epic 8 REST contract (Compose may still use stubs until the real API ships).

## Product scope (lake, not Parquet-only)

The session and catalog story must stay consistent with broader lake plans:

- [docs/data-sources-databases-sftp.md](data-sources-databases-sftp.md) — databases / SFTP (ELT vs federation vs custom `TableProvider`).
- [docs/table-formats-metastore-scope.md](table-formats-metastore-scope.md) — Hive / Iceberg / Delta and metastore scope.

`scorpio.catalog.Catalog` holds **logical names and paths** used when building SQL for the remote engine; it is not a local execution catalog.

## Public API (overview)

| Symbol | Role |
|--------|------|
| `Session.connect(...)` | Short constructor using env + optional overrides (always coordinator-attached). |
| `Session.builder()` / `SessionBuilder` | Fluent configuration. |
| `session.catalog` | Logical table registry (metadata for SQL generation; engine resolves paths and credentials). |
| `session.sql(query)` | `POST /v1/sql` on coordinator; decodes **Arrow IPC stream** or JSON tabular payload to `pyarrow.Table`. |
| `session.ping()` | `GET /` (or health) — returns `True` on HTTP 2xx. |
| `session.start()` | Eager `POST /v1/sessions`. |
| `session.stop()` | Best-effort `POST /v1/sessions/{id}/close`. |
| `session.config()` | Redacted mapping for logging/tests. |
| `session.version()` | `scorpio_python_api` package version plus optional `GET /v1/version` body. |
| `session.verify_scheduler_reachable()` | gRPC channel readiness to `SCORPIO_SCHEDULER_HOST:SCORPIO_SCHEDULER_PORT` (TCP / protocol handshake only; RPC stubs live under `docs/grpc-codegen.md`). |
| `session.run_dataframe(df)` | Run a lazy Epic 2 `scorpio.dataframe.DataFrame` (compiled SQL → same `sql()` path). |

## Coordinator REST contract (MVP)

Until the real coordinator ships, the Compose stack may still use `hashicorp/http-echo` for port **8080** (`deploy/docker-compose/docker-compose.scorpio-stack.yml`). Scorpio's Python API expects the following routes when you run against a real API:

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

See also [docs/deployment.md](deployment.md) for Compose ports and image wiring, and [docs/python-dataframe.md](python-dataframe.md) for the Epic 2 lazy DataFrame API built on this session.

## Distributed SQL acceptance

Phase 1 acceptance calls for **Scorpio's Python API** to drive a **distributed** SQL path (executor participation). Today:

- The **Rust** `scorpio` client exercises the full DataFusion / Ballista scheduler path (see `engine/README.md`).
- **Python** implements the **coordinator HTTP contract** and Arrow/JSON decoding so a future API (Epic 8) can front the same engine without redesign.
- Opt-in integration: run Compose with a coordinator implementing the routes above, export `SCORPIO_INTEGRATION=1`, and run `pytest` from `python/scorpio/` (see `tests/test_session_http_roundtrip.py` marker `integration`).

## Tests

From `python/scorpio/` after `pip install -e ".[dev]"`:

```bash
pytest
```

CI: `.github/workflows/scorpio-python.yml`.
