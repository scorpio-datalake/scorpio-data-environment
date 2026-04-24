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

"""Minimal REST client for the future Scorpio coordinator (Epic 8 API contract, MVP)."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping, MutableMapping
from urllib.parse import urljoin

from scorpio.config import SessionConfig
from scorpio.exceptions import ScorpioConnectionError, ScorpioCoordinatorError


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
        h: dict[str, str] = {"User-Agent": "scorpio-python/0.0.0"}
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
