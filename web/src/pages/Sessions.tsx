// Licensed under the Apache License, Version 2.0 (see LICENSE in repository root).

import { Alert, Button, Paper, Stack, Typography } from "@mui/material";
import { useCoordSession } from "../context/CoordinatorSession";

export function Sessions() {
  const { sessionId, busy, error, ensureSession, clearSession } = useCoordSession();

  return (
    <Stack spacing={2}>
      <Typography variant="h5">Sessions</Typography>
      <Typography variant="body2" color="text.secondary">
        Maps to coordinator <code>POST /v1/sessions</code> and <code>POST /v1/sessions/…/close</code> (
        <code>docs/openapi/coordinator-v1.json</code>).
      </Typography>
      {error ? <Alert severity="error">{error}</Alert> : null}
      <Paper sx={{ p: 2 }}>
        <Typography variant="body1" sx={{ mb: 2 }}>
          Active session id: <strong>{sessionId ?? "—"}</strong>
        </Typography>
        <Stack direction="row" spacing={2}>
          <Button variant="contained" disabled={busy} onClick={() => void ensureSession()}>
            Create / refresh session
          </Button>
          <Button variant="outlined" color="warning" disabled={busy || !sessionId} onClick={() => void clearSession()}>
            Close session
          </Button>
        </Stack>
      </Paper>
    </Stack>
  );
}
