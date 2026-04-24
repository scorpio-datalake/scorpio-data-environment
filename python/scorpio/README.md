# scorpio (Python client)

Editable install: `pip install -e python/scorpio` (see [python/README.md](../README.md)).

## Session API (Epic 1)

- **`Session.connect()`** / **`Session.builder()`** — coordinator REST (`SCORPIO_COORDINATOR_URL`, tenant, retries).
- **`Session.local()`** — in-process **`catalog`** only; `sql()` is not available until a coordinator is configured.
- **`session.sql(...)`** — `POST /v1/sql`; decodes Arrow IPC or JSON tabular responses.

Full contract, env vars, auth placeholders, and lake alignment: [docs/python-session.md](../../docs/python-session.md).

gRPC stubs → `src/scorpio/_grpc/` per [docs/grpc-codegen.md](../../docs/grpc-codegen.md).

## Tests

```bash
cd python/scorpio && pip install -e ".[dev]" && pytest
```

CI: `.github/workflows/scorpio-python.yml`.
