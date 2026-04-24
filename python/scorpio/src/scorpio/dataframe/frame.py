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

"""Lazy partition-aware DataFrame (Epic 2) — composes with :class:`scorpio.session.Session`."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import pandas as pd
import pyarrow as pa

from scorpio.dataframe.job import JobHandle
from scorpio.dataframe.plan import (
    AggExpr,
    Aggregate,
    Coalesce,
    Filter,
    GroupByKeys,
    Join,
    Limit,
    LogicalPlan,
    Repartition,
    Select,
    SourceScan,
    SourceTable,
    Transform,
    WindowSpec,
    WithColumn,
    WriteParquet,
)
from scorpio.dataframe.sql import logical_plan_to_count_sql, logical_plan_to_sql

if TYPE_CHECKING:
    from scorpio.session import Session


def _extend(plan: LogicalPlan, *nodes: Transform) -> LogicalPlan:
    return LogicalPlan(plan.source, plan.transforms + nodes)


class DataFrame:
    """Lazy relational plan; use :meth:`collect` with :class:`~scorpio.session.Session` for execution."""

    __slots__ = ("_plan",)

    def __init__(self, plan: LogicalPlan) -> None:
        self._plan = plan

    @property
    def plan(self) -> LogicalPlan:
        """Logical plan snapshot (immutable)."""
        return self._plan

    def select(self, *columns: str) -> DataFrame:
        if not columns:
            return self
        return DataFrame(_extend(self._plan, Select(columns=tuple(columns))))

    def filter(self, expression: str) -> DataFrame:
        """Filter rows; ``expression`` is SQL pasted into a ``WHERE`` clause (MVP — trusted input)."""
        return DataFrame(_extend(self._plan, Filter(expression=expression)))

    def with_column(self, name: str, expression: str) -> DataFrame:
        """Add/replace column using SQL ``expression``."""
        return DataFrame(_extend(self._plan, WithColumn(name=name, expression=expression)))

    def join(
        self,
        other: str,
        on: str | tuple[str, ...],
        *,
        how: Literal["inner", "left", "right", "full", "semi", "anti"] = "inner",
    ) -> DataFrame:
        """Equi-join to another **registered** logical table ``other`` (catalog name)."""
        keys = (on,) if isinstance(on, str) else tuple(on)
        return DataFrame(_extend(self._plan, Join(other=other, on=keys, how=how)))

    def group_by(self, *keys: str) -> "_GroupBy":
        return _GroupBy(self, keys)

    @classmethod
    def from_table(cls, name: str) -> DataFrame:
        """Reference an existing catalog table without a read_* helper."""
        return cls(LogicalPlan(SourceTable(name)))

    def repartition(self, num_partitions: int) -> DataFrame:
        """Partitioning hint (documented vs engine — see ``docs/python-dataframe.md``)."""
        if num_partitions < 1:
            raise ValueError("num_partitions must be >= 1")
        return DataFrame(_extend(self._plan, Repartition(num_partitions=num_partitions)))

    def coalesce(self, num_partitions: int) -> DataFrame:
        """Reduce partition-hint (see docs for semantics vs Spark ``coalesce`` / DataFusion)."""
        if num_partitions < 1:
            raise ValueError("num_partitions must be >= 1")
        return DataFrame(_extend(self._plan, Coalesce(num_partitions=num_partitions)))

    def limit(self, n: int) -> DataFrame:
        return DataFrame(_extend(self._plan, Limit(n=n)))

    def window(self, sql_fragment: str) -> DataFrame:
        """Attach an explain-only window description; SQL compilation raises until extended."""
        return DataFrame(_extend(self._plan, WindowSpec(sql_fragment=sql_fragment)))

    def write_parquet(self, path: str) -> DataFrame:
        """Deferred Parquet write (terminal sink — do not call ``to_sql``); Epic 3 executes writes."""
        return DataFrame(_extend(self._plan, WriteParquet(path=path)))

    def to_sql(self) -> str:
        """Compile to a DataFusion-style ``SELECT`` for :meth:`scorpio.session.Session.sql`."""
        return logical_plan_to_sql(self._plan)

    def explain(self, *, extended: bool = False) -> str:
        """Human-readable plan (``extended`` reserved for future costing / protobuf debug)."""
        lines = ["Scorpio.DataFrame (lazy)"]
        src = self._plan.source
        if isinstance(src, SourceTable):
            lines.append(f"  TableScan: {src.name}")
        else:
            lines.append(f"  Scan: format={src.format} uri={src.uri!r}")
        for i, t in enumerate(self._plan.transforms, 1):
            lines.append(f"  {i:02d}. {t!r}")
        if extended:
            lines.append("  (extended diagnostics not yet implemented)")
        return "\n".join(lines)

    def collect(self, session: Session) -> pa.Table:
        """Execute through coordinator REST using :meth:`scorpio.session.Session.sql`."""
        return session.sql(self.to_sql())

    def to_pandas(self, session: Session) -> pd.DataFrame:
        return self.collect(session).to_pandas()

    def to_arrow(self, session: Session) -> pa.Table:
        return self.collect(session)

    def count(self, session: Session) -> int:
        t = session.sql(logical_plan_to_count_sql(self._plan))
        return int(t.column(0)[0].as_py())

    def show(self, n: int = 20, *, session: Session) -> None:
        """Print up to ``n`` rows (runs ``LIMIT`` via coordinator)."""
        print(self.limit(n).collect(session).to_pandas().to_string(index=False)))  # noqa: T201

    def submit(self, session: Session) -> JobHandle:
        """Prepare job handle (Epic 3); executors invoked once coordinator fronts real jobs."""
        _ = session  # reserved for tenancy / session context on submit
        return JobHandle(job_id="epic3-placeholder", sql_text=self.to_sql())

    def __repr__(self) -> str:
        head = "DataFrame"
        if isinstance(self._plan.source, SourceTable):
            head += f"(table={self._plan.source.name!r}, transforms={len(self._plan.transforms)})"
        else:
            head += f"(scan={self._plan.source.format!r}, transforms={len(self._plan.transforms)})"
        return head


class _GroupBy:
    __slots__ = ("_df", "_keys")

    def __init__(self, df: DataFrame, keys: tuple[str, ...]) -> None:
        self._df = df
        self._keys = keys

    def agg(self, *aggs: AggExpr) -> DataFrame:
        if not aggs:
            raise ValueError("agg() requires at least one AggExpr")
        node = Aggregate(group=GroupByKeys(keys=self._keys), aggs=tuple(aggs))
        return DataFrame(_extend(self._df._plan, node))
