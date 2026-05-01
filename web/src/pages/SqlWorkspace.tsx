// Licensed under the Apache License, Version 2.0 (see LICENSE in repository root).

import { Alert, Button, Chip, Paper, Stack, TextField, Typography } from "@mui/material";
import { useState } from "react";
import { apiSubmitSql } from "../api/coordinator";
import { useCoordSession } from "../context/CoordinatorSession";

export function SqlWorkspace() {
  const { sessionId, busy, error, ensureSession } = useCoordSession();
  const [sql, setSql] = useState("SELECT 1 AS n;");
  const [result, setResult] = useState<string | null>(null);
  const [runErr, setRunErr] = useState<string | null>(null);

  const runSql = async () => {
    setRunErr(null);
    setResult(null);
    let sid: string;
    try {
      sid = await ensureSession();
    } catch {
      return;
    }
    try {
      const r = await apiSubmitSql(sid, sql);
      const ct = r.headers.get("Content-Type") ?? "";
      if (r.ok) {
        if (ct.includes("arrow")) {
          const buf = await r.arrayBuffer();
          setResult(
            `Arrow IPC stream (${buf.byteLength} bytes). Decode with pyarrow/notebook wiring or extend UI with apache-arrow.`,
          );
        } else if (ct.includes("json")) {
          setResult(await r.text());
        } else {
          setResult(await r.text());
        }
      } else {
        setRunErr(`HTTP ${r.status}: ${(await r.text()).slice(0, 4096)}`);
      }
    } catch (e: unknown) {
      setRunErr(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <Stack spacing={2}>
      <Typography variant="h5">SQL workspace</Typography>
      <Typography variant="body2" color="text.secondary">
        Runs against coordinator <code>/v1/sql</code>. Ensure CORS headers on the coordinator for browser origins, or proxy this UI behind the same host.
      </Typography>
      {error || runErr ? <Alert severity="error">{error ?? runErr}</Alert> : null}
      <Stack direction="row" spacing={1} alignItems="center">
        <Chip label={`Session: ${sessionId ?? "none"}`} variant="outlined" />
        <Button variant="outlined" disabled={busy} onClick={() => void ensureSession()}>
          Acquire session
        </Button>
      </Stack>
      <TextField
        label="SQL"
        value={sql}
        onChange={(e) => setSql(e.target.value)}
        multiline
        minRows={6}
        fullWidth
      />
      <Button variant="contained" disabled={busy} onClick={() => void runSql()}>
        Run SQL
      </Button>
      {result ? (
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle2">Result</Typography>
          <Typography component="pre" sx={{ mt: 1, whiteSpace: "pre-wrap", fontFamily: "monospace" }}>
            {result}
          </Typography>
        </Paper>
      ) : null}
    </Stack>
  );
}
