#!/usr/bin/env python3
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

"""Epic 2 sample: lazy DataFrame → SQL → Session (requires live coordinator for collect)."""

from __future__ import annotations

import os

from scorpio import AggExpr, Session, read_parquet


def main() -> None:
    # Use SCORPIO_* from the environment (see docs/python-session.md).
    session = Session.connect()
    path = os.environ.get("SCORPIO_EXAMPLE_PARQUET", "s3://bucket/path/to/file.parquet")
    df = (
        read_parquet(session, path, table_name="demo")
        .filter("id IS NOT NULL")
        .select("id", "name")
        .repartition(8)
        .limit(100)
    )
    print(df.explain())  # noqa: T201
    print(df.to_sql())  # noqa: T201
    # Distributed execution (executor-backed) once coordinator implements /v1/sql:
    # table = session.run_dataframe(df)
    # print(table.to_pandas())


if __name__ == "__main__":
    main()
