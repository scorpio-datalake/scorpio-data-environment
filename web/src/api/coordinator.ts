// Licensed under the Apache License, Version 2.0 (see LICENSE in repository root).
//
// Minimal browser client for Scorpio coordinator OpenAPI v1 (`docs/openapi/coordinator-v1.json`).
// CORS must be allowed by the coordinator, or terminate TLS at a same-origin gateway.

export type CoordinatorConfig = {
  baseUrl: string;
  tenantId: string;
  bearer: string;
};

export function coordinatorConfig(): CoordinatorConfig {
  const base =
    import.meta.env.VITE_SCORPIO_COORDINATOR_URL?.replace(/\/$/, "") ??
    "http://127.0.0.1:8080";
  return {
    baseUrl: base,
    tenantId: import.meta.env.VITE_SCORPIO_TENANT_ID ?? "",
    bearer: import.meta.env.VITE_SCORPIO_AUTH_BEARER ?? "",
  };
}

export function coordinatorHeaders(extra?: HeadersInit): Headers {
  const c = coordinatorConfig();
  const h = new Headers(extra);
  h.set(
    "User-Agent",
    "scorpio-web-ui/epic7 (Mozilla-compatible; Scorpio OSS UI scaffold)",
  );
  if (c.tenantId) {
    h.set("X-Scorpio-Tenant-Id", c.tenantId);
  }
  if (c.bearer) {
    h.set("Authorization", `Bearer ${c.bearer}`);
  }
  return h;
}

async function coordinatorFetch(
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  const c = coordinatorConfig();
  const url = `${c.baseUrl}${path.startsWith("/") ? path : `/${path}`}`;
  const headers = coordinatorHeaders(init.headers);
  const method = init.method ?? "GET";
  if (method !== "GET" && method !== "HEAD" && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  return fetch(url, {
    ...init,
    headers,
  });
}

export async function apiCreateSession(): Promise<string> {
  const r = await coordinatorFetch("/v1/sessions", {
    method: "POST",
    body: JSON.stringify({ tenant_id: coordinatorConfig().tenantId || null }),
  });
  if (!r.ok) throw new Error(`createSession: HTTP ${r.status}`);
  const j = (await r.json()) as { session_id?: string };
  const id = j.session_id;
  if (!id) throw new Error(`createSession: bad payload ${JSON.stringify(j)}`);
  return id;
}

export async function apiCloseSession(sessionId: string): Promise<void> {
  const r = await coordinatorFetch(`/v1/sessions/${encodeURIComponent(sessionId)}/close`, {
    method: "POST",
    body: "{}",
  });
  if (!(r.ok || r.status === 204)) throw new Error(`closeSession: HTTP ${r.status}`);
}

export async function apiSubmitSql(sessionId: string, sql: string): Promise<Response> {
  const r = await coordinatorFetch(`/v1/sql`, {
    method: "POST",
    body: JSON.stringify({
      session_id: sessionId,
      sql,
      tenant_id: coordinatorConfig().tenantId || null,
    }),
  });
  return r;
}

export async function apiSubmitJob(
  sessionId: string,
  sql: string,
): Promise<{ job_id: string; status: string }> {
  const r = await coordinatorFetch(`/v1/jobs`, {
    method: "POST",
    body: JSON.stringify({
      session_id: sessionId,
      sql,
      tenant_id: coordinatorConfig().tenantId || null,
    }),
  });
  if (!r.ok) throw new Error(`submitJob: HTTP ${r.status}`);
  return (await r.json()) as { job_id: string; status: string };
}

export async function apiJobStatus(sessionId: string, jobId: string): Promise<unknown> {
  const q = new URLSearchParams({ session_id: sessionId });
  const r = await coordinatorFetch(`/v1/jobs/${encodeURIComponent(jobId)}?${q}`, {
    method: "GET",
  });
  if (!r.ok) throw new Error(`jobStatus: HTTP ${r.status}`);
  return r.json();
}
