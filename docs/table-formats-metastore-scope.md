# Hive Metastore, Iceberg, and Delta — Phase 1 scope

This document captures the **product/engine scope decision** for Phase 1 so work stays aligned with DataFusion and Ballista capabilities in-tree.

---

## Current baseline (Scorpio engine as imported)

- **File layouts:** CSV, JSON, Parquet (and similar) via DataFusion registration and object-store URLs (`s3://`, `gs://`, `abfs://`, …) through `CustomObjectStoreRegistry`.
- **Stock Ballista:** No requirement to ship a **Hive Thrift Metastore** client, **Iceberg** catalog, or **Delta Lake** reader as part of the minimal fork unless you explicitly add dependencies and catalog wiring.

---

## Scope decision (Phase 1)

| Area | Phase 1 stance | Rationale |
|------|----------------|-----------|
| **Hive Metastore** | **Out of scope** for MVP unless a customer contract requires it | Adds HMS connectivity, catalog sync, and security model; prefer explicit paths / future REST catalog |
| **Apache Iceberg** | **Out of scope** for MVP read path | DataFusion Iceberg support evolves quickly; pin and test deliberately in a later epic |
| **Delta Lake** | **Out of scope** for MVP read path | Same as Iceberg — optional `datafusion-delta` (or successor) integration is a tracked follow-up |

**Minimal read path in Phase 1:** **Parquet (and CSV/JSON) on object storage** with path-based registration. If you need **partition pruning** and **schema evolution**, prioritize **well-partitioned Parquet** and explicit `OPTIONS` / session config over table-format magic until an Iceberg/Delta epic is scheduled.

---

## When to re-open scope

Revisit this document when **any** of the following is true:

- Product requires **time travel** or **MERGE/DELETE** semantics at rest.
- Customers expect **Unity Catalog / Glue / HMS** as the system of record for table names.
- DataFusion + workspace dependencies add a **supported, pinned** Iceberg or Delta crate you are willing to test in **multi-executor** Ballista jobs.

---

## Minimal “read path story” for operators (today)

1. Store datasets as **Parquet** under a bucket prefix with a stable convention (`s3://lake/warehouse/db/table/...`).
2. Inject **credentials** per [object-store-credentials.md](object-store-credentials.md) on scheduler and executors.
3. Register tables in the client/session layer (Epic 1–2) or SQL DDL your stack exposes, pointing at those prefixes.

---

## Related

- [data-sources-databases-sftp.md](data-sources-databases-sftp.md)
- [scorpio-engine-compatibility.md](scorpio-engine-compatibility.md)
