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

  const navButtonStyle = {
    textTransform: 'none',
    borderRadius: 0,
    fontWeight: 600,
    px: 4,
    py: 2,
    color: '#eee',
    display: 'flex',
    gap: 1.5,
    transition: 'all 0.3s ease',
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
      '&::after': {
        content: '""',
        position: 'absolute',
        bottom: 0,
        left: 0,
        width: '100%',
        height: '2px',
        bgcolor: '#fff',
      }
    }
  };

  return (
    <AppBar
      position="fixed"
      elevation={0}
      sx={{
        bgcolor: '#000',
        borderBottom: '1px solid #333'
      }}
    >
      <Container maxWidth="lg">
        <Toolbar disableGutters sx={{ justifyContent: 'space-between' }}>
          
          <Typography
            variant="h6"
            sx={{ 
              cursor: "pointer", 
              fontWeight: 900, 
              letterSpacing: '-0.5px',
              color: '#fff' 
            }}
            onClick={() => navigate("/")}
          >
            Actual Intelligence
          </Typography>

          <Box sx={{ 
            display: 'flex', 
            alignItems: 'stretch',
            bgcolor: '#000', 
            height: '64px' 
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

                <Divider orientation="vertical" flexItem sx={{ bgcolor: '#333', width: '1px' }} />

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
                  onClick={() => console.log("Token action")}
                >
                  Token
                </Button>

                <Divider orientation="vertical" flexItem sx={{ bgcolor: '#333', width: '1px' }} />

                <Button
                  startIcon={<LogoutIcon />}
                  sx={{ ...navButtonStyle, color: '#ff5252', '&:hover': { color: '#ff1744', bgcolor: '#1a0000' } }}
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