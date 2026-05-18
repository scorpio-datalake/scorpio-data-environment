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

import unittest.mock

from scorpio import Session, SessionBuilder


def test_session_builder_chain() -> None:
    import os

    with unittest.mock.patch.dict(
        os.environ,
        {"SCORPIO_COORDINATOR_URL": "http://example.invalid:9"},
        clear=False,
    ):
        s = (
            SessionBuilder.from_env()
            .coordinator_url("http://127.0.0.1:18080")
            .tenant_id("org-1")
            .max_retries(2)
            .build()
        )
        cfg = dict(s.config())
        assert cfg["coordinator_url"] == "http://127.0.0.1:18080"
        assert cfg["tenant_id"] == "org-1"
        assert cfg["max_retries"] == 2


def test_session_builder_defaults_from_env_when_empty() -> None:
    s = Session.builder().build()
    assert "coordinator_url" in dict(s.config())
