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

Images install from `python/scorpio` and `python/pipeline`; see `python/README.md` and `docs/grpc-codegen.md`. Python **session** env vars and coordinator REST contract: `docs/python-session.md`.
