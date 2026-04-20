import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import { 
  AppBar, 
  Toolbar, 
  Button, 
  Typography, 
  Box, 
  Container, 
  Divider,
  useTheme 
} from "@mui/material";

// Icons
import LoginIcon from '@mui/icons-material/Login';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import LogoutIcon from '@mui/icons-material/Logout';
import TokenIcon from '@mui/icons-material/Token';
import ForumIcon from '@mui/icons-material/Forum';
import PsychologyIcon from '@mui/icons-material/Psychology';
import SettingsIcon from '@mui/icons-material/Settings';

// Assets
import catLogo from "../assets/cat1.png";

const BACKEND_URL = "";

function Navbar() {
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme(); 
  const token = localStorage.getItem("token");
  const email = localStorage.getItem("email"); 
  const [balance, setBalance] = useState(0);
  
  const [animationsEnabled, setAnimationsEnabled] = useState(localStorage.getItem("ui-animations") !== "false");

  // Theme Detection
  const currentThemeId = localStorage.getItem("ui-theme") || "default";
  const isDefault = currentThemeId === 'default';
  const isCyber = currentThemeId === 'matrix';
  const isBlood = currentThemeId === 'blood';
  const isRetro = currentThemeId === 'vibe';
  const isWarm = currentThemeId === 'warm';
  const isDarkMode = theme.palette.mode === 'dark';

  const getLogoutColor = () => {
    if (isDarkMode) return '#ff5252';
    if (isCyber) return '#003b00';
    if (isWarm) return '#5d4037';
    return '#ff5252';
  };

  const logoutColor = getLogoutColor();

  let navBg = isDarkMode ? "#000" : theme.palette.primary.main;
  
  if (isDefault) navBg = "#000";
  if (isBlood)   navBg = "#1a0000";
  if (isRetro)   navBg = "#0f0f1e";

  const navTextColor = "#fff"; 
  const borderColor = isDefault ? "#333" : "rgba(255,255,255,0.2)";

  const isActive = (path) => location.pathname === path;

  useEffect(() => {
    const handleSync = () => {
      setAnimationsEnabled(localStorage.getItem("ui-animations") !== "false");
    };

    const fetchBalance = async () => {
      if (token) {
        try {
          const res = await axios.get(`${BACKEND_URL}/v1/tokens`, {
            headers: { Authorization: `Bearer ${token}` },
            params: { accountName: email } 
          });
          setBalance(res.data.tokenBalance);
        } catch (err) {
          console.error("Failed to fetch balance", err);
        }
      }
    };

    fetchBalance();
    window.addEventListener("storage", handleSync);
    const interval = setInterval(fetchBalance, 30000);
    
    return () => {
      clearInterval(interval);
      window.removeEventListener("storage", handleSync);
    };
  }, [token, email]);

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    localStorage.removeItem("email");
    navigate("/login");
  };

  const underlineEffect = (active, color = '#fff') => ({
    '&::after': {
      content: '""',
      position: 'absolute',
      bottom: 0,
      left: 0,
      width: active ? '100%' : '0%',
      height: '3px',
      bgcolor: color,
      transition: animationsEnabled ? 'width 0.3s ease-in-out' : 'none',
    },
    '&:hover::after': {
      width: '100%',
    }
  });

  const getNavButtonStyle = (path, customColor = '#eee', activeBg = 'rgba(255,255,255,0.1)') => {
    const active = isActive(path);
    
    return {
      textTransform: 'none',
      borderRadius: 0, 
      fontWeight: active ? 800 : 600,
      px: animationsEnabled ? (active ? 5 : 4) : 4, 
      minWidth: animationsEnabled ? (active ? '100px' : '90px') : '100px', 
      py: 2,
      color: active ? '#fff' : customColor,
      bgcolor: active ? activeBg : 'transparent',
      display: 'flex',
      gap: 1.5,
      height: '100%',
      transition: animationsEnabled ? 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)' : 'none',
      position: 'relative',
      fontSize: animationsEnabled ? (active ? '1.1rem' : '1rem') : '1rem',
      '& .MuiButton-startIcon': {
        transition: animationsEnabled ? 'transform 0.3s ease' : 'none',
        transform: (animationsEnabled && active) ? 'scale(1.3)' : 'scale(1)',
      },
      '&:hover': {
        bgcolor: activeBg,
        color: '#fff',
        px: (animationsEnabled && !active) ? 5 : undefined,
        fontSize: (animationsEnabled && !active) ? '1.1rem' : undefined,
        '& .MuiButton-startIcon': {
          transform: animationsEnabled ? 'scale(1.3)' : 'none', 
        },
      },
      ...underlineEffect(active, active ? '#fff' : customColor)
    };
  };

  const SettingsButton = () => (
    <Button
      startIcon={<SettingsIcon />}
      sx={getNavButtonStyle("/settings", isDefault ? '#00e5ff' : '#fff', 'rgba(0, 229, 255, 0.15)')}
      onClick={() => navigate("/settings")}
    >
      Settings
    </Button>
  );

  return (
    <AppBar
      position="fixed"
      elevation={0}
      sx={{
        bgcolor: navBg,
        borderBottom: `1px solid ${borderColor}`,
        zIndex: (theme) => theme.zIndex.drawer + 1,
        transition: animationsEnabled ? 'background-color 0.4s ease' : 'none'
      }}
    >
      <Container maxWidth={false} sx={{ height: '100%', px: { xs: 2, md: 4 } }}>
        <Toolbar disableGutters sx={{ justifyContent: 'space-between', height: '80px' }}>
          
          <Box onClick={() => navigate("/")} sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 2, 
              cursor: "pointer", 
              position: 'relative',
              px: 2,
              py: 1,
              transition: animationsEnabled ? 'transform 0.3s ease' : 'none',
              '&:hover': { transform: animationsEnabled ? 'scale(1.05)' : 'none' },
              ...underlineEffect(isActive("/"))
          }}>
            <Box 
              component="img"
              src={catLogo}
              alt="AI Logo"
              sx={{
                height: '40px',
                width: 'auto',
                display: 'block',
                filter: isCyber ? 'none' : 'invert(1) brightness(1.2)'
              }}
            />
            <Typography variant="h5" sx={{ fontWeight: 900, letterSpacing: '-1px', color: navTextColor, textTransform: 'uppercase' }}>
              <span style={{ color: isDefault ? '#666' : 'rgba(255,255,255,0.5)' }}>Actual</span> Intelligence
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'stretch', height: '100%' }}>
            {!token ? (
              <>
                <Button startIcon={<LoginIcon />} sx={getNavButtonStyle("/login")} onClick={() => navigate("/login")}>
                  Log In
                </Button>
                <Divider orientation="vertical" flexItem sx={{ bgcolor: borderColor, width: '1px', my: 2 }} />
                <Button startIcon={<PersonAddIcon />} sx={getNavButtonStyle("/register")} onClick={() => navigate("/register")}>
                  Sign Up
                </Button>
                <Divider orientation="vertical" flexItem sx={{ bgcolor: borderColor, width: '1px', my: 2 }} />
                <SettingsButton />
              </>
            ) : (
              <>
                <Button startIcon={<ForumIcon />} sx={getNavButtonStyle("/chat")} onClick={() => navigate("/chat")}>
                  My Chats
                </Button>

                <Divider orientation="vertical" flexItem sx={{ bgcolor: borderColor, width: '1px', my: 2 }} />

                <Button startIcon={<PsychologyIcon />} sx={getNavButtonStyle("/tasks/claim")} onClick={() => navigate("/tasks/claim")}>
                  Task List
                </Button>

                <Divider orientation="vertical" flexItem sx={{ bgcolor: borderColor, width: '1px', my: 2 }} />

                <Button
                  startIcon={<TokenIcon sx={{ color: '#FFD700' }} />}
                  sx={getNavButtonStyle("/tokens", '#FFD700', 'rgba(255, 215, 0, 0.15)')}
                  onClick={() => navigate("/tokens")}
                >
                  {balance} ◈
                </Button>

                <Divider orientation="vertical" flexItem sx={{ bgcolor: borderColor, width: '1px', my: 2 }} />

                <SettingsButton />

                <Divider orientation="vertical" flexItem sx={{ bgcolor: borderColor, width: '1px', my: 2 }} />

                <Button
                  startIcon={<LogoutIcon />}
                  sx={getNavButtonStyle(null, logoutColor, `${logoutColor}26`)}
                  onClick={logout}
                >
                  Logout
                </Button>
              </>
            )}
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  );
}

export default Navbar;