import { Routes, Route } from "react-router-dom";
import { Box, Container, ThemeProvider, createTheme, CssBaseline } from "@mui/material";
import { useState, useMemo, useEffect } from "react";

import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import Login from "./pages/auth/Login";
import Register from "./pages/auth/Register";
import Profile from "./pages/auth/Profile";
import Tokens from "./pages/Tokens";
import Settings from "./pages/Settings";
import ChatList from "./pages/ChatList";
import ChatPage from "./pages/ChatPage";
import ChatCreate from "./pages/requester/ChatCreate";
import TaskList from "./pages/responder/TaskList";

function App() {
  const [textScale, setTextScale] = useState(localStorage.getItem("ui-scale") || "medium");

  const theme = useMemo(() => {
    const scaleFactor = {
      small: "12px",
      medium: "16px",
      large: "20px"
    };

    return createTheme({
      typography: {
        fontFamily: "'Inter', sans-serif",
      },
      components: {
        MuiCssBaseline: {
          styleOverrides: {
            html: {
              fontSize: scaleFactor[textScale],
              transition: "font-size 0.3s ease-in-out",
            },
          },
        },
      },
    });
  }, [textScale]);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline /> 
      <Box sx={{ display: "flex", flexDirection: "column", minHeight: "100vh", bgcolor: "#fff" }}>
        <Navbar />
        <Box component="main" sx={{ flexGrow: 1, pt: "80px" }}>
          <Container maxWidth={false} sx={{ py: 4, px: { xs: 2, md: 4 } }}>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/profile" element={<Profile />} />
              <Route path="/tokens" element={<Tokens />} />
              <Route path="/settings" element={<Settings setTextScale={setTextScale} />} />
              <Route path="/chat" element={<ChatList />} />
              <Route path="/chat/new" element={<ChatCreate />} />
              <Route path="/chat/:id" element={<ChatPage />} />
              <Route path="/tasks/claim" element={<TaskList />} />
            </Routes>
          </Container>
        </Box>
      </Box>
    </ThemeProvider>
  );
}

export default App;