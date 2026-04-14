import { useNavigate } from "react-router-dom";
import { AppBar, Toolbar, Button, Typography, Box, Container } from "@mui/material";

function Navbar() {
  const navigate = useNavigate();
  const token = localStorage.getItem("token");

  const logout = () => {
    localStorage.clear();
    navigate("/login");
  };

  const buttonBase = {
    textTransform: 'none',
    borderRadius: '8px',
    fontWeight: 600,
    px: 2.5,
    transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
    '&:hover': { transform: 'translateY(-2px)' },
    '&:active': { transform: 'translateY(0)' }
  };

  return (
    <AppBar
      position="fixed"
      elevation={0}
      sx={{
        bgcolor: '#0a0a0a',
        borderBottom: '1px solid #222'
      }}
    >
      <Container maxWidth="lg" disableGutters>
        <Toolbar
          sx={{
            justifyContent: 'space-between',
            px: { xs: 2, lg: 0 },
            minHeight: '64px'
          }}
        >
          <Typography
            variant="h6"
            sx={{ cursor: "pointer", fontWeight: 900, color: '#fff' }}
            onClick={() => navigate("/")}
          >
            Actual Intelligence
          </Typography>

          <Box sx={{ display: 'flex', gap: 1.5 }}>
            {!token ? (
              <>
                <Button
                  sx={{ ...buttonBase, color: '#fff', bgcolor: 'rgba(255,255,255,0.1)' }}
                  onClick={() => navigate("/login")}
                >
                  Log In
                </Button>
                <Button
                  variant="contained"
                  disableElevation
                  sx={{ ...buttonBase, bgcolor: '#fff', color: '#000' }}
                  onClick={() => navigate("/register")}
                >
                  Sign Up
                </Button>
              </>
            ) : (
              <>
                <Button
                  sx={{ ...buttonBase, color: '#ff5252' }}
                  onClick={logout}
                >
                  Logout
                </Button>
                <Button
                  sx={{ ...buttonBase, color: '#ff5252' }}
                  onClick={logout}
                >
                  Token Thing Here!
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