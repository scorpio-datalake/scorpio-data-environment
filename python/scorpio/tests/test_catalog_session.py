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

"""Catalog metadata and ``Session`` wiring (Scorpio's Python API — no local engine)."""

import os
import unittest.mock

import pytest

from scorpio import Catalog, Session
from scorpio.exceptions import ScorpioConfigError


def test_catalog_register_list_standalone() -> None:
    c = Catalog()
    c.register_parquet("t", "/tmp/x.parquet")
    assert c.list_tables() == ["t"]
    h = c.get_table("t")
    assert h.kind == "parquet" and h.location == "/tmp/x.parquet"
    c.unregister("t")
    assert c.list_tables() == []


def test_session_catalog_registers_without_sql() -> None:
    with unittest.mock.patch.dict(
        os.environ,
        {"SCORPIO_COORDINATOR_URL": "http://127.0.0.1:65501", "SCORPIO_HTTP_RETRIES": "1"},
        clear=False,
    ):
        s = Session.connect()
        s.catalog.register_parquet("t", "/data/x.parquet")
        assert s.catalog.list_tables() == ["t"]


def test_session_config_view() -> None:
    with unittest.mock.patch.dict(
        os.environ,
        {
            "SCORPIO_COORDINATOR_URL": "http://127.0.0.1:9",
            "SCORPIO_TENANT_ID": "acme",
        },
        clear=False,
    ):
        s = Session.connect()
        cfg = dict(s.config())
        assert cfg["tenant_id"] == "acme"
        assert "local_only" not in cfg


def test_verify_scheduler_requires_endpoint() -> None:
    with unittest.mock.patch.dict(
        os.environ,
        {"SCORPIO_COORDINATOR_URL": "http://127.0.0.1:9"},
        clear=False,
    ):
        s = Session.connect()
        with pytest.raises(ScorpioConfigError):
            s.verify_scheduler_reachable()
