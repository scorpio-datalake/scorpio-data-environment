# Deployment (Scorpio)

## Env

- **`SCORPIO_ENGINE_ROOT`**: directory containing `engine/Cargo.toml`. Default: `<repo>/engine` (set by `scripts/build-ballista-docker.*` / `scripts/docker-compose-up.*`).
- **`COMPOSE_FILE`**: override Compose file; default **`deploy/docker-compose/docker-compose.scorpio-stack.yml`** (MVP stack). Engine-only: `deploy/docker-compose/docker-compose.scorpio-engine.yml`.

Compose **v2.20+** required for `include:` in the stack file.

## Compose MVP (`docker-compose.scorpio-stack.yml`)

Includes scheduler + executor (from `docker-compose.scorpio-engine.yml`), **slim Python runtime** (`Dockerfile.python-runtime`), **API stub** (`hashicorp/http-echo:0.2.3`), **web stub** (`Dockerfile.web-stub`). Host ports: **50050** scheduler gRPC, **50051/50052** executor, **8080** API stub, **8081**→web 80.

Build/up from repo root: `scripts/build-ballista-docker.sh` / `scripts/docker-compose-up.sh` (or `.ps1`).

## Kubernetes

`kubectl apply -k deploy/k8s/base` — same logical components; images **`scorpio-*:local`** must exist on nodes or be patched to a registry. EKS: `kubectl apply -k deploy/k8s/overlays/eks` after AWS LB Controller + image wiring.

## CI

`.github/workflows/scorpio-engine-docker.yml` runs `bash scripts/build-ballista-docker.sh` (full stack build). Rust: `scorpio-engine-multi-os.yml`.

## Python / notebooks

Images install **Scorpio's Python API** (`python/scorpio`) and `python/pipeline`; see `python/README.md` and `docs/grpc-codegen.md`. Session env vars and REST contract: `docs/python-session.md`. Lazy DataFrame: `docs/python-dataframe.md`.

## Web UI (Epic 7)

Production React shell lives under **`web/`** (Vite — see **`web/README.md`**). Operators typically:

1. **`npm ci && npm run build`** in **`web/`** (or bake the same in a frontend image Dockerfile).
2. Serve **`web/dist`** behind an ingress aligned with **`VITE_SCORPIO_COORDINATOR_URL`** (**`docs/control-plane-overview.md`**, **`docs/openapi/coordinator-v1.json`**).
3. Address **browser CORS** (proxy same-origin **or** coordinator `Access-Control-*` once **Phase 2** **`Planning/Phase2-OSS.md` P2‑E1** ships hardened HTTP).

Compose today still uses **`Dockerfile.web-stub`** placeholder; swapping in the real UI image wiring is backlog for deployment overlays (see **`docs/runbooks-multi-cloud-smoke.md`** for cloud smoke scaffolding).
