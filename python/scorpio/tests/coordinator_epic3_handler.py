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

"""Threading HTTP handler implementing Epic 3 coordinator routes (+ Epic 1/2 MVP)."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

import pyarrow as pa


class Epic3ThreadingHTTPServer(ThreadingHTTPServer):
    """Raised TCP listen backlog for burst concurrent clients (stub tests)."""

    request_queue_size = 256


def _arrow_ipc_table_slice(values: list[int], *, offset: int, limit: int) -> bytes:
    slice_vals = values[offset : offset + limit]
    tbl = pa.table({"v": pa.array(slice_vals, type=pa.int64())})
    sink = pa.BufferOutputStream()
    writer = pa.ipc.new_stream(sink, tbl.schema)
    try:
        writer.write_table(tbl)
    finally:
        writer.close()
    return sink.getvalue().to_pybytes()


def build_epic3_handler(
    *,
    expected_tenant: str | None = None,
    full_result_rows: list[int] | None = None,
    capture_submits: dict[str, Any] | None = None,
) -> type[BaseHTTPRequestHandler]:
    """Return a ``BaseHTTPRequestHandler`` subclass with in-memory job store."""
    rows_default = [0, 1, 2, 3, 4]
    full_rows = full_result_rows if full_result_rows is not None else rows_default
    state: dict[str, Any] = {
        "jobs": {},
        "counter": 0,
        "counter_lock": threading.Lock(),
        "expected_tenant": expected_tenant,
        "full_rows": full_rows,
        "capture_submits": capture_submits,
        "python_udfs": {},
    }

    class Epic3CoordinatorHandler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: object) -> None:  # noqa: A003
            return

        def _tenant_ok(self) -> bool:
            exp = state["expected_tenant"]
            if exp is None:
                return True
            if self.headers.get("X-Scorpio-Tenant-Id") != exp:
                self.send_response(400)
                self.end_headers()
                return False
            return True

        def _advance_job_status(self, job: dict[str, Any]) -> str:
            if job.get("cancelled"):
                return "CANCELLED"
            if "SQL_ERROR" in job["sql"]:
                job["error"] = "injected SQL_ERROR"
                return "FAILED"
            job["polls"] = job.get("polls", 0) + 1
            if "__SCORPIO_SLOW_JOB__" in job["sql"]:
                if job["polls"] < 3:
                    return "RUNNING"
                return "SUCCEEDED"
            if job["polls"] < 2:
                return "RUNNING"
            return "SUCCEEDED"

        def do_GET(self) -> None:  # noqa: N802
            if not self._tenant_ok():
                return
            parsed = urlparse(self.path)
            path = parsed.path
            qs = parse_qs(parsed.query)
            if path in ("/", "/health"):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"ok")
                return
            if path == "/v1/version":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"version":"epic3-stub"}')
                return
            if path.startswith("/v1/jobs/") and path.endswith("/result"):
                job_id = path.split("/")[3]
                if not qs.get("session_id"):
                    self.send_response(400)
                    self.end_headers()
                    return
                job = state["jobs"].get(job_id)
                if not job:
                    self.send_response(404)
                    self.end_headers()
                    return
                # Result pages do not advance lifecycle (poll ``GET /v1/jobs/{{id}}`` first).
                st = job["status"]
                if st != "SUCCEEDED":
                    self.send_response(409)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(b'{"error":"job_not_complete","code":"409"}')
                    return
                offset = int(qs.get("offset", ["0"])[0])
                limit = int(qs.get("limit", ["65536"])[0])
                full = state["full_rows"]
                slice_vals = full[offset : offset + limit]
                slice_len = len(slice_vals)
                next_offset = offset + slice_len
                has_more = next_offset < len(full)
                raw = _arrow_ipc_table_slice(full, offset=offset, limit=limit)
                self.send_response(200)
                self.send_header("Content-Type", "application/vnd.apache.arrow.stream")
                self.send_header("X-Scorpio-Has-More", "1" if has_more else "0")
                self.send_header("X-Scorpio-Next-Offset", str(next_offset))
                self.end_headers()
                self.wfile.write(raw)
                return
            if path.startswith("/v1/jobs/") and path.count("/") == 3:
                job_id = path.split("/")[-1]
                job = state["jobs"].get(job_id)
                if not job:
                    self.send_response(404)
                    self.end_headers()
                    return
                st = self._advance_job_status(job)
                job["status"] = st
                body = {
                    "job_id": job_id,
                    "session_id": job["session_id"],
                    "status": st,
                    "error": job.get("error"),
                }
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(body).encode("utf-8"))
                return
            self.send_response(404)
            self.end_headers()

        def do_POST(self) -> None:  # noqa: N802
            if not self._tenant_ok():
                return
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length else b""
            try:
                payload = json.loads(raw.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                payload = {}
            path = urlparse(self.path).path
            if path == "/v1/sessions":
                self.send_response(201)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"session_id":"stub-session"}')
                return
            if path == "/v1/sql":
                sql = str(payload.get("sql", ""))
                if "SQL_ERROR" in sql:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(b'{"error":"sql_failed"}')
                    return
                tbl = pa.table({"n": pa.array([42], type=pa.int32())})
                sink = pa.BufferOutputStream()
                writer = pa.ipc.new_stream(sink, tbl.schema)
                try:
                    writer.write_table(tbl)
                finally:
                    writer.close()
                self.send_response(200)
                self.send_header("Content-Type", "application/vnd.apache.arrow.stream")
                self.end_headers()
                self.wfile.write(sink.getvalue().to_pybytes())
                return
            if path == "/v1/jobs":
                cap = state.get("capture_submits")
                if isinstance(cap, dict):
                    cap["last_submit"] = dict(payload)
                sid = str(payload.get("session_id", ""))
                sql = str(payload.get("sql", ""))
                with state["counter_lock"]:
                    state["counter"] += 1
                    job_id = f"j-{state['counter']}"
                    state["jobs"][job_id] = {
                        "session_id": sid,
                        "sql": sql,
                        "status": "QUEUED",
                        "polls": 0,
                        "cancelled": False,
                        "error": None,
                    }
                self.send_response(202)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(
                    json.dumps({"job_id": job_id, "status": "QUEUED"}).encode("utf-8")
                )
                return
            if "/v1/jobs/" in path and path.endswith("/cancel"):
                job_id = path.split("/")[3]
                job = state["jobs"].get(job_id)
                if not job:
                    self.send_response(404)
                    self.end_headers()
                    return
                job["cancelled"] = True
                job["status"] = "CANCELLED"
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True, "status": "CANCELLED"}).encode("utf-8"))
                return
            if path.startswith("/v1/sessions/") and path.endswith("/close"):
                self.send_response(204)
                self.end_headers()
                return
            # `/v1/sessions/{session_id}/python-udfs` → ['v1','sessions',session_id,'python-udfs'] (length 4)
            parts = path.strip("/").split("/")
            if (
                len(parts) == 4
                and parts[0] == "v1"
                and parts[1] == "sessions"
                and parts[3] == "python-udfs"
            ):
                sess = parts[2]
                udf_name = str(payload.get("name", "")).strip()
                udf_src = str(payload.get("source", ""))
                ret_type = str(payload.get("return_arrow_type", "float64") or "float64").strip()
                if not udf_name or not udf_src.strip():
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(b'{"error":"invalid_python_udf","code":"400"}')
                    return
                per_session = state["python_udfs"].setdefault(sess, {})
                per_session[udf_name] = {
                    "source": udf_src,
                    "return_arrow_type": ret_type,
                }
                self.send_response(201)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(
                    json.dumps(
                        {"name": udf_name, "registered": True, "session_id": sess},
                    ).encode("utf-8")
                )
                return
            self.send_response(404)
            self.end_headers()

    return Epic3CoordinatorHandler
