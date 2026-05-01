# Operator roadmap — authentication and tenancy (Epic 9)

**Phase 1 OSS** exposes **headers and env placeholders** (`X-Scorpio-Tenant-Id`, bearer token in **`scorpio`** **`SessionConfig`**) documented in **[`python-session.md`](python-session.md)** — enough for demos and Compose.

**Epic 9 hardened** posture (**post–Phase 1**, coordinator-backed) requires:

1. **Token validation** bound to issuer + audience; short-lived credentials.
2. **Tenant resolution** and **authorization** denying cross-tenant resource access server-side—not only trusting client headers.
3. **Audit** hooks (who ran which job against which metastore/catalog).
4. **Optional IdP**: OIDC/SAML federation (optional layer); keep the documented OSS path simple (`Planning/Phase1.md` guardrail).

Implement when **`Planning/Phase2-OSS.md`** coordinator (**P2‑E1**) and deployment recipes stabilize enough to anchor policy middleware at the coordinator edge.
