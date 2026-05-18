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

"""Read paths for lazy :class:`scorpio.dataframe.DataFrame` via **Scorpio's Python API** (registers URIs for remote engine).

Every path requires a :class:`scorpio.session.Session`; execution is always remote (Rust coordinator/engine).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from scorpio.dataframe.frame import DataFrame
from scorpio.dataframe.plan import LogicalPlan, SourceTable

if TYPE_CHECKING:
    from scorpio.session import Session


def read_parquet(session: Session, path: str, *, table_name: str = "scorpio_df_parquet") -> DataFrame:
    """Register ``path`` (local path or ``s3://`` / ``gs://`` / ``az://`` URI) and return a lazy DataFrame.

    Registration uses :meth:`scorpio.catalog.Catalog.register_parquet`; the engine resolves credentials
    per Epic 0 (see ``docs/object-store-credentials.md``).
    """
    session.catalog.register_parquet(table_name, path)
    return DataFrame(LogicalPlan(SourceTable(table_name)))


def read_csv(session: Session, path: str, *, table_name: str = "scorpio_df_csv") -> DataFrame:
    """Register a CSV path/URI on the session catalog (logical handle for engine-side scan)."""
    session.catalog.register_uri(table_name, path)
    return DataFrame(LogicalPlan(SourceTable(table_name)))


def read_json(session: Session, path: str, *, table_name: str = "scorpio_df_json") -> DataFrame:
    """Register a JSON path/URI on the session catalog (logical handle for engine-side scan)."""
    session.catalog.register_uri(table_name, path)
    return DataFrame(LogicalPlan(SourceTable(table_name)))
