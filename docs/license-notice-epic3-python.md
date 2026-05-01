# License / NOTICE — Epic 3 (plan wire + job lifecycle)

Epic 3 extends **Scorpio's Python API** job submission, status, cancel, and paged results over **REST** (`python/scorpio/src/scorpio/_rest/coordinator.py`, `python/scorpio/src/scorpio/dataframe/job.py`) plus contract tests. New and touched files use **Apache License 2.0** file headers consistent with the repo.

**Coordinator contract** is documented in **`docs/openapi/coordinator-v1.json`**; engine behavior remains **Apache DataFusion** / **Ballista** lineage (see root **`NOTICE`**).

**Scorpio project license:** Re-read [license-and-notice.txt](../license-and-notice.txt) before release; monorepo **`LICENSE`** and **`NOTICE`** remain authoritative for distribution.
