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
  IconButton,
  useTheme
} from "@mui/material";

// Icons
import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';
import MotionPhotosOffIcon from '@mui/icons-material/MotionPhotosOff';

const BACKEND_URL = "http://localhost:5000";

function Login() {
  const navigate = useNavigate();
  const theme = useTheme();
  const isDarkMode = theme.palette.mode === 'dark';

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState({});
  const [mounted, setMounted] = useState(false);
  
  const [animationsEnabled, setAnimationsEnabled] = useState(localStorage.getItem("ui-animations") !== "false");

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
    if (Object.keys(tempErrors).length > 0) { setErrors(tempErrors); return; }

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
      if (lowerMsg.includes("user") || lowerMsg.includes("email")) setErrors({ email: msg });
      else if (lowerMsg.includes("password")) setErrors({ password: msg });
      else setErrors({ general: msg });
    }
  };

  const handleClickShowPassword = () => setShowPassword((show) => !show);

  const inputStyles = {
    mb: 2,
    '& .MuiOutlinedInput-root': {
      borderRadius: '0px',
      backgroundColor: theme.palette.background.paper,
      '& fieldset': { borderWidth: '2px', borderColor: isDarkMode ? 'rgba(255,255,255,0.1)' : '#eee' },
      '&:hover fieldset': { borderColor: theme.palette.primary.main },
      '&.Mui-focused fieldset': { borderColor: theme.palette.text.primary, borderWidth: '2px' },
    },
    '& .MuiFormHelperText-root': {
      position: { md: 'absolute' }, left: { md: '100%' }, top: { md: '50%' },
      transform: { md: 'translateY(-50%)' }, width: { md: 'max-content' },
      ml: { md: 2 }, fontWeight: 800, textTransform: 'uppercase', fontSize: '0.7rem',
      color: `${theme.palette.error.main} !important`,
    }
  };

  const actionButtonStyle = (isPrimary) => ({
    py: 1.5,
    borderRadius: '0px',
    textTransform: 'uppercase',
    fontSize: '0.9rem',
    fontWeight: 900,
    letterSpacing: '1px',
    bgcolor: isPrimary ? theme.palette.text.primary : 'transparent',
    color: isPrimary ? theme.palette.background.default : theme.palette.text.primary,
    border: `2px solid ${theme.palette.text.primary}`,
    transition: animationsEnabled ? 'all 0.2s ease' : 'none',
    '&:hover': {
      bgcolor: theme.palette.text.primary, 
      color: theme.palette.background.default,
      transform: animationsEnabled ? 'translateY(-2px)' : 'none',
      boxShadow: animationsEnabled ? `4px 4px 0px ${isDarkMode ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'}` : 'none',
    }
  });

  const fadeSlide = (delay = 0) => {
    if (!animationsEnabled) return {};
    return {
      opacity: mounted ? 1 : 0,
      transform: mounted ? 'translateX(0px)' : 'translateX(-20px)',
      transition: `all 0.5s cubic-bezier(0.16, 1, 0.3, 1)`,
      transitionDelay: `${delay}ms`
    };
  };

  return (
    <Container maxWidth="xs" sx={{ overflow: 'visible' }}>
      <Box sx={{ mt: 12, display: 'flex', flexDirection: 'column', alignItems: 'center', pb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 900, mb: 1, textTransform: 'uppercase', color: theme.palette.text.primary, ...fadeSlide(0) }}>
          Login
        </Typography>
        <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 4, color: theme.palette.text.secondary, ...fadeSlide(50) }}>
          Access your professional identity
        </Typography>

        <Box component="form" onSubmit={handleLogin} sx={{ width: '100%' }}>
          <TextField placeholder="EMAIL ADDRESS" fullWidth value={email} onChange={(e) => setEmail(e.target.value)} error={!!errors.email} helperText={errors.email} sx={{ ...inputStyles, ...fadeSlide(150) }} inputProps={{ style: { fontWeight: 700, textTransform: 'uppercase' }}} />
          <TextField placeholder="PASSWORD" type={showPassword ? 'text' : 'password'} fullWidth value={password} onChange={(e) => setPassword(e.target.value)} error={!!errors.password} helperText={errors.password} sx={{ ...inputStyles, mb: 3, ...fadeSlide(200) }}
            slotProps={{ input: { endAdornment: (
              <InputAdornment position="end">
                <IconButton onClick={handleClickShowPassword} edge="end" sx={{ color: theme.palette.text.primary }}>
                  {showPassword ? <VisibilityOff /> : <Visibility />}
                </IconButton>
              </InputAdornment>
            )}}}
          />

          {errors.general && <Typography variant="caption" sx={{ color: theme.palette.error.main, fontWeight: 900, mb: 2, display: 'block', textAlign: 'center', textTransform: 'uppercase' }}>{errors.general}</Typography>}

          <Button variant="contained" fullWidth type="submit" disableElevation sx={{ ...actionButtonStyle(true), ...fadeSlide(250) }}>
            Log In
          </Button>

          <Divider sx={{ my: 4, fontWeight: 800, textTransform: 'uppercase', color: theme.palette.text.disabled, ...fadeSlide(300) }}>or</Divider>

          <Button variant="outlined" fullWidth onClick={() => navigate("/register")} disableElevation sx={{ ...actionButtonStyle(false), ...fadeSlide(350) }}>
            Create Account
          </Button>

          {!animationsEnabled && (
            <Box sx={{ mt: 4, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1, opacity: 0.5 }}>
              <MotionPhotosOffIcon fontSize="small" />
              <Typography variant="caption" sx={{ fontWeight: 700, textTransform: 'uppercase' }}>Reduced Motion Mode Active</Typography>
            </Box>
          )}
        </Box>
      </Box>
    </Container>
  );
}

export default Login;