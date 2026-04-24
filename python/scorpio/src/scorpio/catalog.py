# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""Client-side catalog metadata for Phase 1 MVP (registration is local until coordinator sync lands).

Lake scope (databases, SFTP, Hive / Iceberg / Delta) is documented in the monorepo; this module
must stay consistent with those product paths—see ``docs/data-sources-databases-sftp.md`` and
``docs/table-formats-metastore-scope.md`` in the repository root.
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Literal


@dataclass(frozen=True)
class TableHandle:
    """Registered table reference (MVP: Parquet path or opaque URI)."""

    name: str
    kind: Literal["parquet", "uri"]
    location: str


class Catalog:
    """In-process table registry attached to a :class:`scorpio.session.Session`.

    Phase 1 keeps registration **client-side**; pushing catalog state to the distributed
    coordinator/engine is deferred to later epics. Names and hooks intentionally align with a
    future metastore / table-format story (Iceberg, Delta, Hive) without claiming support here.
    """

    def __init__(self) -> None:
        self._lock = RLock()
        self._tables: dict[str, TableHandle] = {}

    def register_parquet(self, name: str, path: str) -> None:
        """Register a Parquet dataset path under ``name`` (local metadata only in MVP)."""
        with self._lock:
            self._tables[name] = TableHandle(name=name, kind="parquet", location=path)

    def register_uri(self, name: str, uri: str) -> None:
        """Register an opaque storage URI (S3, GCS, ADLS, etc.) for future engine resolution."""
        with self._lock:
            self._tables[name] = TableHandle(name=name, kind="uri", location=uri)

    def get_table(self, name: str) -> TableHandle:
        """Return handle for ``name`` or raise ``KeyError``."""
        with self._lock:
            return self._tables[name]

    def list_tables(self) -> list[str]:
        """Sorted list of registered logical names."""
        with self._lock:
            return sorted(self._tables.keys())

    def unregister(self, name: str) -> None:
        """Remove a registration if present."""
        with self._lock:
            self._tables.pop(name, None)
