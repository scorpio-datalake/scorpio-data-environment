// Licensed under the Apache License, Version 2.0 (see LICENSE in repository root).

import { Alert, Button, Chip, Paper, Stack, TextField, Typography } from "@mui/material";
import { useState } from "react";
import { apiJobStatus, apiSubmitJob } from "../api/coordinator";
import { useCoordSession } from "../context/CoordinatorSession";

export function Jobs() {
  const { ensureSession } = useCoordSession();
  const [sql, setSql] = useState("SELECT 1;");
  const [jobId, setJobId] = useState<string | null>(null);
  const [statusText, setStatusText] = useState<string>("");
  const [err, setErr] = useState<string | null>(null);

  const submit = async () => {
    setErr(null);
    setStatusText("");
    try {
      const sid = await ensureSession();
      const j = await apiSubmitJob(sid, sql);
      setJobId(j.job_id);
      setStatusText(JSON.stringify(j, null, 2));
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  };

  const poll = async () => {
    if (!jobId) return;
    setErr(null);
    try {
      const sid = await ensureSession();
      const body = await apiJobStatus(sid, jobId);
      setStatusText(JSON.stringify(body, null, 2));
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <Stack spacing={2}>
      <Typography variant="h5">Jobs</Typography>
      <Typography variant="body2" color="text.secondary">
        Async path: <code>POST /v1/jobs</code> then poll <code>GET /v1/jobs/</code>
        <code>{"{job_id}"}</code> per Epic 3 OpenAPI.
      </Typography>
      {err ? <Alert severity="error">{err}</Alert> : null}
      <TextField label="SQL snapshot" value={sql} onChange={(e) => setSql(e.target.value)} multiline minRows={3} fullWidth />
      <Stack direction="row" spacing={1} alignItems="center">
        <Button variant="contained" onClick={() => void submit()}>
          Submit job
        </Button>
        <Button variant="outlined" disabled={!jobId} onClick={() => void poll()}>
          Refresh status
        </Button>
        {jobId ? <Chip label={jobId} /> : null}
      </Stack>
      {statusText ? (
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle2">Status</Typography>
          <Typography component="pre" sx={{ mt: 1, fontFamily: "monospace", whiteSpace: "pre-wrap" }}>
            {statusText}
          </Typography>
        </Paper>
      ) : null}
    </Stack>
  );
}
