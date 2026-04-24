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

"""Job handle for Epic 3 — coordinator ``/v1/jobs`` submit/status/cancel/paged Arrow results."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

import pyarrow as pa

from scorpio._rest.coordinator import HttpResponse
from scorpio.exceptions import ScorpioJobError

if TYPE_CHECKING:
    from scorpio.session import Session

_JOB_RESULT_PAGE_ROWS = 4096


def _table_from_job_result_response(resp: HttpResponse) -> pa.Table:
    """Decode one Arrow IPC page from ``GET /v1/jobs/…/result`` (same wire as ``/v1/sql``)."""
    if resp.status == 409:
        raise ScorpioJobError(
            "Job result not ready (HTTP 409 job_not_complete); wait until status is SUCCEEDED."
        )
    if resp.status != 200:
        raise ScorpioJobError(f"Job result HTTP {resp.status}: {resp.body[:512]!r}")
    try:
        with pa.ipc.open_stream(pa.py_buffer(resp.body)) as reader:
            return reader.read_all()
    except pa.ArrowInvalid:
        pass
    try:
        payload = json.loads(resp.body.decode("utf-8"))
    except json.JSONDecodeError as e:
        raise ScorpioJobError("Job result was not Arrow IPC or JSON table") from e
    if not isinstance(payload, dict):
        raise ScorpioJobError(f"Unexpected JSON for job result: {type(payload)}")
    columns = payload.get("columns")
    rows = payload.get("rows", payload.get("data"))
    if not isinstance(columns, list) or not isinstance(rows, list):
        raise ScorpioJobError(f"JSON job result must have columns and rows: {payload.keys()!r}")
    if not columns:
        return pa.table({})
    col_data: dict[str, list[object]] = {str(c): [] for c in columns}
    for row in rows:
        if not isinstance(row, (list, tuple)) or len(row) != len(columns):
            raise ScorpioJobError(f"Row shape mismatch vs columns {columns!r}: {row!r}")
        for name, cell in zip(columns, row):
            col_data[str(name)].append(cell)
    return pa.table(col_data)


@dataclass
class JobHandle:
    """Reference to a coordinator job (``POST /v1/jobs``); poll status and fetch paged Arrow."""

    job_id: str
    sql_text: str

    def status(self, session: Session) -> Literal[
        "PENDING", "RUNNING", "SUCCEEDED", "FAILED", "CANCELLED", "UNKNOWN"
    ]:
        """GET ``/v1/jobs/{job_id}`` — maps coordinator enums to a small stable set."""
        sid = session.coordinator_session_id()
        payload = session._client.get_job_status_payload(sid, self.job_id)
        raw = str(payload.get("status", "UNKNOWN")).upper()
        mapping: dict[str, Literal["PENDING", "RUNNING", "SUCCEEDED", "FAILED", "CANCELLED", "UNKNOWN"]] = {
            "QUEUED": "PENDING",
            "PENDING": "PENDING",
            "RUNNING": "RUNNING",
            "SUCCEEDED": "SUCCEEDED",
            "FAILED": "FAILED",
            "CANCELLED": "CANCELLED",
        }
        return mapping.get(raw, "UNKNOWN")

    def cancel(self, session: Session) -> None:
        """POST ``/v1/jobs/{job_id}/cancel``."""
        if self.job_id == "epic3-placeholder":
            raise ScorpioJobError("Cannot cancel placeholder job handle (use a real coordinator).")
        sid = session.coordinator_session_id()
        session._client.cancel_job(sid, self.job_id)

    def result_arrow(self, session: Session) -> pa.Table:
        """Materialize job output via paginated ``GET /v1/jobs/…/result``; falls back to ``sql`` for legacy placeholder."""
        if self.job_id == "epic3-placeholder":
            return session.sql(self.sql_text)
        for _ in range(200):
            st = self.status(session)
            if st == "SUCCEEDED":
                break
            if st in ("FAILED", "CANCELLED"):
                raise ScorpioJobError(f"Job ended with status {st!r} (no result rows).")
        else:
            raise ScorpioJobError("Timed out waiting for job SUCCEEDED (coordinator status poll).")
        sid = session.coordinator_session_id()
        offset = 0
        chunks: list[pa.Table] = []
        while True:
            resp = session._client.fetch_job_result_page_raw(
                sid, self.job_id, offset=offset, limit=_JOB_RESULT_PAGE_ROWS
            )
            tbl = _table_from_job_result_response(resp)
            if tbl.num_rows == 0:
                break
            chunks.append(tbl)
            offset += tbl.num_rows
            if tbl.num_rows < _JOB_RESULT_PAGE_ROWS:
                break
        if not chunks:
            return pa.table({})
        return pa.concat_tables(chunks)
