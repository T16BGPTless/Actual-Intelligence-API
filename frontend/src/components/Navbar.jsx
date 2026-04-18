import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { 
  AppBar, 
  Toolbar, 
  Button, 
  Typography, 
  Box, 
  Container, 
  Divider 
} from "@mui/material";

// Icons
import LoginIcon from '@mui/icons-material/Login';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import LogoutIcon from '@mui/icons-material/Logout';
import TokenIcon from '@mui/icons-material/Token';
import ForumIcon from '@mui/icons-material/Forum';
import PsychologyIcon from '@mui/icons-material/Psychology';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';

// Assets
import catLogo from "../assets/cat1.png";

function Navbar() {
  const navigate = useNavigate();
  const token = localStorage.getItem("token");
  const email = localStorage.getItem("email"); 
  const [balance, setBalance] = useState(0);

  useEffect(() => {
    const fetchBalance = async () => {
      if (token) {
        try {
          const res = await axios.get(`http://localhost:5000/v1/tokens`, {
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
    const interval = setInterval(fetchBalance, 30000);
    return () => clearInterval(interval);
  }, [token, email]);

  const logout = () => {
    localStorage.clear();
    navigate("/login");
  };

  const underlineEffect = {
    '&::after': {
      content: '""',
      position: 'absolute',
      bottom: 0,
      left: 0,
      width: '0%',
      height: '2px',
      bgcolor: '#fff',
      transition: 'width 0.3s ease-in-out',
    },
    '&:hover::after': {
      width: '100%',
    }
  };

  const navButtonStyle = {
    textTransform: 'none',
    borderRadius: 0,
    fontWeight: 600,
    px: 4,
    py: 2,
    color: '#eee',
    display: 'flex',
    gap: 1.5,
    height: '100%',
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    position: 'relative',
    '& .MuiButton-startIcon': {
      transition: 'transform 0.3s ease',
    },
    '&:hover': {
      bgcolor: '#1a1a1a',
      color: '#fff',
      fontSize: '1.05rem',
      '& .MuiButton-startIcon': {
        transform: 'scale(1.2)',
      },
    },
    ...underlineEffect
  };

  const brandContainerStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: 1.5, 
    cursor: "pointer", 
    position: 'relative',
    px: 1,
    py: 0.5,
    transition: 'transform 0.3s ease',
    '&:hover': {
      transform: 'scale(1.02)', 
    },
    '&::after': {
      content: '""',
      position: 'absolute',
      bottom: -2,
      left: 0,
      width: '0%',
      height: '3px',
      bgcolor: '#fff',
      transition: 'width 0.3s ease-in-out',
    },
    '&:hover::after': {
      width: '100%',
    }
  };

  const brandTextStyle = {
    fontWeight: 900, 
    letterSpacing: '-1px',
    color: '#fff',
    textTransform: 'uppercase',
    display: 'inline-block',
  };

  return (
    <AppBar
      position="fixed"
      elevation={0}
      sx={{
        bgcolor: '#000',
        borderBottom: '1px solid #333',
        zIndex: (theme) => theme.zIndex.drawer + 1
      }}
    >
      <Container maxWidth="lg" sx={{ height: '100%' }}>
        <Toolbar disableGutters sx={{ justifyContent: 'space-between', height: '64px' }}>
          
          {/* Brand/Logo Section */}
          <Box onClick={() => navigate("/")} sx={brandContainerStyle}>
            <Box 
              component="img"
              src={catLogo}
              alt="AI Logo"
              sx={{
                height: '32px', 
                width: 'auto',
                display: 'block',
                filter: 'invert(1) brightness(1.2)'
              }}
            />
            <Typography variant="h6" sx={brandTextStyle}>
              <span style={{ color: '#666' }}>Actual</span> Intelligence
            </Typography>
          </Box>

          {/* Nav Links Section */}
          <Box sx={{ 
            display: 'flex', 
            alignItems: 'stretch',
            bgcolor: '#000', 
            height: '100%' 
          }}>
            {!token ? (
              <>
                <Button
                  startIcon={<LoginIcon />}
                  sx={navButtonStyle}
                  onClick={() => navigate("/login")}
                >
                  Log In
                </Button>

                <Divider orientation="vertical" flexItem sx={{ bgcolor: '#333', width: '1px', my: 2 }} />

                <Button
                  startIcon={<PersonAddIcon />}
                  sx={navButtonStyle}
                  onClick={() => navigate("/register")}
                >
                  Sign Up
                </Button>
              </>
            ) : (
              <>
                <Button
                  startIcon={<ForumIcon />}
                  sx={navButtonStyle}
                  onClick={() => navigate("/chat/new")}
                >
                  My Chats
                </Button>

                <Divider orientation="vertical" flexItem sx={{ bgcolor: '#333', width: '1px', my: 2 }} />

                <Button
                  startIcon={<PsychologyIcon />}
                  sx={navButtonStyle}
                  onClick={() => navigate("/tasks/claim")}
                >
                  Task List
                </Button>

                <Divider orientation="vertical" flexItem sx={{ bgcolor: '#333', width: '1px', my: 2 }} />

                <Button
                  startIcon={<AccountCircleIcon />}
                  sx={navButtonStyle}
                  onClick={() => navigate("/profile")}
                >
                  Profile
                </Button>

                <Divider orientation="vertical" flexItem sx={{ bgcolor: '#333', width: '1px', my: 2 }} />

                <Button
                  startIcon={<TokenIcon sx={{ color: '#FFD700' }} />}
                  sx={{ 
                    ...navButtonStyle, 
                    color: '#FFD700', 
                    fontWeight: 800,
                    '&::after': { ...underlineEffect['&::after'], bgcolor: '#FFD700' },
                    '&:hover': { 
                      ...navButtonStyle['&:hover'],
                      color: '#FFF176', 
                      bgcolor: '#1a1a00',
                    } 
                  }}
                  onClick={() => navigate("/tokens")}
                >
                  {balance} ◈
                </Button>

                <Divider orientation="vertical" flexItem sx={{ bgcolor: '#333', width: '1px', my: 2 }} />

                <Button
                  startIcon={<LogoutIcon />}
                  sx={{ 
                    ...navButtonStyle, 
                    color: '#ff5252', 
                    '&::after': { ...underlineEffect['&::after'], bgcolor: '#ff5252' },
                    '&:hover': { 
                      ...navButtonStyle['&:hover'],
                      color: '#ff1744', 
                      bgcolor: '#1a0000',
                    } 
                  }}
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