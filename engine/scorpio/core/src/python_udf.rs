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

//! Session-scoped scalar Python UDF payloads (Epic 4 control-plane contract).
//!
//! Executors will consume these definitions once Arrow IPC to a Python worker
//! pool is attached to distributed plans; today this module provides shared
//! serde-friendly structs and an in-memory registry for tests and future HTTP layers.

use parking_lot::Mutex;
use std::collections::HashMap;
use std::sync::Arc;

/// Serialized scalar UDF handed from coordinator / driver to executor workers.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PythonScalarUdfDefinition {
    /// Function name exposed in SQL for the owning session.
    pub name: String,
    /// Python source text (`def foo(x): ...` style) stored verbatim until execution validates it.
    pub source: String,
    /// Logical Arrow return type hint (DataFusion-compatible string, e.g. `float64`).
    pub return_arrow_type: String,
}

impl PythonScalarUdfDefinition {
    /// Build a definition with sanitized non-empty identifiers.
    pub fn validate(&self) -> Result<(), &'static str> {
        let n = self.name.trim();
        if n.is_empty() {
            return Err("udf name must be non-empty");
        }
        if self.source.trim().is_empty() {
            return Err("udf source must be non-empty");
        }
        if self.return_arrow_type.trim().is_empty() {
            return Err("return_arrow_type must be non-empty");
        }
        Ok(())
    }
}

/// In-memory registry keyed by `(session_id, udf_name)` — usable by coordinator shims or tests.
#[derive(Debug, Clone)]
pub struct SessionPythonUdfRegistry {
    inner: Arc<Mutex<HashMap<(String, String), PythonScalarUdfDefinition>>>,
}

impl Default for SessionPythonUdfRegistry {
    fn default() -> Self {
        Self {
            inner: Arc::new(Mutex::new(HashMap::new())),
        }
    }
}

impl SessionPythonUdfRegistry {
    /// New empty registry.
    pub fn new() -> Self {
        Self::default()
    }

    /// Insert or replace a UDF bound to `session_id`.
    pub fn register(
        &self,
        session_id: impl Into<String>,
        def: PythonScalarUdfDefinition,
    ) -> Result<(), &'static str> {
        def.validate()?;
        let session_id = session_id.into();
        let name = def.name.clone();
        self.inner.lock().insert((session_id, name), def);
        Ok(())
    }

    /// Fetch a definition if present.
    pub fn get(&self, session_id: &str, name: &str) -> Option<PythonScalarUdfDefinition> {
        self.inner
            .lock()
            .get(&(session_id.to_string(), name.to_string()))
            .cloned()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn register_and_get_round_trip() {
        let reg = SessionPythonUdfRegistry::new();
        let def = PythonScalarUdfDefinition {
            name: "triple".to_string(),
            source: "def triple(x): return 3 * x".to_string(),
            return_arrow_type: "float64".to_string(),
        };
        reg.register("sess-a", def.clone()).unwrap();
        assert_eq!(reg.get("sess-a", "triple"), Some(def));
        assert!(reg.get("sess-b", "triple").is_none());
    }

    #[test]
    fn reject_empty_name() {
        let reg = SessionPythonUdfRegistry::new();
        let bad = PythonScalarUdfDefinition {
            name: "  ".to_string(),
            source: "def x(): return 1".to_string(),
            return_arrow_type: "float64".to_string(),
        };
        assert!(reg.register("s", bad).is_err());
    }
}
