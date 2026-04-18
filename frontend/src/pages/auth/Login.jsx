import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

// MUI Components
import {
  TextField,
  Button,
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
  const [errors, setErrors] = useState({});
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setMounted(true), 50);
    return () => clearTimeout(timer);
  }, []);

  const handleLogin = async (e) => {
    e.preventDefault();
    setErrors({});

    let tempErrors = {};
    if (!email) tempErrors.email = "Email is required";
    if (!password) tempErrors.password = "Password is required";

    if (Object.keys(tempErrors).length > 0) {
      setErrors(tempErrors);
      return;
    }

    try {
      const res = await axios.post(`${BACKEND_URL}/v1/auth/login`, { email, password });
      
      const { accessToken, user } = res.data;

      localStorage.setItem("token", accessToken);
      localStorage.setItem("username", user.username);
      localStorage.setItem("name", user.name);
      localStorage.setItem("email", user.email);

      navigate("/");
      
    } catch (err) {
      const msg = err.response?.data?.message || "Login failed";
      const lowerMsg = msg.toLowerCase();

      if (lowerMsg.includes("user") || lowerMsg.includes("email")) {
        setErrors({ email: msg });
      } else if (lowerMsg.includes("password")) {
        setErrors({ password: msg });
      } else {
        setErrors({ general: msg });
      }
    }
  };

  const handleClickShowPassword = () => setShowPassword((show) => !show);

  const inputStyles = {
    mb: 2,
    position: 'relative',
    '& .MuiOutlinedInput-root': {
      borderRadius: '0px',
      backgroundColor: '#ffffff',
      '& fieldset': { borderWidth: '2px', borderColor: '#eee' },
      '&:hover fieldset': { borderColor: '#bbb' },
      '&.Mui-focused fieldset': { borderColor: 'black', borderWidth: '2px' },
      '&.Mui-error fieldset': { borderColor: '#ff1744' },
    },
    '& .MuiFormHelperText-root': {
      position: { md: 'absolute' },
      left: { md: '100%' },
      top: { md: '50%' },
      transform: { md: 'translateY(-50%)' },
      width: { md: 'max-content' },
      ml: { md: 2 },
      fontWeight: 800,
      textTransform: 'uppercase',
      fontSize: '0.7rem',
      color: '#ff1744 !important',
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
    <Container maxWidth="xs" sx={{ overflow: 'visible' }}>
      <Box sx={{ mt: 12, display: 'flex', flexDirection: 'column', alignItems: 'center', pb: 4 }}>
        
        <Typography variant="h4" sx={{ fontWeight: 900, mb: 1, textTransform: 'uppercase', letterSpacing: '-1px', ...fadeSlide(0) }}>
          Login
        </Typography>

        <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 4, color: '#666', ...fadeSlide(50) }}>
          Access your professional identity
        </Typography>

        <Box component="form" onSubmit={handleLogin} sx={{ width: '100%' }}>
          
          <TextField
            placeholder="EMAIL ADDRESS"
            fullWidth
            value={email}
            onChange={(e) => {
                setEmail(e.target.value);
                if(errors.email) setErrors({...errors, email: null});
            }}
            error={!!errors.email}
            helperText={errors.email}
            sx={{ ...inputStyles, ...fadeSlide(150) }}
          />

          <TextField
            placeholder="PASSWORD"
            type={showPassword ? 'text' : 'password'}
            fullWidth
            value={password}
            onChange={(e) => {
                setPassword(e.target.value);
                if(errors.password) setErrors({...errors, password: null});
            }}
            error={!!errors.password}
            helperText={errors.password}
            sx={{ ...inputStyles, mb: 3, ...fadeSlide(200) }}
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      aria-label="toggle password visibility"
                      onClick={handleClickShowPassword}
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

          {errors.general && (
            <Typography variant="caption" sx={{ color: '#ff1744', fontWeight: 900, mb: 2, display: 'block', textAlign: 'center', textTransform: 'uppercase' }}>
              {errors.general}
            </Typography>
          )}

          <Button variant="contained" fullWidth type="submit" disableElevation sx={{ ...actionButtonStyle(true), ...fadeSlide(250) }}>
            Log In
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