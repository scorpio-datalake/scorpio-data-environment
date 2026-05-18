// Licensed under the Apache License, Version 2.0 (see LICENSE in repository root).

import { createTheme } from "@mui/material/styles";

export const scorpioTheme = createTheme({
  palette: {
    mode: "light",
    primary: { main: "#1565c0" },
    secondary: { main: "#37474f" },
  },
  typography: {
    fontFamily: '"DM Sans","Roboto","Helvetica","Arial",sans-serif',
    h6: { fontWeight: 600 },
  },
});
