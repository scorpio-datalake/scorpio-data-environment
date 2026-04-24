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

"""Scorpio's Python API — :class:`Session` over coordinator REST (thin wrapper; no local execution)."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, replace
from typing import Any, Mapping

import pyarrow as pa

from scorpio.catalog import Catalog
from scorpio.config import SessionConfig
from scorpio.exceptions import (
    ScorpioConfigError,
    ScorpioConnectionError,
    ScorpioCoordinatorError,
    ScorpioSqlError,
)
from scorpio._rest.coordinator import CoordinatorClient, HttpResponse

logger = logging.getLogger(__name__)


def _table_from_coordinator_response(resp: HttpResponse) -> pa.Table:
    """Decode Arrow IPC stream or a small JSON tabular payload."""
    if resp.status != 200:
        raise ScorpioSqlError(f"SQL HTTP {resp.status}: {resp.body[:512]!r}")

    try:
        with pa.ipc.open_stream(pa.py_buffer(resp.body)) as reader:
            return reader.read_all()
    except pa.ArrowInvalid:
        pass

    try:
        payload = json.loads(resp.body.decode("utf-8"))
    except json.JSONDecodeError as e:
        raise ScorpioSqlError(
            "Could not parse SQL result as Arrow IPC or JSON; "
            "see docs/python-session.md for response contract."
        ) from e
    return _table_from_json_payload(payload)


def _table_from_json_payload(payload: Any) -> pa.Table:
    if not isinstance(payload, dict):
        raise ScorpioSqlError(f"Unexpected JSON shape for SQL result: {type(payload)}")
    columns = payload.get("columns")
    rows = payload.get("rows", payload.get("data"))
    if not isinstance(columns, list) or not isinstance(rows, list):
        raise ScorpioSqlError(f"JSON SQL result must have columns and rows/data: {payload.keys()!r}")
    if not columns:
        return pa.table({})
    col_data: dict[str, list[Any]] = {str(c): [] for c in columns}
    for row in rows:
        if not isinstance(row, (list, tuple)) or len(row) != len(columns):
            raise ScorpioSqlError(f"Row shape mismatch vs columns {columns!r}: {row!r}")
        for name, cell in zip(columns, row):
            col_data[str(name)].append(cell)
    return pa.table(col_data)


@dataclass
class SessionBuilder:
    """Fluent builder for :class:`Session` (``Session.builder().coordinator_url(...).build()``)."""

    _config: SessionConfig | None = None

    @classmethod
    def from_env(cls) -> SessionBuilder:
        b = cls()
        b._config = SessionConfig.from_env()
        return b

    def coordinator_url(self, url: str) -> SessionBuilder:
        self._ensure()
        self._config = replace(self._config, coordinator_url=url)
        return self

    def tenant_id(self, tenant_id: str | None) -> SessionBuilder:
        self._ensure()
        self._config = replace(self._config, tenant_id=tenant_id)
        return self

    def scheduler_endpoint(self, host: str, grpc_port: int) -> SessionBuilder:
        """Record scheduler location for :meth:`Session.verify_scheduler_reachable`."""
        self._ensure()
        self._config = replace(self._config, scheduler_host=host, scheduler_grpc_port=grpc_port)
        return self

    def connect_timeout_sec(self, value: float) -> SessionBuilder:
        self._ensure()
        self._config = replace(self._config, connect_timeout_sec=value)
        return self

    def request_timeout_sec(self, value: float) -> SessionBuilder:
        self._ensure()
        self._config = replace(self._config, request_timeout_sec=value)
        return self

    def max_retries(self, value: int) -> SessionBuilder:
        self._ensure()
        self._config = replace(self._config, max_retries=value)
        return self

    def auth_bearer_token(self, token: str | None) -> SessionBuilder:
        self._ensure()
        self._config = replace(self._config, auth_bearer_token=token)
        return self

    def build(self) -> Session:
        if self._config is None:
            self._config = SessionConfig.from_env()
        return Session._from_config(self._config)

    def _ensure(self) -> None:
        if self._config is None:
            self._config = SessionConfig.from_env()


class Session:
    """Coordinator-attached workspace for **Scorpio's Python API** (REST → Rust engine).

    All query execution goes through the coordinator ``/v1/sql`` path; there is **no** local
    query engine in Python. Use :meth:`connect` or :class:`SessionBuilder`.
    """

    __slots__ = ("_config", "_client", "_session_id", "_stopped", "catalog")

    def __init__(self, config: SessionConfig, *, client: CoordinatorClient) -> None:
        self._config = config
        self._client = client
        self._session_id: str | None = None
        self._stopped = False
        self.catalog = Catalog()

    @classmethod
    def _from_config(cls, config: SessionConfig) -> Session:
        return cls(config, client=CoordinatorClient(config))

    @classmethod
    def builder(cls) -> SessionBuilder:
        return SessionBuilder()

    @classmethod
    def connect(
        cls,
        *,
        coordinator_url: str | None = None,
        tenant_id: str | None = None,
    ) -> Session:
        """Connect using ``SessionConfig.from_env()`` with optional overrides."""
        cfg = SessionConfig.from_env()
        if coordinator_url is not None:
            cfg = replace(cfg, coordinator_url=coordinator_url)
        if tenant_id is not None:
            cfg = replace(cfg, tenant_id=tenant_id)
        return cls._from_config(cfg)

    def config(self) -> Mapping[str, Any]:
        """Return a redacted view of session configuration (for logging and tests)."""
        return {
            "coordinator_url": self._config.coordinator_url,
            "tenant_id": self._config.tenant_id,
            "scheduler_host": self._config.scheduler_host,
            "scheduler_grpc_port": self._config.scheduler_grpc_port,
            "connect_timeout_sec": self._config.connect_timeout_sec,
            "request_timeout_sec": self._config.request_timeout_sec,
            "max_retries": self._config.max_retries,
            "has_auth_bearer": bool(self._config.auth_bearer_token),
        }

    def version(self) -> dict[str, str]:
        """``scorpio-python-api`` package version and optional coordinator ``GET /v1/version`` body."""
        from scorpio import __version__ as ver

        out: dict[str, str] = {"scorpio_python_api": ver}
        if self._client and not self._stopped:
            try:
                r = self._client.request("GET", "/v1/version")
                if 200 <= r.status < 300:
                    out["coordinator"] = r.body.decode("utf-8", errors="replace")[:4096]
            except (ScorpioConnectionError, ScorpioCoordinatorError):
                logger.debug("version: coordinator /v1/version not available", exc_info=True)
        return out

    def ping(self) -> bool:
        """Return True if coordinator responds with HTTP 2xx to ``GET /``."""
        try:
            r = self._client.health_get("/")
            return 200 <= r.status < 300
        except ScorpioConnectionError:
            return False

    def verify_scheduler_reachable(self) -> None:
        """Open a gRPC channel to ``host:port`` and wait until ready (requires ``grpcio``)."""
        if self._config.scheduler_host is None or self._config.scheduler_grpc_port is None:
            raise ScorpioConfigError(
                "Set SCORPIO_SCHEDULER_HOST and SCORPIO_SCHEDULER_PORT (or SessionBuilder.scheduler_endpoint)."
            )
        import grpc

        target = f"{self._config.scheduler_host}:{self._config.scheduler_grpc_port}"
        channel = grpc.insecure_channel(target)
        try:
            grpc.channel_ready_future(channel).result(timeout=self._config.connect_timeout_sec)
        finally:
            channel.close()

    def start(self) -> None:
        """Eagerly create remote session id at coordinator (``POST /v1/sessions``)."""
        self._ensure_session_id()

    def coordinator_session_id(self) -> str:
        """Return coordinator ``session_id``, creating it via ``POST /v1/sessions`` if needed."""
        return self._ensure_session_id()

    def _ensure_session_id(self) -> str:
        if self._stopped:
            raise ScorpioSqlError("Session is stopped")
        if self._session_id is None:
            self._session_id = self._client.create_session()
        return self._session_id

    def sql(self, query: str) -> pa.Table:
        """Run SQL through coordinator ``POST /v1/sql`` (Rust Scorpio / DataFusion engine)."""
        if self._stopped:
            raise ScorpioSqlError("Session is stopped")
        resp = self._client.execute_sql_raw(self._ensure_session_id(), query)
        return _table_from_coordinator_response(resp)

    def submit_sql(self, sql: str) -> "JobHandle":
        """Submit async job ``POST /v1/jobs`` (Epic 3); poll via :class:`scorpio.dataframe.job.JobHandle`."""
        from scorpio.dataframe.job import JobHandle

        if self._stopped:
            raise ScorpioSqlError("Session is stopped")
        job_id, _status = self._client.submit_job(self._ensure_session_id(), sql)
        return JobHandle(job_id=job_id, sql_text=sql)

    def run_dataframe(self, df: object) -> pa.Table:
        """Execute a lazy :class:`scorpio.dataframe.DataFrame` (compiled to SQL via this session)."""
        from scorpio.dataframe.frame import DataFrame

        if not isinstance(df, DataFrame):
            raise TypeError(f"run_dataframe expects scorpio.dataframe.DataFrame, got {type(df)!r}")
        return df.collect(self)

    def stop(self) -> None:
        """Close remote session at coordinator (best-effort) and release client-side state."""
        if self._session_id and not self._stopped:
            try:
                self._client.close_session(self._session_id)
            except ScorpioCoordinatorError:
                logger.debug("stop: coordinator close_session failed", exc_info=True)
        self._session_id = None
        self._stopped = True
