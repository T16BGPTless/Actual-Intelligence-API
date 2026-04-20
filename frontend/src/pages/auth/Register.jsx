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
  useTheme,
  Alert,
  Collapse,
  CircularProgress
} from '@mui/material';

// Icons
import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;

function Register() {
  const navigate = useNavigate();
  const theme = useTheme();
  const isDarkMode = theme.palette.mode === 'dark';

  const [formData, setFormData] = useState({ name: '', username: '', email: '', password: '', confirmPassword: '' });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  
  // UI States
  const [errors, setErrors] = useState({});
  const [mounted, setMounted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [animationsEnabled] = useState(localStorage.getItem("ui-animations") !== "false");

  useEffect(() => {
    const timer = setTimeout(() => setMounted(true), 50);
    return () => clearTimeout(timer);
  }, []);

  const handleChange = (prop) => (e) => {
    setFormData({ ...formData, [prop]: e.target.value });
    if (errors[prop]) setErrors({ ...errors, [prop]: null });
    if (errors.general) setErrors({ ...errors, general: null });
  };

  const registerUser = async (e) => {
    e.preventDefault();
    setErrors({});
    
    // 1. Validation
    let tempErrors = {};
    if (!formData.name) tempErrors.name = "Full name is required";
    if (!formData.username) tempErrors.username = "Username is required";
    if (!formData.email) tempErrors.email = "Email is required";
    if (!formData.password) tempErrors.password = "Password is required";
    if (formData.password !== formData.confirmPassword) tempErrors.confirmPassword = "Passwords mismatch";
    
    if (Object.keys(tempErrors).length > 0) { 
      setErrors(tempErrors); 
      return; 
    }

    setLoading(true);

    try {
      const res = await axios.post(`${BACKEND_URL}/v1/auth/register`, {
        email: formData.email,
        password: formData.password,
        name: formData.name,
        username: formData.username
      });

      // 3. Success Persistence
      localStorage.setItem('token', res.data.accessToken);
      localStorage.setItem('username', res.data.user.username);
      localStorage.setItem('email', res.data.user.email);
      navigate('/');
    } catch (err) {
      setErrors({ general: err.response?.data?.message || 'Registration failed. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  // Styles
  const inputStyles = (field) => ({
    mb: 2,
    '& .MuiOutlinedInput-root': {
      borderRadius: '0px',
      backgroundColor: theme.palette.background.paper,
      '& fieldset': { 
        borderWidth: '2px', 
        borderColor: errors[field] ? theme.palette.error.main : (isDarkMode ? 'rgba(255,255,255,0.1)' : '#eee') 
      },
      '&:hover fieldset': { borderColor: theme.palette.primary.main },
      '&.Mui-focused fieldset': { borderColor: theme.palette.text.primary, borderWidth: '2px' },
    }
  });

  const buttonBase = (isPrimary) => ({
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
    opacity: loading ? 0.7 : 1,
    '&:hover': {
      bgcolor: theme.palette.text.primary, 
      color: theme.palette.background.default,
      transform: (animationsEnabled && !loading) ? 'translateY(-2px)' : 'none',
      boxShadow: (animationsEnabled && !loading) ? `4px 4px 0px ${isDarkMode ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'}` : 'none',
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

        <Collapse in={!!errors.general} sx={{ width: '100%', mb: 2 }}>
          <Alert severity="error" variant="filled" sx={{ borderRadius: 0, fontWeight: 800 }}>
            {errors.general}
          </Alert>
        </Collapse>

        <Box component="form" onSubmit={registerUser} sx={{ width: '100%' }}>
          <TextField 
            placeholder="FULL NAME" 
            fullWidth 
            disabled={loading}
            error={!!errors.name}
            helperText={errors.name}
            onChange={handleChange('name')} 
            sx={{ ...inputStyles('name'), ...fadeSlide(150) }} 
          />
          <TextField 
            placeholder="USERNAME" 
            fullWidth 
            disabled={loading}
            error={!!errors.username}
            helperText={errors.username}
            onChange={handleChange('username')} 
            sx={{ ...inputStyles('username'), ...fadeSlide(200) }} 
          />
          <TextField 
            placeholder="EMAIL ADDRESS" 
            fullWidth 
            disabled={loading}
            error={!!errors.email}
            helperText={errors.email}
            onChange={handleChange('email')} 
            sx={{ ...inputStyles('email'), ...fadeSlide(250) }} 
          />
          <TextField 
            placeholder="PASSWORD" 
            type={showPassword ? 'text' : 'password'} 
            fullWidth 
            disabled={loading}
            error={!!errors.password}
            helperText={errors.password}
            onChange={handleChange('password')} 
            sx={{ ...inputStyles('password'), ...fadeSlide(300) }}
            slotProps={{ input: { endAdornment: (
              <InputAdornment position="end">
                <IconButton onClick={() => setShowPassword(!showPassword)} sx={{ color: theme.palette.text.primary }} disabled={loading}>
                  {showPassword ? <VisibilityOff /> : <Visibility />}
                </IconButton>
              </InputAdornment>
            )}}}
          />
          <TextField 
            placeholder="CONFIRM PASSWORD" 
            type={showConfirmPassword ? 'text' : 'password'} 
            fullWidth 
            disabled={loading}
            error={!!errors.confirmPassword}
            helperText={errors.confirmPassword}
            onChange={handleChange('confirmPassword')} 
            sx={{ ...inputStyles('confirmPassword'), mb: 3, ...fadeSlide(350) }}
            slotProps={{ input: { endAdornment: (
              <InputAdornment position="end">
                <IconButton onClick={() => setShowConfirmPassword(!showConfirmPassword)} sx={{ color: theme.palette.text.primary }} disabled={loading}>
                  {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                </IconButton>
              </InputAdornment>
            )}}}
          />

          <Button 
            variant="contained" 
            fullWidth 
            type="submit" 
            disableElevation 
            disabled={loading}
            sx={{ ...buttonBase(true), ...fadeSlide(400) }}
          >
            {loading ? (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <CircularProgress size={20} color="inherit" />
                PROCESSING...
              </Box>
            ) : (
              "Sign Up"
            )}
          </Button>

          <Divider sx={{ my: 4, fontWeight: 800, textTransform: 'uppercase', color: theme.palette.text.disabled, ...fadeSlide(450) }}>or</Divider>
          
          <Box sx={{ display: 'flex', gap: 2, ...fadeSlide(500) }}>
            <Button variant="outlined" fullWidth onClick={() => navigate("/login")} sx={buttonBase(false)} disabled={loading}>Log In</Button>
          </Box>
        </Box>
      </Box>
    </Container>
  );
}

export default Register;