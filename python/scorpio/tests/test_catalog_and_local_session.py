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

import pytest

from scorpio import Session
from scorpio.exceptions import ScorpioConfigError, ScorpioNotImplementedError


def test_catalog_register_list() -> None:
    s = Session.local(tenant_id="t1")
    s.catalog.register_parquet("t", "/tmp/x.parquet")
    assert s.catalog.list_tables() == ["t"]
    h = s.catalog.get_table("t")
    assert h.kind == "parquet" and h.location == "/tmp/x.parquet"
    s.catalog.unregister("t")
    assert s.catalog.list_tables() == []


def test_local_session_sql_raises() -> None:
    s = Session.local()
    with pytest.raises(ScorpioNotImplementedError):
        s.sql("SELECT 1")


def test_local_session_config_view() -> None:
    s = Session.local(tenant_id="acme")
    cfg = dict(s.config())
    assert cfg["local_only"] is True
    assert cfg["tenant_id"] == "acme"


def test_verify_scheduler_requires_endpoint() -> None:
    s = Session.local()
    with pytest.raises(ScorpioConfigError):
        s.verify_scheduler_reachable()
