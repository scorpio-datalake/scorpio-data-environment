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

"""Compile :class:`scorpio.dataframe.plan.LogicalPlan` to DataFusion-style SQL (MVP)."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from scorpio.exceptions import ScorpioPlanError

if TYPE_CHECKING:
    from scorpio.dataframe.plan import LogicalPlan

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def quote_ident(name: str) -> str:
    if not _IDENT.match(name):
        raise ScorpioPlanError(f"Invalid SQL identifier for MVP compiler: {name!r}")
    return f'"{name}"'


def logical_plan_to_sql(plan: LogicalPlan) -> str:
    """Return a single ``SELECT`` suitable for :meth:`scorpio.session.Session.sql`."""
    from scorpio.dataframe.plan import (
        Aggregate,
        Coalesce,
        Filter,
        Join,
        Limit,
        Repartition,
        Select,
        SourceScan,
        WindowSpec,
        WithColumn,
        WriteParquet,
    )

    if plan.transforms and isinstance(plan.transforms[-1], WriteParquet):
        raise ScorpioPlanError(
            "Plan ends in write sink; use deferred write execution (Epic 3), not to_sql()."
        )
    for t in plan.transforms:
        if isinstance(t, WindowSpec):
            raise ScorpioPlanError(
                "Window specs are explain-only in MVP; use session.sql() for raw window queries."
            )

    if isinstance(plan.source, SourceScan):
        raise ScorpioPlanError(
            "SourceScan must be registered on Session.catalog before SQL generation; "
            "use read_parquet/read_csv/read_json or catalog.register_*()."
        )

    left = quote_ident(plan.source.name)
    from_clause = f"{left} AS {left}"
    join_sql: list[str] = []
    filters: list[str] = []
    select_columns: tuple[str, ...] | None = None
    with_cols: list[str] = []
    agg_block: Aggregate | None = None
    limit_n: int | None = None
    hints: list[str] = []

    for t in plan.transforms:
        if isinstance(t, Select):
            if select_columns is not None:
                raise ScorpioPlanError("Multiple Select nodes are not supported in MVP.")
            select_columns = t.columns
        elif isinstance(t, Filter):
            filters.append(f"({t.expression})")
        elif isinstance(t, WithColumn):
            with_cols.append(f"{t.expression} AS {quote_ident(t.name)}")
        elif isinstance(t, Join):
            how_map = {
                "inner": "INNER",
                "left": "LEFT",
                "right": "RIGHT",
                "full": "FULL OUTER",
                "semi": "LEFT SEMI",
                "anti": "LEFT ANTI",
            }
            join_word = how_map.get(t.how, "INNER")
            other = quote_ident(t.other)
            conds = " AND ".join(
                f"{left}.{quote_ident(c)} = {other}.{quote_ident(c)}" for c in t.on
            )
            join_sql.append(f"{join_word} JOIN {other} AS {other} ON {conds}")
        elif isinstance(t, Aggregate):
            if agg_block is not None:
                raise ScorpioPlanError("Multiple Aggregate nodes are not supported in MVP.")
            agg_block = t
        elif isinstance(t, Repartition):
            hints.append(f"repartition({t.num_partitions})")
        elif isinstance(t, Coalesce):
            hints.append(f"coalesce({t.num_partitions})")
        elif isinstance(t, Limit):
            limit_n = t.n
        elif isinstance(t, WriteParquet):
            raise ScorpioPlanError("WriteParquet in mid-plan is not supported.")

    if agg_block is not None:
        parts: list[str] = []
        for expr in agg_block.aggs:
            col = quote_ident(expr.column)
            op = expr.op
            if op == "sum":
                inner = f"SUM({col})"
            elif op == "min":
                inner = f"MIN({col})"
            elif op == "max":
                inner = f"MAX({col})"
            elif op == "avg":
                inner = f"AVG({col})"
            elif op == "count":
                inner = f"COUNT({col})"
            elif op == "count_distinct":
                inner = f"COUNT(DISTINCT {col})"
            else:
                raise ScorpioPlanError(f"Unsupported aggregate op: {op}")
            alias = expr.alias or f"{op}_{expr.column}"
            parts.append(f"{inner} AS {quote_ident(alias)}")
        keys_sql = ", ".join(quote_ident(k) for k in agg_block.group.keys)
        proj = (keys_sql + ", " if keys_sql else "") + ", ".join(parts)
        group_sql = ", ".join(quote_ident(k) for k in agg_block.group.keys) if agg_block.group.keys else ""
    elif select_columns:
        proj = ", ".join(quote_ident(c) for c in select_columns)
        if with_cols:
            proj = proj + ", " + ", ".join(with_cols)
    else:
        star = f"{left}.*"
        if with_cols:
            proj = star + ", " + ", ".join(with_cols)
        else:
            proj = star

    out: list[str] = []
    if hints:
        out.append("/* scorpio: " + "; ".join(hints) + " */")
    out.append(f"SELECT {proj} FROM {from_clause}")
    out.extend(join_sql)
    if filters:
        out.append("WHERE " + " AND ".join(filters))
    if agg_block is not None and agg_block.group.keys:
        out.append("GROUP BY " + ", ".join(quote_ident(k) for k in agg_block.group.keys))
    if limit_n is not None:
        out.append(f"LIMIT {int(limit_n)}")
    return " ".join(out)


def logical_plan_to_count_sql(plan: LogicalPlan) -> str:
    inner = logical_plan_to_sql(plan)
    return f"SELECT COUNT(*) AS cnt FROM ({inner}) AS _scorpio_sub"
