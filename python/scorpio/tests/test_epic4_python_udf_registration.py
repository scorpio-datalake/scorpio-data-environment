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

"""Epic 4 — register Python scalar UDF via coordinator REST (contract + in-proc handler)."""

from __future__ import annotations

import threading
from http.server import ThreadingHTTPServer

from coordinator_epic3_handler import build_epic3_handler

from scorpio.session import Session


def test_register_python_scalar_udf_roundtrip() -> None:
    handler = build_epic3_handler()
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        url = f"http://{host}:{port}"
        session = (
            Session.builder()
            .coordinator_url(url)
            .max_retries(1)
            .request_timeout_sec(5.0)
            .connect_timeout_sec(3.0)
            .build()
        )
        session.start()
        out = session.register_python_scalar_udf(
            "double_x",
            "def double_x(x: float) -> float:\n    return x * 2.0\n",
            return_arrow_type="float64",
        )
        assert out.get("registered") is True
        assert out.get("name") == "double_x"
        assert out.get("session_id")
    finally:
        server.shutdown()
        thread.join(timeout=5.0)
