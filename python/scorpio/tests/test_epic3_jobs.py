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

"""Epic 3 — job submit/status/cancel/paged results against in-process coordinator stub."""

from __future__ import annotations

import os
import threading
import unittest.mock
from http.server import ThreadingHTTPServer

import pyarrow as pa
import pytest

from coordinator_epic3_handler import build_epic3_handler

from scorpio import DataFrame, Session
from scorpio.exceptions import ScorpioJobError


def _serve(handler_cls: type) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def test_epic3_submit_poll_result_roundtrip() -> None:
    h = build_epic3_handler()
    server = _serve(h)
    try:
        port = server.server_address[1]
        url = f"http://127.0.0.1:{port}"
        with unittest.mock.patch.dict(
            os.environ,
            {"SCORPIO_COORDINATOR_URL": url, "SCORPIO_HTTP_RETRIES": "1"},
            clear=False,
        ):
            session = Session.connect()
            handle = session.submit_sql("SELECT 1")
            assert handle.job_id.startswith("j-")
            assert handle.status(session) in ("PENDING", "RUNNING", "SUCCEEDED")
            tbl = handle.result_arrow(session)
            assert tbl.num_rows == 5
            assert list(tbl.column("v").to_pylist()) == [0, 1, 2, 3, 4]
    finally:
        server.shutdown()


def test_epic3_dataframe_submit_uses_same_path() -> None:
    h = build_epic3_handler()
    server = _serve(h)
    try:
        port = server.server_address[1]
        url = f"http://127.0.0.1:{port}"
        with unittest.mock.patch.dict(
            os.environ,
            {"SCORPIO_COORDINATOR_URL": url, "SCORPIO_HTTP_RETRIES": "1"},
            clear=False,
        ):
            session = Session.connect()
            df = DataFrame.from_table("t").select("a").limit(1)
            hnd = df.submit(session)
            out = hnd.result_arrow(session)
            assert out.num_rows == 5
    finally:
        server.shutdown()


def test_epic3_cancel_job() -> None:
    h = build_epic3_handler()
    server = _serve(h)
    try:
        port = server.server_address[1]
        url = f"http://127.0.0.1:{port}"
        with unittest.mock.patch.dict(
            os.environ,
            {"SCORPIO_COORDINATOR_URL": url, "SCORPIO_HTTP_RETRIES": "1"},
            clear=False,
        ):
            session = Session.connect()
            slow = session.submit_sql("SELECT __SCORPIO_SLOW_JOB__")
            assert slow.status(session) == "RUNNING"
            slow.cancel(session)
            assert slow.status(session) == "CANCELLED"
            with pytest.raises(ScorpioJobError, match="CANCELLED"):
                slow.result_arrow(session)
    finally:
        server.shutdown()


def test_epic3_job_failed_status() -> None:
    h = build_epic3_handler()
    server = _serve(h)
    try:
        port = server.server_address[1]
        url = f"http://127.0.0.1:{port}"
        with unittest.mock.patch.dict(
            os.environ,
            {"SCORPIO_COORDINATOR_URL": url, "SCORPIO_HTTP_RETRIES": "1"},
            clear=False,
        ):
            session = Session.connect()
            bad = session.submit_sql("SELECT SQL_ERROR")
            assert bad.status(session) == "FAILED"
            with pytest.raises(ScorpioJobError, match="FAILED"):
                bad.result_arrow(session)
    finally:
        server.shutdown()


def test_epic3_paginated_result_concat(monkeypatch: pytest.MonkeyPatch) -> None:
    import scorpio.dataframe.job as jobmod

    monkeypatch.setattr(jobmod, "_JOB_RESULT_PAGE_ROWS", 2)
    h = build_epic3_handler()
    server = _serve(h)
    try:
        port = server.server_address[1]
        url = f"http://127.0.0.1:{port}"
        with unittest.mock.patch.dict(
            os.environ,
            {"SCORPIO_COORDINATOR_URL": url, "SCORPIO_HTTP_RETRIES": "1"},
            clear=False,
        ):
            session = Session.connect()
            tbl = session.submit_sql("SELECT 1").result_arrow(session)
            assert tbl.num_rows == 5
            assert pa.types.is_int64(tbl.schema.field("v").type)
    finally:
        server.shutdown()


def test_epic3_coordinator_session_id_idempotent() -> None:
    h = build_epic3_handler()
    server = _serve(h)
    try:
        port = server.server_address[1]
        url = f"http://127.0.0.1:{port}"
        with unittest.mock.patch.dict(
            os.environ,
            {"SCORPIO_COORDINATOR_URL": url, "SCORPIO_HTTP_RETRIES": "1"},
            clear=False,
        ):
            session = Session.connect()
            a = session.coordinator_session_id()
            b = session.coordinator_session_id()
            assert a == b == "stub-session"
    finally:
        server.shutdown()
