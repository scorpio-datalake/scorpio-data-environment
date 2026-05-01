// Licensed under the Apache License, Version 2.0 (see LICENSE in repository root).

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { apiCloseSession, apiCreateSession } from "../api/coordinator";

type CoordSessionContextVal = {
  sessionId: string | null;
  busy: boolean;
  error: string | null;
  /** Returns coordinator `session_id`, creating one when needed. */
  ensureSession: () => Promise<string>;
  clearSession: () => Promise<void>;
};

const CoordSessionCtx = createContext<CoordSessionContextVal | null>(null);

export function CoordSessionProvider({ children }: { children: ReactNode }) {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const ensureSession = useCallback(async (): Promise<string> => {
    setBusy(true);
    setError(null);
    try {
      const sid = sessionId ?? (await apiCreateSession());
      setSessionId(sid);
      return sid;
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(msg);
      throw e;
    } finally {
      setBusy(false);
    }
  }, [sessionId]);

  const clearSession = useCallback(async () => {
    if (!sessionId) return;
    setBusy(true);
    setError(null);
    try {
      await apiCloseSession(sessionId);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSessionId(null);
      setBusy(false);
    }
  }, [sessionId]);

  const val = useMemo(
    (): CoordSessionContextVal => ({
      sessionId,
      busy,
      error,
      ensureSession,
      clearSession,
    }),
    [sessionId, busy, error, ensureSession, clearSession],
  );

  return <CoordSessionCtx.Provider value={val}>{children}</CoordSessionCtx.Provider>;
}

export function useCoordSession(): CoordSessionContextVal {
  const c = useContext(CoordSessionCtx);
  if (!c) throw new Error("useCoordSession requires CoordSessionProvider");
  return c;
}
