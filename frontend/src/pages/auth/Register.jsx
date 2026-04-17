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
  IconButton
} from '@mui/material';

// Icons
import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';
import BugReportIcon from '@mui/icons-material/BugReport';

const BACKEND_URL = "http://localhost:5000";

function Register() {
  const navigate = useNavigate();

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

  // DEBUG BYPASS HANDLER
  const handleDebugBypass = () => {
    // Manually set local storage to mimic a successful login
    const debugToken = `debug_session_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem('token', debugToken);
    localStorage.setItem('email', 'debug_user@local.test');
    
    console.warn("DEBUG: Bypass triggered. Session ID injected into LocalStorage.");
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

      localStorage.setItem('token', res.data.accessToken);
      localStorage.setItem('email', formData.email);
      navigate('/');
    } catch (err) {
      const msg = err.response?.data?.message || err.response?.data?.error || 'Registration failed';
      if (msg.toLowerCase().includes("email")) {
        setErrors({ email: msg });
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
      color: '#ff1744',
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
      <Box sx={{ mt: 8, display: 'flex', flexDirection: 'column', alignItems: 'center', pb: 4 }}>
        
        <Typography variant="h4" sx={{ fontWeight: 900, mb: 1, textTransform: 'uppercase', ...fadeSlide(0) }}>
          Register
        </Typography>

        <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 4, color: '#666', ...fadeSlide(50) }}>
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
          />

          <TextField 
            placeholder="USERNAME" 
            fullWidth 
            value={formData.username} 
            onChange={handleChange('username')} 
            error={!!errors.username}
            helperText={errors.username}
            sx={{ ...inputStyles, ...fadeSlide(200) }} 
          />

          <TextField 
            placeholder="EMAIL ADDRESS" 
            fullWidth 
            value={formData.email} 
            onChange={handleChange('email')} 
            error={!!errors.email}
            helperText={errors.email}
            sx={{ ...inputStyles, ...fadeSlide(250) }} 
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
                    <IconButton onClick={() => setShowPassword(!showPassword)} edge="end" sx={{ color: 'black' }}>
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
                    <IconButton onClick={() => setShowConfirmPassword(!showConfirmPassword)} edge="end" sx={{ color: 'black' }}>
                      {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              },
            }}
          />

          {errors.general && (
            <Typography variant="caption" sx={{ color: '#ff1744', fontWeight: 900, mb: 2, display: 'block', textAlign: 'center' }}>
              {errors.general}
            </Typography>
          )}

          <Button variant="contained" fullWidth type="submit" disableElevation sx={{ ...actionButtonStyle(true), ...fadeSlide(400) }}>
            Sign Up
          </Button>

          <Divider sx={{ my: 4, fontWeight: 800, textTransform: 'uppercase', ...fadeSlide(450) }}>or</Divider>

          {/* Action Row for Login and Debug Bypass */}
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
                color: '#d32f2f', 
                borderColor: '#d32f2f',
                '&:hover': {
                  bgcolor: '#d32f2f',
                  color: 'white',
                  borderColor: '#d32f2f'
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