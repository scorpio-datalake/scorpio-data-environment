# gRPC / protobuf — Python codegen

## Where `.proto` lives

| Location | Role |
|----------|------|
| `engine/scorpio/core/proto/` (and related `build.rs`) | **Canonical** for the Rust workspace today. |
| `apis/proto/` | Optional **copies or hand-trimmed** `.proto` for Python-only CI or public API contracts. Keep in sync manually or with a small sync script later. |

Recommendation: treat **engine** as source of truth; add files under `apis/proto/` only when you want a language-neutral publish surface or to decouple Python codegen from a split repo.

## Output package

Generate into **`python/scorpio/src/scorpio/_grpc/`** (package already stubbed). Add generated modules to `.gitignore` if you prefer generated-only CI; or commit stubs for offline builds.

## grpcio-tools (one-off)

From repo root, with protos copied to `apis/proto` (example paths—adjust to match files you sync):

```bash
python -m pip install grpcio-tools
python -m grpc_tools.protoc -I apis/proto --python_out=python/scorpio/src/scorpio \
  --grpc_python_out=python/scorpio/src/scorpio apis/proto/example.proto
```

Move/rename outputs so imports live under `scorpio._grpc` (see [grpcio generated layout](https://grpc.io/docs/languages/python/quickstart/)).

## buf (optional)

Initialize `buf.yaml` / `buf.gen.yaml` under `apis/` when you outgrow ad-hoc `protoc` lines; keep `python_out` pointed at `scorpio/_grpc/`.
