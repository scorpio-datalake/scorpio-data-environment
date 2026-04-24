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

"""Errors raised by the Scorpio Python session and HTTP coordinator client."""


class ScorpioError(Exception):
    """Base class for Scorpio client errors."""


class ScorpioConfigError(ScorpioError):
    """Invalid session configuration or environment."""


class ScorpioConnectionError(ScorpioError):
    """Could not reach the coordinator or scheduler endpoint."""


class ScorpioCoordinatorError(ScorpioError):
    """Coordinator returned an error response."""


class ScorpioSqlError(ScorpioCoordinatorError):
    """SQL execution failed at the coordinator or downstream engine."""


class ScorpioNotImplementedError(ScorpioError):
    """Feature not available in this build or deployment (document upgrade path)."""
