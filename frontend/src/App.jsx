import { Routes, Route } from "react-router-dom";
import { Box, Container, ThemeProvider, createTheme, CssBaseline } from "@mui/material";
import { useState, useMemo } from "react";

// Components & Pages
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
  const [themeMode, setThemeMode] = useState(localStorage.getItem("ui-theme") || "default");

  const theme = useMemo(() => {
    const scaleFactor = { small: "13px", medium: "16px", large: "19px" };
    
    const palettes = {
      default: { primary: "#000", accent: "#00e5ff", bg: "#fff", text: "#000", mode: 'light' },
      matrix: { primary: "#00ff41", accent: "#003b00", bg: "#0d0d0d", text: "#00ff41", mode: 'dark' },
      blood: { primary: "#ff5252", accent: "#4a0000", bg: "#0a0a0a", text: "#ff5252", mode: 'dark' },
      vibe: { primary: "#ff00ff", accent: "#00ffff", bg: "#1a1a2e", text: "#ff00ff", mode: 'dark' },
      fluffy: { primary: "#ffafbd", accent: "#ffc3a0", bg: "#fff5f7", text: "#ff80ab", mode: 'light' },
      warm: { primary: "#d35400", accent: "#f39c12", bg: "#fdf5e6", text: "#5d4037", mode: 'light' }
    };

    const active = palettes[themeMode] || palettes.default;
    const isFluffy = themeMode === 'fluffy';

    return createTheme({
      palette: {
        mode: active.mode,
        primary: { main: active.primary },
        background: { default: active.bg, paper: isFluffy ? "#fff" : active.bg },
        text: { primary: active.text }
      },
      // Universal straight corners
      shape: { borderRadius: 0 }, 
      typography: { 
        fontFamily: themeMode === 'matrix' ? "'Courier New', monospace" : "'Inter', sans-serif",
      },
      components: {
        MuiCssBaseline: {
          styleOverrides: {
            html: { fontSize: scaleFactor[textScale], transition: "font-size 0.3s ease" },
            body: { backgroundColor: active.bg, color: active.text }
          },
        },
        MuiButton: {
          styleOverrides: {
            root: { borderRadius: 0, fontWeight: 900 }
          }
        },
        MuiPaper: {
          styleOverrides: {
            root: { backgroundImage: 'none', borderRadius: 0 }
          }
        },
        MuiOutlinedInput: {
          styleOverrides: {
            root: { borderRadius: 0 }
          }
        }
      },
    });
  }, [textScale, themeMode]);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline /> 
      <Box sx={{ display: "flex", flexDirection: "column", minHeight: "100vh", bgcolor: "background.default" }}>
        <Navbar />
        <Box component="main" sx={{ flexGrow: 1, pt: "80px" }}>
          <Container maxWidth={false} sx={{ py: 4, px: { xs: 2, md: 4 } }}>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/profile" element={<Profile />} />
              <Route path="/tokens" element={<Tokens />} />
              <Route path="/settings" element={<Settings setTextScale={setTextScale} setThemeMode={setThemeMode} />} />
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