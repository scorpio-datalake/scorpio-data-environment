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

"""Epic 3 — OpenAPI JSON contract is loadable and defines job + session paths."""

from __future__ import annotations

import json
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_openapi_coordinator_v1_json_loads() -> None:
    path = _repo_root() / "docs" / "openapi" / "coordinator-v1.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["openapi"].startswith("3.")
    paths = data["paths"]
    for key in (
        "/v1/sessions",
        "/v1/sql",
        "/v1/jobs",
        "/v1/jobs/{job_id}",
        "/v1/jobs/{job_id}/cancel",
        "/v1/jobs/{job_id}/result",
    ):
        assert key in paths, f"missing path {key}"
