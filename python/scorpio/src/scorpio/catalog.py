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

"""Logical table names and paths attached to **Scorpio's Python API** ``Session`` for remote SQL.

Registrations are **metadata only in Python** (they become identifiers in SQL sent to the Rust
coordinator/engine); they are not scans or compute in Python. Lake scope is documented in the
monorepo — see ``docs/data-sources-databases-sftp.md`` and ``docs/table-formats-metastore-scope.md``.
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
    """Logical table registry attached to a :class:`scorpio.session.Session` (Scorpio's Python API).

    Entries are **names and URIs used in generated SQL** for the remote Rust engine; Python does
    not read datasets here. Pushing catalog state through coordinator APIs is deferred to later
    epics. Names align with a future metastore / table-format story (Iceberg, Delta, Hive) without
    claiming support here.
    """

    def __init__(self) -> None:
        self._lock = RLock()
        self._tables: dict[str, TableHandle] = {}

    def register_parquet(self, name: str, path: str) -> None:
        """Register a Parquet path/URI under ``name`` for SQL sent to the remote engine."""
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
