# Multi-cloud freeware smoke (Epic 12 — GKE, EKS, AKS)

Purpose: reproduce a **minimal**, **cheap** Scorpio smoke on three clouds—not production sizing.

**References:** **`deploy/docker-compose/`** for local analogue; **`docs/deployment.md`**, **`docs/object-store-credentials.md`**, **`docs/engine-test-coverage-inventory.md`**.

Common prep:

1. Build or pull Scorpio scheduler/executor/control-plane/coordinator images (pin tags explicitly).
2. Create a tiny cluster (single small node pool or trial Autopilot-equivalent acceptable).
3. Apply **`deploy/k8s/base`** (or cloud overlay stub) plus secrets for object storage IAM.
4. Run **health**: coordinator **`GET /`**, then **`POST /v1/sql`** or Rust client smoke aligned with **`Planning/Phase1.md` Epic 0–3**.
5. **Teardown**: delete cluster or scale to zero; document lingering costs.

Optional **object-store** reads by cloud (**gs://**, **s3://**, **Azure blobs**) using **short-lived** credentials—not MinIO-only—unless the runbook records an explicit skip with reason.

**Multi-executor:** target **≥2** executor Pods with at least **cancel job** or **failure** path documented (**kubectl**, REST cancel, or script).

---

## Google Cloud — GKE (skeleton)

- Enable API; create VPC + minimal Autopilot cluster *or* `e2-small`/`e2-micro` sanity node pool (pick one SKU and codify limits).
- Workload Identity or service account JSON for **`gs://`** access if exercised.
- Document **trial/free tier** caveat and teardown command (`gcloud container clusters delete …`).

## AWS — EKS (skeleton)

- Minimal managed node group (t3.small-equivalent acceptable) **or** Fargate-only profile — document ingress limitations.
- IRSA (**IAM Roles for Service Accounts**) for **`s3://`** pulls if exercised.
- `eksctl`/Terraform equivalent one-liners go here when validated.

## Azure — AKS (skeleton)

- Smallest SKU node pool permitted in region; MSI or workload identity secret for **`abfss://`/blob** if exercised.
- Document **Consumption/billing caps** reminders for trial subs.

---

**CI cron** for **`cargo test -p scorpio-core --features build-binary`** is optional backlog (**Epic 12** checklist) — tracked separately from mandatory PR pipelines.
