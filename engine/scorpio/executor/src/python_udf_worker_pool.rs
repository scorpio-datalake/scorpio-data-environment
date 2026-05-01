// Licensed to the Apache Software Foundation (ASF) under one
// or more contributor license agreements.  See the NOTICE file
// distributed with this work for additional information
// regarding copyright ownership.  The ASF licenses this file
// to you under the Apache License, Version 2.0 (the
// "License"); you may not use this file except in compliance
// with the License.  You may obtain a copy of the License at
//
//   http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing,
// software distributed under the License is distributed on an
// "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
// KIND, either express or implied.  See the License for the
// specific language governing permissions and limitations
// under the License.

//! Bounded concurrency gate for Epic 4 Python UDF worker invokes (stub IPC).
//!
//! Real execution spawns subprocesses or connects to pooled interpreters; here we only
//! model **capacity** and **timeouts** so executors can share one policy object.

use std::sync::Arc;
use std::time::Duration;
use tokio::sync::Semaphore;

/// Configuration for limiting concurrent Python UDF evaluation on an executor.
#[derive(Debug, Clone)]
pub struct PythonUdfWorkerPoolConfig {
    /// Maximum simultaneous in-flight scalar calls (minimum 1 when used).
    pub max_concurrent_python_calls: usize,
    /// Per-invoke wall-clock budget passed to downstream executor logic.
    pub invoke_timeout: Duration,
}

impl Default for PythonUdfWorkerPoolConfig {
    fn default() -> Self {
        Self {
            max_concurrent_python_calls: 4,
            invoke_timeout: Duration::from_secs(30),
        }
    }
}

/// Semaphore-backed pool coordinating Python worker concurrency.
#[derive(Debug, Clone)]
pub struct PythonUdfWorkerPool {
    config: PythonUdfWorkerPoolConfig,
    semaphore: Arc<Semaphore>,
}

impl PythonUdfWorkerPool {
    /// Constructs a pool; `max_concurrent_python_calls` is clamped to at least **1**.
    pub fn new(config: PythonUdfWorkerPoolConfig) -> Self {
        let n = config.max_concurrent_python_calls.max(1);
        Self {
            config: PythonUdfWorkerPoolConfig {
                max_concurrent_python_calls: n,
                invoke_timeout: config.invoke_timeout,
            },
            semaphore: Arc::new(Semaphore::new(n)),
        }
    }

    /// Active configuration snapshot.
    pub fn config(&self) -> &PythonUdfWorkerPoolConfig {
        &self.config
    }

    /// Remaining permits (approximate visibility for metrics/tests).
    pub fn available_slots(&self) -> usize {
        self.semaphore.available_permits()
    }

    /// Try to reserve one concurrent invoke slot — returns `None` when saturated.
    pub fn try_acquire_invoke_permit(&self) -> Option<tokio::sync::SemaphorePermit<'_>> {
        self.semaphore.try_acquire().ok()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn pool_respects_capacity() {
        let pool = PythonUdfWorkerPool::new(PythonUdfWorkerPoolConfig {
            max_concurrent_python_calls: 2,
            invoke_timeout: Duration::from_millis(1),
        });
        assert_eq!(pool.available_slots(), 2);
        let _a = pool.try_acquire_invoke_permit().expect("first");
        let _b = pool.try_acquire_invoke_permit().expect("second");
        assert!(pool.try_acquire_invoke_permit().is_none());
    }
}
