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

"""Deferred job handle bridging DataFrame actions to coordinator (Epic 3 placeholder)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

import pyarrow as pa

if TYPE_CHECKING:
    from scorpio.session import Session


@dataclass
class JobHandle:
    """Opaque job reference; Epic 3 will add status/cancel/streaming over coordinator APIs.

    Today ``submit`` captures the compiled SQL so ``result_arrow`` can run via
    ``Session.sql`` without a second compile step.
    """

    job_id: str
    sql_text: str

    def status(self) -> Literal["PENDING", "RUNNING", "SUCCEEDED", "FAILED", "UNKNOWN"]:
        """Coordinator job status (stub until Epic 3)."""
        return "PENDING"

    def cancel(self) -> None:
        """Request cancellation (stub until Epic 3)."""
        raise NotImplementedError("JobHandle.cancel — Epic 3 coordinator API")

    def result_arrow(self, session: Session) -> pa.Table:
        """Materialize using the same SQL snapshot held on this handle."""
        return session.sql(self.sql_text)
