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

"""Minimal REST client for Scorpio's Python API (``scorpio-python-api``) → coordinator (Epic 8 contract, MVP)."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping, MutableMapping
from urllib.parse import quote, urlencode, urljoin

from scorpio.config import SessionConfig
from scorpio.exceptions import ScorpioConnectionError, ScorpioCoordinatorError, ScorpioJobError
from scorpio.python_api_meta import SCORPIO_PYTHON_API_ID


@dataclass(frozen=True)
class HttpResponse:
    """Raw HTTP response from the coordinator."""

    status: int
    body: bytes
    content_type: str | None


class CoordinatorClient:
    """HTTP/JSON + Arrow IPC helper aligned with ``docs/python-session.md``."""

    def __init__(self, config: SessionConfig) -> None:
        self._config = config
        base = config.coordinator_url.rstrip("/") + "/"
        self._base = base

    def _headers(self, extra: Mapping[str, str] | None = None) -> dict[str, str]:
        from scorpio import __version__ as _package_version

        h: dict[str, str] = {"User-Agent": f"{SCORPIO_PYTHON_API_ID}/{_package_version}"}
        if self._config.auth_bearer_token:
            h["Authorization"] = f"Bearer {self._config.auth_bearer_token}"
        if self._config.tenant_id:
            h["X-Scorpio-Tenant-Id"] = self._config.tenant_id
        if extra:
            h.update(dict(extra))
        return h

    def request(
        self,
        method: str,
        path: str,
        *,
        body: bytes | None = None,
        json_body: Any | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> HttpResponse:
        """Perform an HTTP request with retries on connection errors and HTTP 503."""
        url = urljoin(self._base, path.lstrip("/"))
        data = body
        hdrs: MutableMapping[str, str] = self._headers(headers)
        if json_body is not None:
            data = json.dumps(json_body).encode("utf-8")
            hdrs.setdefault("Content-Type", "application/json")

        last_err: Exception | None = None
        for attempt in range(max(1, self._config.max_retries)):
            req = urllib.request.Request(url, data=data, method=method, headers=dict(hdrs))
            try:
                with urllib.request.urlopen(
                    req,
                    timeout=self._config.request_timeout_sec,
                ) as resp:
                    raw = resp.read()
                    ctype = resp.headers.get("Content-Type")
                    return HttpResponse(status=resp.status, body=raw, content_type=ctype)
            except urllib.error.HTTPError as e:
                if e.code == 503 and attempt + 1 < self._config.max_retries:
                    time.sleep(self._config.retry_backoff_sec * (attempt + 1))
                    continue
                try:
                    raw = e.read()
                except Exception:
                    raw = b""
                raise ScorpioCoordinatorError(
                    f"HTTP {e.code} for {method} {url}: {raw[:512]!r}"
                ) from e
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                last_err = e
                if attempt + 1 < self._config.max_retries:
                    time.sleep(self._config.retry_backoff_sec * (attempt + 1))
                    continue
                raise ScorpioConnectionError(f"{method} {url} failed: {e}") from e

        raise ScorpioConnectionError(f"{method} {url} failed after retries: {last_err!r}")

    def health_get(self, path: str = "/") -> HttpResponse:
        """GET coordinator root or ``/health`` (MVP: any 2xx counts as reachable)."""
        return self.request("GET", path)

    def create_session(self) -> str:
        """POST ``/v1/sessions`` — returns server ``session_id`` (JSON)."""
        resp = self.request("POST", "/v1/sessions", json_body={"tenant_id": self._config.tenant_id})
        if resp.status not in (200, 201):
            raise ScorpioCoordinatorError(f"create_session: HTTP {resp.status}")
        payload = json.loads(resp.body.decode("utf-8"))
        sid = payload.get("session_id")
        if not isinstance(sid, str) or not sid:
            raise ScorpioCoordinatorError(f"create_session: missing session_id in {payload!r}")
        return sid

    def close_session(self, session_id: str) -> None:
        """POST ``/v1/sessions/{id}/close``."""
        self.request("POST", f"/v1/sessions/{session_id}/close", json_body={})

    def execute_sql_raw(self, session_id: str, sql: str) -> HttpResponse:
        """POST ``/v1/sql`` — response body is Arrow IPC stream or JSON error."""
        return self.request(
            "POST",
            "/v1/sql",
            json_body={"session_id": session_id, "sql": sql, "tenant_id": self._config.tenant_id},
        )

    def submit_job(self, session_id: str, sql: str) -> tuple[str, str]:
        """POST ``/v1/jobs`` — returns ``(job_id, status)`` per OpenAPI ``SubmitJobResponse``."""
        try:
            resp = self.request(
                "POST",
                "/v1/jobs",
                json_body={"session_id": session_id, "sql": sql, "tenant_id": self._config.tenant_id},
            )
        except ScorpioCoordinatorError as e:
            if "HTTP 404" in str(e):
                raise ScorpioJobError(
                    "POST /v1/jobs not implemented on this coordinator (HTTP 404); "
                    "use Session.sql() or DataFrame.collect() for synchronous SQL."
                ) from e
            raise
        if resp.status not in (200, 201, 202):
            raise ScorpioJobError(f"submit_job: HTTP {resp.status}: {resp.body[:512]!r}")
        payload = json.loads(resp.body.decode("utf-8"))
        job_id = payload.get("job_id")
        status = payload.get("status", "UNKNOWN")
        if not isinstance(job_id, str) or not job_id:
            raise ScorpioJobError(f"submit_job: missing job_id in {payload!r}")
        if not isinstance(status, str):
            raise ScorpioJobError(f"submit_job: bad status in {payload!r}")
        return job_id, status

    def get_job_status_payload(self, session_id: str, job_id: str) -> dict[str, Any]:
        """GET ``/v1/jobs/{job_id}?session_id=…`` — JSON ``JobStatusResponse``."""
        safe_sid = quote(session_id, safe="")
        safe_jid = quote(job_id, safe="")
        path = f"/v1/jobs/{safe_jid}?session_id={safe_sid}"
        resp = self.request("GET", path)
        if resp.status != 200:
            raise ScorpioJobError(f"get_job_status: HTTP {resp.status}: {resp.body[:512]!r}")
        out = json.loads(resp.body.decode("utf-8"))
        if not isinstance(out, dict):
            raise ScorpioJobError(f"get_job_status: expected JSON object, got {type(out)}")
        return out

    def cancel_job(self, session_id: str, job_id: str) -> dict[str, Any]:
        """POST ``/v1/jobs/{job_id}/cancel`` with JSON body ``{{\"session_id\"}}``."""
        safe_jid = quote(job_id, safe="")
        resp = self.request(
            "POST",
            f"/v1/jobs/{safe_jid}/cancel",
            json_body={"session_id": session_id},
        )
        if resp.status not in (200, 204):
            raise ScorpioJobError(f"cancel_job: HTTP {resp.status}: {resp.body[:512]!r}")
        if resp.status == 204 or not resp.body.strip():
            return {"ok": True, "status": "CANCELLED"}
        out = json.loads(resp.body.decode("utf-8"))
        if not isinstance(out, dict):
            raise ScorpioJobError(f"cancel_job: expected JSON object, got {type(out)}")
        return out

    def fetch_job_result_page_raw(
        self,
        session_id: str,
        job_id: str,
        *,
        offset: int = 0,
        limit: int = 65_536,
    ) -> HttpResponse:
        """GET ``/v1/jobs/{job_id}/result`` — one Arrow IPC stream page (Epic 3 pagination)."""
        if offset < 0 or limit < 1:
            raise ValueError("offset must be >= 0 and limit >= 1")
        safe_jid = quote(job_id, safe="")
        q = urlencode({"session_id": session_id, "offset": offset, "limit": limit})
        return self.request("GET", f"/v1/jobs/{safe_jid}/result?{q}")
