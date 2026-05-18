# Databases, SFTP, and Scorpio — strategy (Phase 1)

Scorpio’s distributed engine is strongest when inputs are **object-store–backed columnar files** (Parquet, CSV, JSON) registered in the session catalog. **PostgreSQL, MySQL, Oracle, SFTP, and similar** sources are **not** first-class remote `TableProvider`s the way `s3://` tables are.

This document records the **approved strategies** and a **lightweight spike** you can run without committing secrets to the repo.

---

## Option A — ELT to Parquet (recommended default)

**Pattern:** Land data in the **lake** (S3 / GCS / ADLS) as **Parquet** (partitioned when useful) using your existing ingestion stack (Airbyte, Fivetran, dbt, custom batch jobs, `COPY … TO`, Spark, etc.), then register paths in Scorpio.

| Pros | Cons |
|------|------|
| Predictable performance; executor-local object-store reads align with the engine | Extra pipeline step; not “live” RDBMS |
| Simple security (storage IAM) shared with the rest of Phase 1 | Freshness bounded by ingest schedule |

**When to choose:** Default for Phase 1 product work unless you have a hard requirement for federated RDBMS reads.

---

## Option B — Custom `TableProvider` (engine extension)

**Pattern:** Implement a DataFusion [`TableProvider`](https://docs.rs/datafusion/latest/datafusion/catalog/trait.TableProvider.html) (and supporting `ExecutionPlan`) that streams JDBC/ODBC or native protocol rows into **Arrow** batches, register it in `SessionContext` / catalog paths you control.

| Pros | Cons |
|------|------|
| Query-in-place against operational DBs | Network and DB load on every scan; harder to push predicates unless you invest heavily |
| Fits specialized connectors | Must serialize custom nodes through the distributed engine if used in distributed plans (see compatibility doc) |

**When to choose:** Small number of high-value sources, team owns Rust connector maintenance, and latency/cost to the database is acceptable.

---

## Option C — Federation / external query engine

**Pattern:** Keep heavy federation in **Trino / Presto / BigQuery / Snowflake** etc.; Scorpio reads their **exported** results or a narrow integration (e.g. Parquet export to the lake).

| Pros | Cons |
|------|------|
| Reuses mature federation | Another system to operate; not “pure Scorpio SQL” over arbitrary JDBC |

**When to choose:** Organization already standardizes on an external SQL federation tier.

---

## SFTP

Treat SFTP like **files at rest**: sync objects to the lake (Option A) with a scheduled pull (e.g. `lftp`, dedicated ingest service). Running SFTP inside the scheduler/executor hot path is usually a poor fit for distributed SQL.

---

## Phase 1 recommendation

1. **Ship** object-store tables + ELT/EL to Parquet as the supported path ([object-store-credentials.md](object-store-credentials.md)).
2. **Track** a custom `TableProvider` or upstream DataFusion connector work as a **follow-up epic** if a product requirement mandates live Postgres reads.
3. **Document** any chosen connector in the engine README and compatibility notes when code lands.

---

## Optional spike: Postgres → Parquet (no engine change)

**Purpose:** Validate connectivity and file layout before Epic 2 reads the dataset from `s3://` / local disk.

Prerequisites: network path from the machine running the script to Postgres; credentials via env (for example `PGPASSWORD` or a `DATABASE_URL` you export in the shell), not committed in repo source.

**Python (illustrative):** use `sqlalchemy` or `psycopg` to `SELECT *` in chunks, build a `pyarrow.Table`, then `pyarrow.parquet.write_table` to a file (or stream to object storage with the object-store SDK). **Polars** `read_database` + `write_parquet` is a concise alternative. The spike outcome is a **Parquet file** you register against Scorpio like any other lake path.

---

## Related

- [scorpio-engine-compatibility.md](scorpio-engine-compatibility.md) — serialization and distributed boundaries
- [table-formats-metastore-scope.md](table-formats-metastore-scope.md) — catalogs and table formats
