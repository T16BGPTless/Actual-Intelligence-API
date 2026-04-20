import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

// MUI
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
} from '@mui/material';

// Icons
import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';

const BACKEND_URL = "";

function Register() {
  const navigate = useNavigate();
  const theme = useTheme();
  const isDarkMode = theme.palette.mode === 'dark';

  const [formData, setFormData] = useState({ name: '', username: '', email: '', password: '', confirmPassword: '' });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [errors, setErrors] = useState({});
  const [mounted, setMounted] = useState(false);
  const [animationsEnabled, setAnimationsEnabled] = useState(localStorage.getItem("ui-animations") !== "false");

  useEffect(() => {
    const timer = setTimeout(() => setMounted(true), 50);
    return () => clearTimeout(timer);
  }, []);

  const handleChange = (prop) => (e) => {
    setFormData({ ...formData, [prop]: e.target.value });
    if (errors[prop]) setErrors({ ...errors, [prop]: null });
  };

  const registerUser = async (e) => {
    e.preventDefault();
    setErrors({});
    let tempErrors = {};
    if (!formData.name) tempErrors.name = "Required";
    if (formData.password !== formData.confirmPassword) tempErrors.confirmPassword = "Mismatch";
    if (Object.keys(tempErrors).length > 0) { setErrors(tempErrors); return; }

    try {
      const res = await axios.post(`${BACKEND_URL}/v1/auth/register`, formData);
      localStorage.setItem('token', res.data.accessToken);
      localStorage.setItem('username', res.data.user.username);
      navigate('/');
    } catch (err) {
      setErrors({ general: err.response?.data?.message || 'Failed' });
    }
  };

  const inputStyles = {
    mb: 2,
    '& .MuiOutlinedInput-root': {
      borderRadius: '0px',
      backgroundColor: theme.palette.background.paper,
      '& fieldset': { borderWidth: '2px', borderColor: isDarkMode ? 'rgba(255,255,255,0.1)' : '#eee' },
      '&:hover fieldset': { borderColor: theme.palette.primary.main },
      '&.Mui-focused fieldset': { borderColor: theme.palette.text.primary, borderWidth: '2px' },
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
    <Container maxWidth="xs">
      <Box sx={{ mt: 8, display: 'flex', flexDirection: 'column', alignItems: 'center', pb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 900, mb: 1, textTransform: 'uppercase', color: theme.palette.text.primary, ...fadeSlide(0) }}>Register</Typography>
        <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 4, color: theme.palette.text.secondary, ...fadeSlide(50) }}>Create Account</Typography>

        <Box component="form" onSubmit={registerUser} sx={{ width: '100%' }}>
          <TextField placeholder="FULL NAME" fullWidth onChange={handleChange('name')} sx={{ ...inputStyles, ...fadeSlide(150) }} />
          <TextField placeholder="USERNAME" fullWidth onChange={handleChange('username')} sx={{ ...inputStyles, ...fadeSlide(200) }} />
          <TextField placeholder="EMAIL ADDRESS" fullWidth onChange={handleChange('email')} sx={{ ...inputStyles, ...fadeSlide(250) }} />
          <TextField placeholder="PASSWORD" type={showPassword ? 'text' : 'password'} fullWidth onChange={handleChange('password')} sx={{ ...inputStyles, ...fadeSlide(300) }}
            slotProps={{ input: { endAdornment: (
              <InputAdornment position="end">
                <IconButton onClick={() => setShowPassword(!showPassword)} sx={{ color: theme.palette.text.primary }}>{showPassword ? <VisibilityOff /> : <Visibility />}</IconButton>
              </InputAdornment>
            )}}}
          />
          <TextField placeholder="CONFIRM PASSWORD" type={showConfirmPassword ? 'text' : 'password'} fullWidth onChange={handleChange('confirmPassword')} sx={{ ...inputStyles, mb: 3, ...fadeSlide(350) }}
            slotProps={{ input: { endAdornment: (
              <InputAdornment position="end">
                <IconButton onClick={() => setShowConfirmPassword(!showConfirmPassword)} sx={{ color: theme.palette.text.primary }}>{showConfirmPassword ? <VisibilityOff /> : <Visibility />}</IconButton>
              </InputAdornment>
            )}}}
          />

          <Button variant="contained" fullWidth type="submit" disableElevation sx={{ ...actionButtonStyle(true), ...fadeSlide(400) }}>Sign Up</Button>
          <Divider sx={{ my: 4, fontWeight: 800, textTransform: 'uppercase', color: theme.palette.text.disabled, ...fadeSlide(450) }}>or</Divider>
          
          <Box sx={{ display: 'flex', gap: 2, ...fadeSlide(500) }}>
            <Button variant="outlined" fullWidth onClick={() => navigate("/login")} sx={actionButtonStyle(false)}>Log In</Button>
          </Box>
        </Box>
      </Box>
    </Container>
  );
}

export default Register;