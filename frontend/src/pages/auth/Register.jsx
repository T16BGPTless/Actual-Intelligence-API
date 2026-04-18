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
import BugReportIcon from '@mui/icons-material/BugReport';

const BACKEND_URL = "http://localhost:5000";

function Register() {
  const navigate = useNavigate();
  const theme = useTheme();
  const isDarkMode = theme.palette.mode === 'dark';

  const [formData, setFormData] = useState({
    name: '',
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  });

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [errors, setErrors] = useState({});
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setMounted(true), 50);
    return () => clearTimeout(timer);
  }, []);

  const handleChange = (prop) => (e) => {
    setFormData({ ...formData, [prop]: e.target.value });
    if (errors[prop]) {
      setErrors({ ...errors, [prop]: null });
    }
  };

  const handleDebugBypass = () => {
    const debugToken = `debug_session_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem('token', debugToken);
    localStorage.setItem('username', 'Debug_Cat');
    localStorage.setItem('email', 'debug_user@local.test');
    navigate('/');
  };

  const registerUser = async (e) => {
    e.preventDefault();
    setErrors({});

    let tempErrors = {};
    if (!formData.name) tempErrors.name = "Name is required";
    if (!formData.username) tempErrors.username = "Username is required";
    if (!formData.email) tempErrors.email = "Email is required";
    if (!formData.password) tempErrors.password = "Password is required";
    if (formData.password !== formData.confirmPassword) {
      tempErrors.confirmPassword = "Passwords do not match";
    }

    if (Object.keys(tempErrors).length > 0) {
      setErrors(tempErrors);
      return;
    }

    try {
      const res = await axios.post(`${BACKEND_URL}/v1/auth/register`, {
        email: formData.email,
        password: formData.password,
        name: formData.name,
        username: formData.username,
      });

      const { accessToken, user } = res.data;
      localStorage.setItem('token', accessToken);
      localStorage.setItem('username', user.username);
      localStorage.setItem('email', user.email);
      localStorage.setItem('name', user.name);

      navigate('/');
    } catch (err) {
      const msg = err.response?.data?.message || err.response?.data?.error || 'Registration failed';
      const lowerMsg = msg.toLowerCase();
      
      if (lowerMsg.includes("email")) {
        setErrors({ email: msg });
      } else if (lowerMsg.includes("username")) {
        setErrors({ username: msg });
      } else {
        setErrors({ general: msg });
      }
    }
  };

  const inputStyles = {
    mb: 2,
    position: 'relative',
    '& .MuiOutlinedInput-root': {
      borderRadius: '0px',
      backgroundColor: theme.palette.background.paper,
      '& fieldset': { 
        borderWidth: '2px', 
        borderColor: isDarkMode ? 'rgba(255,255,255,0.1)' : '#eee' 
      },
      '&:hover fieldset': { borderColor: theme.palette.primary.main },
      '&.Mui-focused fieldset': { 
        borderColor: theme.palette.text.primary, 
        borderWidth: '2px' 
      },
      '&.Mui-error fieldset': { borderColor: theme.palette.error.main },
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
    transition: 'all 0.2s ease',
    '&:hover': {
      bgcolor: isPrimary ? theme.palette.action.hover : theme.palette.text.primary,
      color: theme.palette.background.default,
      transform: 'translateY(-2px)',
      boxShadow: `4px 4px 0px ${isDarkMode ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'}`,
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
      <Box sx={{ mt: 8, display: 'flex', flexDirection: 'column', alignItems: 'center', pb: 4 }}>
        
        <Typography 
          variant="h4" 
          sx={{ 
            fontWeight: 900, 
            mb: 1, 
            textTransform: 'uppercase',
            color: theme.palette.text.primary,
            textShadow: isDarkMode ? `0 0 15px ${theme.palette.primary.main}44` : 'none',
            ...fadeSlide(0) 
          }}
        >
          Register
        </Typography>

        <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 4, color: theme.palette.text.secondary, ...fadeSlide(50) }}>
          Create a New Account
        </Typography>

        <Box component="form" onSubmit={registerUser} sx={{ width: '100%' }}>
          
          <TextField 
            placeholder="FULL NAME" 
            fullWidth 
            value={formData.name} 
            onChange={handleChange('name')} 
            error={!!errors.name}
            helperText={errors.name}
            sx={{ ...inputStyles, ...fadeSlide(150) }} 
            inputProps={{ style: { fontWeight: 700, textTransform: 'uppercase' }}}
          />

          <TextField 
            placeholder="USERNAME" 
            fullWidth 
            value={formData.username} 
            onChange={handleChange('username')} 
            error={!!errors.username}
            helperText={errors.username}
            sx={{ ...inputStyles, ...fadeSlide(200) }} 
            inputProps={{ style: { fontWeight: 700, textTransform: 'uppercase' }}}
          />

          <TextField 
            placeholder="EMAIL ADDRESS" 
            fullWidth 
            value={formData.email} 
            onChange={handleChange('email')} 
            error={!!errors.email}
            helperText={errors.email}
            sx={{ ...inputStyles, ...fadeSlide(250) }} 
            inputProps={{ style: { fontWeight: 700, textTransform: 'uppercase' }}}
          />
          
          <TextField 
            placeholder="PASSWORD" 
            type={showPassword ? 'text' : 'password'} 
            fullWidth 
            value={formData.password} 
            onChange={handleChange('password')} 
            error={!!errors.password}
            helperText={errors.password}
            sx={{ ...inputStyles, ...fadeSlide(300) }}
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton onClick={() => setShowPassword(!showPassword)} edge="end" sx={{ color: theme.palette.text.primary }}>
                      {showPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              },
            }}
          />

          <TextField 
            placeholder="CONFIRM PASSWORD" 
            type={showConfirmPassword ? 'text' : 'password'} 
            fullWidth 
            value={formData.confirmPassword} 
            onChange={handleChange('confirmPassword')} 
            error={!!errors.confirmPassword}
            helperText={errors.confirmPassword}
            sx={{ ...inputStyles, mb: 3, ...fadeSlide(350) }}
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton onClick={() => setShowConfirmPassword(!showConfirmPassword)} edge="end" sx={{ color: theme.palette.text.primary }}>
                      {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              },
            }}
          />

          {errors.general && (
            <Typography variant="caption" sx={{ color: theme.palette.error.main, fontWeight: 900, mb: 2, display: 'block', textAlign: 'center', textTransform: 'uppercase' }}>
              {errors.general}
            </Typography>
          )}

          <Button variant="contained" fullWidth type="submit" disableElevation sx={{ ...actionButtonStyle(true), ...fadeSlide(400) }}>
            Sign Up
          </Button>

          <Divider sx={{ 
            my: 4, 
            fontWeight: 800, 
            textTransform: 'uppercase',
            color: theme.palette.text.disabled,
            '&::before, &::after': { borderColor: theme.palette.divider },
            ...fadeSlide(450) 
          }}>
            or
          </Divider>

          <Box sx={{ display: 'flex', gap: 2, ...fadeSlide(500) }}>
            <Button 
              variant="outlined" 
              fullWidth 
              onClick={() => navigate("/login")} 
              disableElevation 
              sx={actionButtonStyle(false)}
            >
              Log In
            </Button>

            <Button 
              variant="outlined" 
              fullWidth 
              onClick={handleDebugBypass} 
              disableElevation 
              startIcon={<BugReportIcon />}
              sx={{ 
                ...actionButtonStyle(false), 
                color: theme.palette.error.main, 
                borderColor: theme.palette.error.main,
                '&:hover': {
                  bgcolor: theme.palette.error.main,
                  color: '#fff',
                  borderColor: theme.palette.error.main
                }
              }}
            >
              Bypass
            </Button>
          </Box>
        </Box>
      </Box>
    </Container>
  );
}

export default Register;