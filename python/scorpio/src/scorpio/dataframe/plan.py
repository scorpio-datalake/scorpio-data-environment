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

"""Logical plan nodes for the lazy :class:`scorpio.dataframe.DataFrame` (Epic 2 MVP)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Union


@dataclass(frozen=True)
class SourceTable:
    """Named table (must exist on :attr:`scorpio.session.Session.catalog` for ``collect``)."""

    name: str


@dataclass(frozen=True)
class SourceScan:
    """File or object-store URI before registration (Parquet / CSV / JSON)."""

    uri: str
    format: Literal["parquet", "csv", "json"]


@dataclass(frozen=True)
class Select:
    """Column projection; empty ``columns`` means ``*``."""

    columns: tuple[str, ...]


@dataclass(frozen=True)
class Filter:
    """SQL boolean expression (caller responsible for safe fragments in MVP)."""

    expression: str


@dataclass(frozen=True)
class WithColumn:
    """Add or replace column ``name`` using SQL ``expression``."""

    name: str
    expression: str


@dataclass(frozen=True)
class Join:
    """Equi-join to another registered table ``other`` on ``on`` (same column name both sides)."""

    other: str
    on: tuple[str, ...]
    how: Literal["inner", "left", "right", "full", "semi", "anti"] = "inner"


@dataclass(frozen=True)
class GroupByKeys:
    keys: tuple[str, ...]


@dataclass(frozen=True)
class AggExpr:
    op: Literal["sum", "min", "max", "avg", "count", "count_distinct"]
    column: str
    alias: str | None = None


@dataclass(frozen=True)
class Aggregate:
    group: GroupByKeys
    aggs: tuple[AggExpr, ...]


@dataclass(frozen=True)
class WindowSpec:
    """Opaque window expression for ``explain``; SQL generation raises until extended."""

    sql_fragment: str


@dataclass(frozen=True)
class Repartition:
    """Shuffle/partition hint (see docs/python-dataframe.md — not emitted as engine SQL in MVP)."""

    num_partitions: int


@dataclass(frozen=True)
class Coalesce:
    """Reduce partition count hint (see docs vs DataFusion/Ballista engine semantics)."""

    num_partitions: int


@dataclass(frozen=True)
class Limit:
    n: int


@dataclass(frozen=True)
class WriteParquet:
    """Deferred sink (execution via Epic 3 job API; ``to_sql`` rejects plans ending here)."""

    path: str


Transform = Union[
    Select,
    Filter,
    WithColumn,
    Join,
    Aggregate,
    WindowSpec,
    Repartition,
    Coalesce,
    Limit,
    WriteParquet,
]


@dataclass(frozen=True)
class LogicalPlan:
    """Ordered lazy plan: single source then transforms."""

    source: SourceTable | SourceScan
    transforms: tuple[Transform, ...] = ()
