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

"""Session configuration loaded from explicit parameters and environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    return float(raw)


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    return int(raw)


@dataclass
class SessionConfig:
    """Coordinator REST base URL, tenant binding, timeouts, and optional auth.

    Environment variables are documented in ``docs/python-session.md`` in the monorepo:
    ``SCORPIO_COORDINATOR_URL``, ``SCORPIO_TENANT_ID``, ``SCORPIO_CONNECT_TIMEOUT``,
    ``SCORPIO_REQUEST_TIMEOUT``, ``SCORPIO_HTTP_RETRIES``, ``SCORPIO_HTTP_RETRY_BACKOFF_SEC``,
    ``SCORPIO_AUTH_BEARER``, ``SCORPIO_SCHEDULER_HOST``, ``SCORPIO_SCHEDULER_PORT``.
    """

    coordinator_url: str = "http://127.0.0.1:8080"
    tenant_id: str | None = None
    connect_timeout_sec: float = 10.0
    request_timeout_sec: float = 120.0
    max_retries: int = 3
    retry_backoff_sec: float = 0.4
    auth_bearer_token: str | None = field(default=None, repr=False)
    scheduler_host: str | None = None
    scheduler_grpc_port: int | None = None

    @classmethod
    def from_env(cls) -> SessionConfig:
        """Build a config from ``SCORPIO_*`` environment variables (see deployment docs)."""
        url = os.environ.get("SCORPIO_COORDINATOR_URL", "http://127.0.0.1:8080").strip()
        tenant = os.environ.get("SCORPIO_TENANT_ID")
        tenant = tenant.strip() if tenant else None
        bearer = os.environ.get("SCORPIO_AUTH_BEARER")
        bearer = bearer.strip() if bearer else None
        host = os.environ.get("SCORPIO_SCHEDULER_HOST")
        host = host.strip() if host else None
        port_raw = os.environ.get("SCORPIO_SCHEDULER_PORT")
        port = int(port_raw.strip()) if port_raw and port_raw.strip() else None
        return cls(
            coordinator_url=url,
            tenant_id=tenant,
            connect_timeout_sec=_env_float("SCORPIO_CONNECT_TIMEOUT", 10.0),
            request_timeout_sec=_env_float("SCORPIO_REQUEST_TIMEOUT", 120.0),
            max_retries=_env_int("SCORPIO_HTTP_RETRIES", 3),
            retry_backoff_sec=_env_float("SCORPIO_HTTP_RETRY_BACKOFF_SEC", 0.4),
            auth_bearer_token=bearer,
            scheduler_host=host,
            scheduler_grpc_port=port,
        )
