# Python packages (`python/`)

## Deployed platform (MLE)

Images install **`scorpio`** and **`scorpio-pipeline`** from this repo with `pip install` (no `pip` on the user laptop). See `deploy/docker-compose/Dockerfile.python-runtime` and `docs/deployment.md`.

## Contributors

Editable installs from the monorepo root:

```bash
pip install -e python/scorpio
pip install -e python/pipeline
```

Optional: `uv pip install -e python/scorpio -e python/pipeline`.

**Scorpio's Python API** (`scorpio-python-api`): session + lazy DataFrame — [docs/python-session.md](../docs/python-session.md), [docs/python-dataframe.md](../docs/python-dataframe.md).
