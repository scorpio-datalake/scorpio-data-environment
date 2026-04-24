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

"""**Scorpio's Python API** (`scorpio-python-api`): thin coordinator client over the Rust Scorpio engine."""

from scorpio.catalog import Catalog, TableHandle
from scorpio.config import SessionConfig
from scorpio.python_api_meta import SCORPIO_PYTHON_API_ID
from scorpio.dataframe import AggExpr, DataFrame, JobHandle, read_csv, read_json, read_parquet
from scorpio.exceptions import (
    ScorpioConfigError,
    ScorpioConnectionError,
    ScorpioCoordinatorError,
    ScorpioError,
    ScorpioJobError,
    ScorpioNotImplementedError,
    ScorpioPlanError,
    ScorpioSqlError,
)
from scorpio.session import Session, SessionBuilder

__version__ = "0.0.0"

__all__ = [
    "AggExpr",
    "Catalog",
    "DataFrame",
    "JobHandle",
    "Session",
    "SessionBuilder",
    "SessionConfig",
    "TableHandle",
    "read_csv",
    "read_json",
    "read_parquet",
    "ScorpioConfigError",
    "ScorpioConnectionError",
    "ScorpioCoordinatorError",
    "ScorpioError",
    "ScorpioJobError",
    "ScorpioNotImplementedError",
    "ScorpioPlanError",
    "ScorpioSqlError",
    "SCORPIO_PYTHON_API_ID",
    "__version__",
]
