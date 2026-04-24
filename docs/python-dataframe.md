# Scorpio Python lazy DataFrame (Epic 2)

The `scorpio.dataframe` module provides a **lazy**, partition-hint-aware API that compiles to **DataFusion-style SQL** for execution through :class:`scorpio.session.Session` (Epic 1 coordinator REST → engine). It is designed to align with Epic 0 object-store paths (`s3://`, `gs://`, Azure-style URIs) by registering locations on the session catalog before SQL is generated.

## Relationship to Epic 0 / engine

- **Reads:** `read_parquet` / `read_csv` / `read_json` register a logical name on :attr:`scorpio.session.Session.catalog`; the Scorpio engine resolves credentials and formats per operator docs (not re-implemented in Python).
- **Execution:** `DataFrame.collect(session)` → `session.sql(df.to_sql())` so the same **distributed** path as raw SQL applies once the coordinator fronts the engine.
- **Upstream lineage:** The execution target is **Apache DataFusion** semantics via Ballista/Scorpio engine code — see repository `NOTICE` and `LICENSE` for Apache 2.0 and Ballista/DataFusion attribution.

## `repartition` vs `coalesce` (MVP)

| API | Intent | MVP SQL behavior |
|-----|--------|------------------|
| `repartition(n)` | Increase shuffle partitions (wide dependency) | Emitted only as a leading SQL **comment** `/* scorpio: repartition(n) */` so operators can see intent; the engine does not yet interpret this hint from Python-generated SQL. |
| `coalesce(n)` | Reduce target partitions (narrow dependency) | Same: **comment hint** `/* scorpio: coalesce(n) */` only. |

Spark’s `coalesce` avoids shuffle when reducing partitions; DataFusion/Ballista partition behavior is engine-specific — treat hints as **documentation + future wire format** until Epic 3/8 define plan bytes or session options.

## Security note (MVP)

`filter()` and `with_column()` accept **raw SQL fragments**. They are intended for trusted builder code; do not pass end-user strings without validation or parameterization (future work).

## Job handles (Epic 3)

`DataFrame.submit(session)` returns a :class:`scorpio.dataframe.job.JobHandle` carrying a snapshot SQL string. `JobHandle.result_arrow(session)` runs that SQL today; `status` / `cancel` are stubs until coordinator job APIs land.

## See also

- [docs/python-session.md](python-session.md) — session, env vars, REST routes.
- [docs/data-sources-databases-sftp.md](data-sources-databases-sftp.md), [docs/table-formats-metastore-scope.md](table-formats-metastore-scope.md) — lake scope (Epic 0).
