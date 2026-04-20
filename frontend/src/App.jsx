import { Routes, Route } from "react-router-dom";
import { Box, Container, ThemeProvider, createTheme, CssBaseline } from "@mui/material";
import { useState, useMemo, useEffect } from "react";

// Components & Pages
import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import Login from "./pages/auth/Login";
import Register from "./pages/auth/Register";
import Profile from "./pages/auth/Profile";
import Tokens from "./pages/Tokens";
import Settings from "./pages/Settings";
import ChatList from "./pages/ChatList";
import ResponderChatPage from "./pages/responder/ChatPage";
import ChatCreate from "./pages/requester/ChatCreate";
import TaskList from "./pages/responder/TaskList";
import RequesterChatPage from "./pages/requester/ChatPage";

function App() {
  const [textScale, setTextScale] = useState(localStorage.getItem("ui-scale") || "medium");
  const [themeMode, setThemeMode] = useState(localStorage.getItem("ui-theme") || "default");
  const [forceDark, setForceDark] = useState(localStorage.getItem("ui-darkmode") === "true");

  useEffect(() => {
    const handleSync = () => {
      setForceDark(localStorage.getItem("ui-darkmode") === "true");
      setTextScale(localStorage.getItem("ui-scale") || "medium");
      setThemeMode(localStorage.getItem("ui-theme") || "default");
    };

    window.addEventListener("storage", handleSync);
    return () => window.removeEventListener("storage", handleSync);
  }, []);

  const theme = useMemo(() => {
    const scaleFactor = { small: "13px", medium: "16px", large: "19px" };
    
    const palettes = {
      default: { 
        light: { primary: "#000", accent: "#00e5ff", bg: "#fff", text: "#000" },
        dark: { primary: "#00e5ff", accent: "#008fa3", bg: "#121212", text: "#fff" }
      },
      matrix: { 
        light: { primary: "#008f11", accent: "#00ff41", bg: "#f0f0f0", text: "#003b00" },
        dark: { primary: "#00ff41", accent: "#003b00", bg: "#0d0d0d", text: "#00ff41" }
      },
      blood: { 
        light: { primary: "#4a0000", accent: "#ff5252", bg: "#fdf2f2", text: "#4a0000" },
        dark: { primary: "#ff5252", accent: "#4a0000", bg: "#0a0a0a", text: "#ff5252" }
      },
      vibe: { 
        light: { primary: "#ff00ff", accent: "#00c2c2", bg: "#f5f5fa", text: "#1a1a2e" },
        dark: { primary: "#ff00ff", accent: "#00ffff", bg: "#1a1a2e", text: "#ff00ff" }
      },
      fluffy: { 
        light: { primary: "#ffafbd", accent: "#ffc3a0", bg: "#fff5f7", text: "#ff80ab" },
        dark: { primary: "#ffafbd", accent: "#ffafbd", bg: "#2d1b1e", text: "#ffafbd" }
      },
      warm: { 
        light: { primary: "#d35400", accent: "#f39c12", bg: "#fdf5e6", text: "#5d4037" },
        dark: { primary: "#f39c12", accent: "#d35400", bg: "#1a0f00", text: "#f39c12" }
      }
    };

    const themeData = palettes[themeMode] || palettes.default;
    const active = forceDark ? themeData.dark : themeData.light;

    return createTheme({
      palette: {
        mode: forceDark ? 'dark' : 'light',
        primary: { main: active.primary },
        background: { 
          default: active.bg, 
          paper: forceDark ? active.bg : (themeMode === 'fluffy' ? "#fff" : active.bg)
        },
        text: { primary: active.text }
      },
      shape: { borderRadius: 0 }, 
      typography: { 
        fontFamily: themeMode === 'matrix' ? "'Courier New', monospace" : "'Inter', sans-serif",
      },
      components: {
        MuiCssBaseline: {
          styleOverrides: {
            html: { fontSize: scaleFactor[textScale], transition: "font-size 0.3s ease" },
            body: { 
              backgroundColor: active.bg,
              color: active.text,
              transition: localStorage.getItem("ui-animations") === "false" ? "none !important" : "background-color 0.3s ease"
            }
          },
        },
        MuiButton: { styleOverrides: { root: { borderRadius: 0, fontWeight: 900 } } },
        MuiPaper: { styleOverrides: { root: { backgroundImage: 'none', borderRadius: 0 } } },
        MuiOutlinedInput: { styleOverrides: { root: { borderRadius: 0 } } }
      },
    });
  }, [textScale, themeMode, forceDark]);

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
              <Route path="/settings" element={
                <Settings 
                  setTextScale={setTextScale} 
                  setThemeMode={setThemeMode} 
                  setForceDark={setForceDark} 
                />
              } />
              <Route path="/chat" element={<ChatList />} />
              <Route path="/chat/new" element={<ChatCreate />} />
              <Route path="/chat/:id" element={<RequesterChatPage />} />
              <Route path="/tasks/:id" element={<ResponderChatPage />} />
              <Route path="/tasks/claim" element={<TaskList />} />
            </Routes>
          </Container>
        </Box>
      </Box>
    </ThemeProvider>
  );
}

export default App;