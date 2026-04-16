import { useNavigate } from "react-router-dom";
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

function Navbar() {
  const navigate = useNavigate();
  const token = localStorage.getItem("token");

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

  const brandStyle = {
    cursor: "pointer", 
    fontWeight: 900, 
    letterSpacing: '-1px',
    color: '#fff',
    textTransform: 'uppercase',
    position: 'relative',
    transition: 'all 0.3s ease',
    display: 'inline-block',
    px: 1,
    py: 0.5,
    '&:hover': {
      transform: 'scale(1.05)',
      color: '#fff',
    },
    ...underlineEffect,
    '&::after': {
        ...underlineEffect['&::after'],
        height: '3px',
        bottom: -2
    }
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
      <Container maxWidth="lg">
        <Toolbar disableGutters sx={{ justifyContent: 'space-between', height: '64px' }}>
          
          <Box onClick={() => navigate("/")} sx={{ display: 'flex', alignItems: 'center' }}>
            <Typography variant="h6" sx={brandStyle}>
              Actual Intelligence
            </Typography>
          </Box>

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
                  startIcon={<TokenIcon />}
                  sx={navButtonStyle}
                  onClick={() => navigate("/tokens")}
                >
                  Token
                </Button>

                <Divider orientation="vertical" flexItem sx={{ bgcolor: '#333', width: '1px', my: 2 }} />

                <Button
                  startIcon={<LogoutIcon />}
                  sx={{ 
                    ...navButtonStyle, 
                    color: '#ff5252', 
                    '&::after': { ...underlineEffect['&::after'], bgcolor: '#ff5252' },
                    '&:hover': { color: '#ff1744', bgcolor: '#1a0000' } 
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