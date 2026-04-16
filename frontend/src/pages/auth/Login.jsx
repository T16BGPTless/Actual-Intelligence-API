import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

// MUI Components
import {
  TextField,
  Button,
  Alert,
  Box,
  Container,
  Typography,
  Divider,
  InputAdornment,
  IconButton
} from "@mui/material";

// Icons
import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';

const BACKEND_URL = "http://localhost:5000";

function Login() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setMounted(true), 50);
    return () => clearTimeout(timer);
  }, []);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const res = await axios.post(`${BACKEND_URL}/v1/auth/login`, { email, password });
      localStorage.setItem("token", res.data.accessToken);
      localStorage.setItem("email", email);
      navigate("/");
    } catch (err) {
      setError(err.response?.data?.message || "Login failed");
    }
  };

  const handleClickShowPassword = () => setShowPassword((show) => !show);
  const handleMouseDownPassword = (event) => event.preventDefault();
  const handleMouseUpPassword = (event) => event.preventDefault();

  const inputStyles = {
    mb: 2,
    '& .MuiOutlinedInput-root': {
      borderRadius: '0px',
      backgroundColor: '#ffffff',
      '& fieldset': { borderWidth: '2px', borderColor: '#eee' },
      '&:hover fieldset': { borderColor: '#bbb' },
      '&.Mui-focused fieldset': { borderColor: 'black', borderWidth: '2px' },
    }
  };

  const actionButtonStyle = (isPrimary) => ({
    py: 1.5,
    borderRadius: '0px',
    textTransform: 'uppercase',
    fontSize: '0.9rem',
    fontWeight: 900,
    letterSpacing: '1px',
    bgcolor: isPrimary ? 'black' : 'transparent',
    color: isPrimary ? 'white' : 'black',
    border: '2px solid black',
    transition: 'all 0.2s ease',
    '&:hover': {
      bgcolor: isPrimary ? '#333' : 'black',
      color: 'white',
      transform: 'translateY(-2px)',
      boxShadow: '4px 4px 0px rgba(0,0,0,0.1)',
    }
  });

  const fadeSlide = (delay = 0) => ({
    opacity: mounted ? 1 : 0,
    transform: mounted ? 'translateX(0px)' : 'translateX(-20px)',
    transition: `all 0.5s cubic-bezier(0.16, 1, 0.3, 1)`,
    transitionDelay: `${delay}ms`
  });

  return (
    <Container maxWidth="xs">
      <Box sx={{ mt: 12, display: 'flex', flexDirection: 'column', alignItems: 'center', pb: 4 }}>
        
        <Typography variant="h4" sx={{ fontWeight: 900, mb: 1, textTransform: 'uppercase', letterSpacing: '-1px', ...fadeSlide(0) }}>
          Login
        </Typography>

        <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 4, color: '#666', ...fadeSlide(50) }}>
          Sign in to your account
        </Typography>

        {error && (
          <Alert severity="error" variant="filled" sx={{ width: '100%', mb: 3, borderRadius: '0px', bgcolor: 'black', ...fadeSlide(100) }}>
            {error}
          </Alert>
        )}

        {/* Keeping text fields without wrapping them in a dedicated FormControl */}
        <Box component="form" onSubmit={handleLogin} sx={{ width: '100%' }}>
          
          <TextField
            placeholder="EMAIL ADDRESS"
            fullWidth
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            sx={{ ...inputStyles, ...fadeSlide(150) }}
          />

          <TextField
            placeholder="PASSWORD"
            type={showPassword ? 'text' : 'password'}
            fullWidth
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            sx={{ ...inputStyles, mb: 3, ...fadeSlide(200) }}
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      aria-label={showPassword ? 'hide the password' : 'display the password'}
                      onClick={handleClickShowPassword}
                      onMouseDown={handleMouseDownPassword}
                      onMouseUp={handleMouseUpPassword}
                      edge="end"
                      sx={{ color: 'black' }}
                    >
                      {showPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              },
            }}
          />

          <Button variant="contained" fullWidth type="submit" disableElevation sx={{ ...actionButtonStyle(true), ...fadeSlide(250) }}>
            Sign In
          </Button>

          <Divider sx={{ my: 4, fontWeight: 800, textTransform: 'uppercase', ...fadeSlide(300) }}>or</Divider>

          <Button variant="outlined" fullWidth onClick={() => navigate("/register")} disableElevation sx={{ ...actionButtonStyle(false), ...fadeSlide(350) }}>
            Create Account
          </Button>

        </Box>
      </Box>
    </Container>
  );
}

export default Login;