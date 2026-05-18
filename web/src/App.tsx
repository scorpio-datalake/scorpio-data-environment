// Licensed under the Apache License, Version 2.0 (see LICENSE in repository root).

import { CssBaseline, ThemeProvider } from "@mui/material";
import { Navigate, Route, Routes } from "react-router-dom";
import { CoordSessionProvider } from "./context/CoordinatorSession";
import { AppShell } from "./layout/AppShell";
import { Jobs } from "./pages/Jobs";
import { Notebook } from "./pages/Notebook";
import { Sessions } from "./pages/Sessions";
import { SqlWorkspace } from "./pages/SqlWorkspace";
import { scorpioTheme } from "./theme";

export function App() {
  return (
    <ThemeProvider theme={scorpioTheme}>
      <CssBaseline />
      <CoordSessionProvider>
        <Routes>
          <Route element={<AppShell />}>
            <Route index element={<Navigate to="/sql" replace />} />
            <Route path="sql" element={<SqlWorkspace />} />
            <Route path="jobs" element={<Jobs />} />
            <Route path="sessions" element={<Sessions />} />
            <Route path="notebook" element={<Notebook />} />
          </Route>
          <Route path="*" element={<Navigate to="/sql" replace />} />
        </Routes>
      </CoordSessionProvider>
    </ThemeProvider>
  );
}
