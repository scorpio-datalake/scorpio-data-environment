# Scorpio's Python API (`scorpio` package)

Editable install: `pip install -e python/scorpio` (see [python/README.md](../README.md)).

This package is the **`scorpio-python-api`**: a **thin coordinator client** over the **Rust** Scorpio engine. It does **not** execute SQL or scans locally; all compute is remote (`POST /v1/sql` → engine).

## Session (Epic 1)

- **`Session.connect()`** / **`Session.builder()`** — coordinator REST (`SCORPIO_COORDINATOR_URL`, tenant, retries).
- **`session.sql(...)`** — `POST /v1/sql`; decodes Arrow IPC or JSON tabular responses.

Full contract, env vars, auth placeholders, and lake alignment: [docs/python-session.md](../../docs/python-session.md).

## Lazy DataFrame (Epic 2)

- **`read_parquet` / `read_csv` / `read_json`** — register on `session.catalog`, return **`DataFrame`**.
- **Transforms** — `select`, `filter`, `with_column`, `join`, `group_by`/`agg`, `repartition`, `coalesce`, `limit`; `collect` / `to_arrow` / `count` / `show` use **`Session.sql`** (results materialize as **Apache Arrow** only — no pandas/polars in this package).
- **`session.run_dataframe(df)`** — same as `df.collect(session)` via compiled SQL.

Details: [docs/python-dataframe.md](../../docs/python-dataframe.md). Example: [examples/python_dataframe_epic2.py](../../examples/python_dataframe_epic2.py).

## Stable client identifier

Use **`scorpio.SCORPIO_PYTHON_API_ID`** (value: `scorpio-python-api`) for logs, support, or custom headers if needed.

## License

The `scorpio` package is **Apache-2.0** (see repository [LICENSE](../../LICENSE), [NOTICE](../../NOTICE), and `NOTICE` in this directory). Engine execution targets **Apache DataFusion** / **Apache Ballista** lineage — keep upstream attribution when distributing.

gRPC stubs → `src/scorpio/_grpc/` per [docs/grpc-codegen.md](../../docs/grpc-codegen.md).

## Tests

```bash
cd python/scorpio && pip install -e ".[dev]" && pytest
```

CI: `.github/workflows/scorpio-python.yml`.
