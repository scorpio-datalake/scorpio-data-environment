// Licensed under the Apache License, Version 2.0 (see LICENSE in repository root).

import MenuBookIcon from "@mui/icons-material/MenuBook";
import StorageIcon from "@mui/icons-material/Storage";
import WorkIcon from "@mui/icons-material/Work";
import WorkspacePremiumIcon from "@mui/icons-material/WorkspacePremium";
import {
  Box,
  Drawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
} from "@mui/material";
import AppBar from "@mui/material/AppBar";
import type { Theme } from "@mui/material/styles";
import { Link, Outlet, useLocation } from "react-router-dom";

const drawerWidth = 240;

function NavDrawer() {
  const location = useLocation();
  const items = [
    { to: "/sql", label: "SQL workspace", Icon: WorkspacePremiumIcon },
    { to: "/jobs", label: "Jobs", Icon: WorkIcon },
    { to: "/sessions", label: "Sessions", Icon: StorageIcon },
    { to: "/notebook", label: "Notebook", Icon: MenuBookIcon },
  ];
  return (
    <Drawer
      variant="persistent"
      open
      sx={{ "& .MuiDrawer-paper": { width: drawerWidth, boxSizing: "border-box" } }}
    >
      <Toolbar />
      <List sx={{ px: 1 }}>
        {items.map(({ to, label, Icon }) => (
          <ListItemButton
            key={to}
            component={Link}
            to={to}
            selected={location.pathname === to}
          >
            <ListItemIcon>
              <Icon fontSize="small" />
            </ListItemIcon>
            <ListItemText primary={label} />
          </ListItemButton>
        ))}
      </List>
    </Drawer>
  );
}

export function AppShell() {
  return (
    <Box sx={{ display: "flex" }}>
      <AppBar position="fixed" sx={{ zIndex: (theme: Theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <Typography variant="h6" component="span" sx={{ flexGrow: 1 }}>
            Scorpio
          </Typography>
          <Typography variant="body2" color="inherit" sx={{ opacity: 0.85 }}>
            Web UI scaffold (Epic 7)
          </Typography>
        </Toolbar>
      </AppBar>
      <NavDrawer />
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: `calc(100% - ${drawerWidth}px)`,
          ml: `${drawerWidth}px`,
          mt: 8,
          minHeight: "100vh",
          bgcolor: "grey.50",
        }}
      >
        <Outlet />
      </Box>
    </Box>
  );
}
