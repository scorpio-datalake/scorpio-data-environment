# Object store credentials (S3, GCS, ADLS) — Scorpio engine

**Goal:** Run scheduler and executor containers **without baking secrets into images**. Supply credentials at deploy time via **environment variables** (from plain env, Docker/Kubernetes secrets, or workload identity).

**Code reference:** `engine/scorpio/core/src/object_store.rs` — `CustomObjectStoreRegistry`.

---

## Principles

1. **Images** contain only binaries and default config; **no** `AWS_SECRET_ACCESS_KEY`, service-account JSON, or storage account keys in layers.
2. **Same contract on every process** that opens `s3://`, `gs://`, or `abfs://` paths: scheduler **and** each executor must receive the **same** env (or equivalent IAM bindings), because tasks run where executors run.
3. **Prefer cloud-native identity** (IRSA on EKS, workload identity on GKE, managed identity on AKS) over long-lived keys when the `object_store` / AWS SDK chain supports it for your deployment.

---

## Amazon S3 (`s3://`)

The registry starts from [`AmazonS3Builder::from_env`](https://docs.rs/object_store/latest/object_store/aws/struct.AmazonS3Builder.html#method.from_env). Optional SQL `SET` keys (`s3.access_key_id`, `s3.secret_access_key`, …) override the env chain when **both** access key and secret are set.

**Common variables (non-exhaustive):**

| Variable | Role |
|----------|------|
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | Static keys from a secret (dev/CI or break-glass) |
| `AWS_SESSION_TOKEN` | Temporary credentials / STS |
| `AWS_REGION` / `AWS_DEFAULT_REGION` | Region |
| `AWS_ENDPOINT_URL` (and SDK-specific variants) | S3-compatible endpoints (MinIO, LocalStack); confirm against the AWS SDK / `object_store` version pinned in `engine/Cargo.toml` |
| `AWS_WEB_IDENTITY_TOKEN_FILE` / `AWS_ROLE_ARN` | IRSA and similar OIDC-based roles |
| `AWS_ENDPOINT_URL_S3` | S3 API endpoint (required for **MinIO** / LocalStack-style hosts) |
| `AWS_ALLOW_HTTP` | Set to `true` when the endpoint uses `http://` (typical for local MinIO) |

**Local / CI testing with MinIO:** MinIO is an S3-compatible server you run **locally** (often via Docker) to exercise real PUT/GET against the same code path as AWS—without AWS credentials. It is still a **network integration** test, not an in-process mock. See [../engine/README.md](../engine/README.md) (section *S3 / MinIO integration test*) and `scorpio/core/tests/s3_minio_integration.rs`.

**Kubernetes (pattern):** define a `Secret` with string data, mount into **scheduler** and **executor** `Deployment`/`StatefulSet` via `envFrom` (same secret name in both) or individual `valueFrom.secretKeyRef` entries.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: scorpio-aws
type: Opaque
stringData:
  AWS_ACCESS_KEY_ID: "<from vault>"
  AWS_SECRET_ACCESS_KEY: "<from vault>"
  AWS_DEFAULT_REGION: "us-east-1"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: scorpio-executor
spec:
  template:
    spec:
      containers:
        - name: executor
          envFrom:
            - secretRef:
                name: scorpio-aws
```

For **IRSA**, omit static keys; mount the projected token and set `AWS_ROLE_ARN` and `AWS_WEB_IDENTITY_TOKEN_FILE` per the EKS documentation.

**Docker Compose:** use `env_file` pointing to a file that is **gitignored**, or `secrets` + Compose syntax your version supports; never commit `.env` with real keys.

---

## Google Cloud Storage (`gs://`)

Uses `GoogleCloudStorageBuilder::from_env`. Typical approaches:

| Approach | Notes |
|----------|--------|
| **Workload Identity (GKE)** | Preferred; no JSON in the cluster as a long-term default |
| **`GOOGLE_APPLICATION_CREDENTIALS`** | Path to a **mounted** service-account JSON (from secret volume), not copied into the image |

Mount the same secret or service account into **scheduler and executors**.

---

## Azure Data Lake Storage / Blob (`abfs://`, `abfss://`, `azure://`, …)

Uses `MicrosoftAzureBuilder::from_env`. Common variables include `AZURE_STORAGE_ACCOUNT_NAME` (or account URL patterns per [`object_store` Azure docs](https://docs.rs/object_store/latest/object_store/azure/struct.MicrosoftAzureBuilder.html)), access keys, SAS, or managed identity as supported by the crate version pinned in `engine/Cargo.toml`.

**AKS:** prefer **managed identity** + federated credentials over account keys in secrets.

**HTTPS Azure hosts** (`https://*.blob.core.windows.net`, `*.dfs.core.windows.net`, Fabric hosts) use the same Azure builder and env contract.

---

## Operational checklist

- [ ] Scheduler `Deployment` has required env (or IRSA/workload identity equivalent).
- [ ] **Every** executor replica has the **same** env for cloud reads/writes used in jobs.
- [ ] CI uses short-lived credentials or MinIO with scoped test buckets.
- [ ] SQL `SET s3.*` is reserved for **session overrides**, not the primary secret path in production.

---

## Related docs

- [scorpio-engine-compatibility.md](scorpio-engine-compatibility.md)
- [../engine/README.md](../engine/README.md)
