# Scorpio's Python API — lazy DataFrame (Epic 2)

The `scorpio.dataframe` module is part of **Scorpio's Python API** (`scorpio-python-api`): a **lazy**, partition-hint-aware **Scorpio `DataFrame`** (not a pandas/polars frame) that compiles to **DataFusion-style SQL** and runs **only** through `scorpio.session.Session` (coordinator REST → Rust Scorpio engine). There is **no** local query engine in Python.

**Distributed semantics:** partitions, scans, shuffles, and aggregations run on **scheduler/executors** like the Rust `scorpio` client—the Python object holds only a **logical plan** (driver). Lake data (e.g. `s3://`, `gs://`, Azure URIs, or future HDFS-compatible paths) is read by the **engine** after catalog registration, not by pulling whole datasets into the Python process.

**Results:** actions such as `collect` / `to_arrow` return **`pyarrow.Table`** (Arrow batches from the cluster). This package does not depend on pandas or polars.

It aligns with Epic 0 object-store paths by registering locations on the session catalog before SQL is generated.

## Relationship to Epic 0 / engine

- **Reads:** `read_parquet` / `read_csv` / `read_json` register a logical name on `Session.catalog`; the Scorpio **Rust** engine resolves credentials and formats per operator docs (not re-implemented in Python).
- **Execution:** `DataFrame.collect(session)` → `session.sql(df.to_sql())` — the same remote path as raw SQL once the coordinator fronts the engine.
- **Upstream lineage:** Execution semantics follow **Apache DataFusion** via Ballista/Scorpio engine code — see repository `NOTICE` and `LICENSE` for Apache 2.0 and Ballista/DataFusion attribution.

## `repartition` vs `coalesce` (MVP)

| API | Intent | MVP SQL behavior |
|-----|--------|------------------|
| `repartition(n)` | Increase shuffle partitions (wide dependency) | Emitted only as a leading SQL **comment** `/* scorpio: repartition(n) */` so operators can see intent; the engine does not yet interpret this hint from Python-generated SQL. |
| `coalesce(n)` | Reduce target partitions (narrow dependency) | Same: **comment hint** `/* scorpio: coalesce(n) */` only. |

Some batch engines implement `coalesce` without a full shuffle when reducing partitions; DataFusion/Ballista behavior is **engine-specific** — treat these hints as **documentation + future wire format** until Epic 3/8 define plan bytes or session options.

## Security note (MVP)

`filter()` and `with_column()` accept **raw SQL fragments**. They are intended for trusted builder code; do not pass end-user strings without validation or parameterization (future work).

## Job handles (Epic 3)

`DataFrame.submit(session)` returns a `scorpio.dataframe.job.JobHandle` carrying a snapshot SQL string. `JobHandle.result_arrow(session)` runs that SQL via the coordinator today; `status` / `cancel` are stubs until coordinator job APIs land.

## See also

- [docs/python-session.md](python-session.md) — session, env vars, REST routes.
- [docs/data-sources-databases-sftp.md](data-sources-databases-sftp.md), [docs/table-formats-metastore-scope.md](table-formats-metastore-scope.md) — lake scope (Epic 0).
