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

//! S3 integration tests against [MinIO](https://min.io/) (S3-compatible, usually run locally or in CI via Docker).
//!
//! Default `cargo test` does **not** run these (`#[ignore]`). CI runs them with `--ignored` after
//! starting MinIO; locally, see [engine/README.md](../../../../README.md).

use datafusion::execution::object_store::ObjectStoreRegistry;
use object_store::path::Path;
use object_store::{ObjectStoreExt, PutPayload};
use scorpio_core::object_store::{CustomObjectStoreRegistry, S3Options};
use url::Url;

/// Bucket must exist (CI creates it with `mc mb`). Object key under that bucket.
const DEFAULT_BUCKET: &str = "scorpio-it";
const OBJECT_KEY: &str = "integration/registry/hello.bin";

/// End-to-end check: [`CustomObjectStoreRegistry`] + S3 env credentials against a real S3 API (MinIO).
///
/// **MinIO** is an S3-compatible server used for **local and CI** testing—not AWS production. It is
/// "local" in the sense that you typically run it on `localhost` (Docker); it is still a **network**
/// integration test (not an in-memory mock).
#[tokio::test]
#[ignore = "requires MinIO (see engine/README.md); CI runs with --ignored"]
async fn s3_roundtrip_custom_registry_against_minio() {
    let _ec2_off = env_guard("AWS_EC2_METADATA_DISABLED", "true");
    let _allow_http = env_guard("AWS_ALLOW_HTTP", "true");

    let bucket = std::env::var("SCORPIO_MINIO_BUCKET").unwrap_or_else(|_| DEFAULT_BUCKET.into());
    let s3_url = format!("s3://{bucket}/{OBJECT_KEY}");
    let url = Url::parse(&s3_url).expect("valid s3 url");

    let reg = CustomObjectStoreRegistry::new(S3Options::default());
    let store = reg
        .get_store(&url)
        .expect("registry should build S3 store from AWS_* env (see object_store AmazonS3Builder::from_env)");

    let path = Path::from(OBJECT_KEY);
    const PAYLOAD: &[u8] = b"scorpio-ballista-minio-integration";
    store
        .put(&path, PutPayload::from_static(PAYLOAD))
        .await
        .expect("put object to MinIO");

    let got = store.get(&path).await.expect("get object");
    let bytes = got.bytes().await.expect("read body");
    assert_eq!(bytes.as_ref(), PAYLOAD);
}

struct EnvGuard {
    key: &'static str,
    previous: Option<String>,
}

fn env_guard(key: &'static str, value: &str) -> EnvGuard {
    let previous = std::env::var(key).ok();
    // SAFETY: integration tests run in a dedicated test binary; only this test touches these keys.
    unsafe {
        std::env::set_var(key, value);
    }
    EnvGuard { key, previous }
}

impl Drop for EnvGuard {
    fn drop(&mut self) {
        unsafe {
            if let Some(ref prev) = self.previous {
                std::env::set_var(self.key, prev);
            } else {
                std::env::remove_var(self.key);
            }
        }
    }
}
