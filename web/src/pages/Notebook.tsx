// Licensed under the Apache License, Version 2.0 (see LICENSE in repository root).

import AddIcon from "@mui/icons-material/Add";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import {
  Alert,
  Button,
  IconButton,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { Fragment, useState } from "react";
import { apiSubmitSql } from "../api/coordinator";
import { useCoordSession } from "../context/CoordinatorSession";

type Cell = { id: string; source: string; output: string };

export function Notebook() {
  const { ensureSession } = useCoordSession();
  const [cells, setCells] = useState<Cell[]>([{ id: "c1", source: "SELECT 1;", output: "" }]);
  const [busyId, setBusyId] = useState<string | null>(null);

  const addCell = () => {
    const id = `c${cells.length + 1}-${Math.random().toString(36).slice(2, 7)}`;
    setCells((prev) => [...prev, { id, source: "", output: "" }]);
  };

  const runCell = async (idx: number) => {
    const cell = cells[idx];
    if (!cell) return;
    setBusyId(cell.id);
    try {
      const sid = await ensureSession();
      const r = await apiSubmitSql(sid, cell.source);
      const ct = r.headers.get("Content-Type") ?? "";
      let out: string;
      if (r.ok && ct.includes("arrow")) {
        const buf = await r.arrayBuffer();
        out = `OK — Arrow IPC ${buf.byteLength} bytes`;
      } else {
        out = await r.text();
      }
      setCells((prev) =>
        prev.map((c, i) => (i === idx ? { ...c, output: `[HTTP ${r.status}] ${out.slice(0, 8192)}` } : c)),
      );
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setCells((prev) => prev.map((c, i) => (i === idx ? { ...c, output: `Error: ${msg}` } : c)));
    } finally {
      setBusyId(null);
    }
  };

  return (
    <Stack spacing={2}>
      <Typography variant="h5">Notebook scratch</Typography>
      <Alert severity="info">
        Cells execute SQL against the Scorpio coordinator (same backend as platform notebook images). Prefer a server-side Python kernel plus `scorpio` where you need a distributed `DataFrame`; this UI proves browser ↔ REST parity.
      </Alert>
      <Stack direction="row" spacing={1}>
        <Button startIcon={<AddIcon />} variant="outlined" onClick={addCell}>
          Add cell
        </Button>
      </Stack>
      {cells.map((cell, idx) => (
        <Fragment key={cell.id}>
          <Typography variant="caption" color="text.secondary">
            In [{idx + 1}]
          </Typography>
          <Paper sx={{ p: 2 }}>
            <Stack spacing={2}>
              <TextField
                label="SQL"
                value={cell.source}
                onChange={(e) =>
                  setCells((prev) => prev.map((c, i) => (i === idx ? { ...c, source: e.target.value } : c)))
                }
                multiline
                minRows={3}
                fullWidth
              />
              <Stack direction="row" alignItems="center" spacing={1}>
                <IconButton
                  color="primary"
                  aria-label={`Run cell ${idx + 1}`}
                  disabled={busyId !== null}
                  onClick={() => void runCell(idx)}
                  size="small"
                >
                  <PlayArrowIcon />
                </IconButton>
              </Stack>
              {cell.output ? (
                <Typography component="pre" sx={{ fontFamily: "monospace", whiteSpace: "pre-wrap", fontSize: 12 }}>
                  {cell.output}
                </Typography>
              ) : null}
            </Stack>
          </Paper>
        </Fragment>
      ))}
    </Stack>
  );
}
