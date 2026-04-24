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

"""Regression: monorepo contains Scorpio engine workspace (Epic 0) for CI checkout."""

from __future__ import annotations

from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_engine_workspace_manifest_exists() -> None:
    cargo = _repo_root() / "engine" / "Cargo.toml"
    assert cargo.is_file(), "Epic 0 engine workspace expected at engine/Cargo.toml"


def test_engine_scorpio_client_crate_exists() -> None:
    lib = _repo_root() / "engine" / "scorpio" / "client" / "Cargo.toml"
    assert lib.is_file(), "Rust scorpio client crate expected at engine/scorpio/client/Cargo.toml"
