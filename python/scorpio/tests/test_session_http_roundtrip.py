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

"""In-process HTTP server exercises coordinator REST contract (no Docker)."""

from __future__ import annotations

import os
import threading
import unittest.mock
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pyarrow as pa
import pytest

from scorpio import Session


def _arrow_ipc_single_int_table(value: int = 42) -> bytes:
    tbl = pa.table({"n": pa.array([value], type=pa.int32())})
    sink = pa.BufferOutputStream()
    writer = pa.ipc.new_stream(sink, tbl.schema)
    try:
        writer.write_table(tbl)
    finally:
        writer.close()
    return sink.getvalue().to_pybytes()


class _ArrowHandler(BaseHTTPRequestHandler):
    expected_tenant: str | None = None

    def log_message(self, fmt: str, *args: object) -> None:  # noqa: A003
        return

    def do_GET(self) -> None:  # noqa: N802
        if self.path in ("/", "/health"):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        elif self.path == "/v1/version":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"version":"mock-coordinator"}')
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        _ = self.rfile.read(length) if length else b""
        tenant_hdr = self.headers.get("X-Scorpio-Tenant-Id")
        if self.expected_tenant is not None and tenant_hdr != self.expected_tenant:
            self.send_response(400)
            self.end_headers()
            return
        if self.path == "/v1/sessions":
            self.send_response(201)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"session_id":"s-integration"}')
        elif self.path == "/v1/sql":
            raw = _arrow_ipc_single_int_table(99)
            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.apache.arrow.stream")
            self.end_headers()
            self.wfile.write(raw)
        elif self.path.startswith("/v1/sessions/") and self.path.endswith("/close"):
            self.send_response(204)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()


class _JsonSqlHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:  # noqa: A003
        return

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        _ = self.rfile.read(length) if length else b""
        if self.path == "/v1/sessions":
            self.send_response(201)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"session_id":"j1"}')
        elif self.path == "/v1/sql":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"columns":["x"],"rows":[[7]]}')
        elif self.path.startswith("/v1/sessions/") and self.path.endswith("/close"):
            self.send_response(204)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()


def _serve(handler_cls: type[BaseHTTPRequestHandler]) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def test_session_sql_arrow_roundtrip() -> None:
    _ArrowHandler.expected_tenant = "tenant-a"
    server = _serve(_ArrowHandler)
    try:
        port = server.server_address[1]
        url = f"http://127.0.0.1:{port}"
        env = {
            "SCORPIO_COORDINATOR_URL": url,
            "SCORPIO_TENANT_ID": "tenant-a",
            "SCORPIO_HTTP_RETRIES": "1",
        }
        with unittest.mock.patch.dict(os.environ, env, clear=False):
            session = Session.connect()
            assert session.ping() is True
            out = session.sql("SELECT 1")
            assert out.column("n")[0].as_py() == 99
            session.stop()
    finally:
        server.shutdown()


def test_coordinator_json_sql_result() -> None:
    server = _serve(_JsonSqlHandler)
    try:
        port = server.server_address[1]
        url = f"http://127.0.0.1:{port}"
        with unittest.mock.patch.dict(
            os.environ,
            {"SCORPIO_COORDINATOR_URL": url, "SCORPIO_HTTP_RETRIES": "1"},
            clear=False,
        ):
            session = Session.connect()
            out = session.sql("SELECT 1")
            assert out.column("x")[0].as_py() == 7
    finally:
        server.shutdown()


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("SCORPIO_INTEGRATION") != "1",
    reason="Set SCORPIO_INTEGRATION=1 with Compose coordinator (see docs/python-session.md)",
)
def test_live_compose_coordinator_ping() -> None:
    s = Session.connect()
    assert s.ping()
