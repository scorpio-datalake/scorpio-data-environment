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

import pyarrow as pa
import pytest

from scorpio import AggExpr, DataFrame
from scorpio.dataframe.frame import _arrow_table_to_fixed_width_string
from scorpio.dataframe.plan import LogicalPlan, SourceTable
from scorpio.dataframe.sql import logical_plan_to_sql
from scorpio.exceptions import ScorpioPlanError


def test_to_sql_select_filter_limit() -> None:
    df = (
        DataFrame.from_table("orders")
        .select("id", "amt")
        .filter("amt > 0")
        .limit(10)
    )
    sql = df.to_sql()
    assert '"orders"' in sql and "WHERE" in sql and "LIMIT 10" in sql
    assert "amt > 0" in sql


def test_repartition_coalesce_in_sql_comment() -> None:
    df = DataFrame.from_table("t").repartition(8).coalesce(2).limit(1)
    sql = df.to_sql()
    assert "repartition(8)" in sql and "coalesce(2)" in sql


def test_group_by_agg_sql() -> None:
    df = DataFrame.from_table("sales").group_by("region").agg(
        AggExpr("sum", "amt", alias="total_amt"),
        AggExpr("count", "id", alias="n_orders"),
    )
    sql = df.to_sql()
    assert "GROUP BY" in sql and "SUM" in sql and "COUNT" in sql


def test_write_sink_rejected_in_to_sql() -> None:
    df = DataFrame.from_table("t").write_parquet("/tmp/out.parquet")
    with pytest.raises(ScorpioPlanError):
        df.to_sql()


def test_window_rejected_in_to_sql() -> None:
    df = DataFrame.from_table("t").window("ROW_NUMBER() OVER (PARTITION BY a)")
    with pytest.raises(ScorpioPlanError):
        df.to_sql()


def test_explain_contains_scan() -> None:
    plan = LogicalPlan(SourceTable("x"))
    text = DataFrame(plan).explain()
    assert "TableScan" in text and "x" in text


def test_join_generates_on_clause() -> None:
    sql = DataFrame.from_table("orders").join("customers", "customer_id", how="inner").to_sql()
    assert "JOIN" in sql and "ON" in sql and "customer_id" in sql


def test_arrow_table_format_header_and_rows() -> None:
    tbl = pa.table({"a": [1, 2], "b": ["x", "y"]})
    s = _arrow_table_to_fixed_width_string(tbl, 10)
    assert "a" in s and "b" in s and "1" in s and "x" in s


def test_arrow_table_format_truncation_footer() -> None:
    tbl = pa.table({"n": list(range(5))})
    s = _arrow_table_to_fixed_width_string(tbl, max_rows=2)
    assert "more rows" in s


def test_arrow_table_format_empty_schema() -> None:
    tbl = pa.table({})
    assert _arrow_table_to_fixed_width_string(tbl, 5) == "(empty schema)"
