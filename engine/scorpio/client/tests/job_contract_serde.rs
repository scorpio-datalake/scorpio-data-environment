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

//! JSON envelopes shared with **Scorpio's Python API** coordinator client (Epic 3).
//! Keep in sync with `docs/openapi/coordinator-v1.json` at the repository root.

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SubmitJobRequest {
    pub session_id: String,
    pub sql: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tenant_id: Option<String>,
    /// `substrait` or `opaque`; optional wire field from `coordinator-v1.json`.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub plan_encoding: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub plan_ir_version: Option<String>,
    /// Base64 plan blob when coordinator accepts non-SQL IR.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub plan_bytes: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SubmitJobResponse {
    pub job_id: String,
    pub status: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct JobStatusResponse {
    pub job_id: String,
    pub session_id: String,
    pub status: String,
    #[serde(default)]
    pub error: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CancelJobRequest {
    pub session_id: String,
}

#[test]
fn submit_job_request_roundtrip() {
    let v = SubmitJobRequest {
        session_id: "s1".into(),
        sql: "SELECT 1".into(),
        tenant_id: Some("t1".into()),
        plan_encoding: None,
        plan_ir_version: None,
        plan_bytes: None,
    };
    let json = serde_json::to_string(&v).unwrap();
    let back: SubmitJobRequest = serde_json::from_str(&json).unwrap();
    assert_eq!(v, back);
}

#[test]
fn submit_job_request_optional_plan_fields_roundtrip() {
    let json = r#"{"session_id":"s","sql":"SELECT 1","plan_encoding":"substrait","plan_ir_version":"0.1","plan_bytes":"AQID"}"#;
    let v: SubmitJobRequest = serde_json::from_str(json).unwrap();
    assert_eq!(v.session_id, "s");
    assert_eq!(v.sql, "SELECT 1");
    assert_eq!(v.plan_encoding.as_deref(), Some("substrait"));
    assert_eq!(v.plan_ir_version.as_deref(), Some("0.1"));
    assert_eq!(v.plan_bytes.as_deref(), Some("AQID"));

    let encoded = serde_json::to_string(&v).unwrap();
    let back: SubmitJobRequest = serde_json::from_str(&encoded).unwrap();
    assert_eq!(v, back);
}

#[test]
fn submit_job_request_ignores_unknown_json_keys() {
    let json = r#"{"session_id":"s","sql":"x","future_field":true}"#;
    let v: SubmitJobRequest = serde_json::from_str(json).unwrap();
    assert_eq!(v.session_id, "s");
    assert_eq!(v.sql, "x");
}

#[test]
fn submit_job_response_matches_openapi_example() {
    let j = r#"{"job_id":"j-7","status":"QUEUED"}"#;
    let v: SubmitJobResponse = serde_json::from_str(j).unwrap();
    assert_eq!(v.job_id, "j-7");
    assert_eq!(v.status, "QUEUED");
}

#[test]
fn job_status_response_optional_error() {
    let j = r#"{"job_id":"j-1","session_id":"s","status":"SUCCEEDED","error":null}"#;
    let v: JobStatusResponse = serde_json::from_str(j).unwrap();
    assert_eq!(v.status, "SUCCEEDED");
    assert!(v.error.is_none() || v.error.as_deref() == Some(""));
}

#[test]
fn cancel_job_request_roundtrip() {
    let v = CancelJobRequest {
        session_id: "stub-session".into(),
    };
    let json = serde_json::to_string(&v).unwrap();
    assert!(json.contains("stub-session"));
    let back: CancelJobRequest = serde_json::from_str(&json).unwrap();
    assert_eq!(v, back);
}
