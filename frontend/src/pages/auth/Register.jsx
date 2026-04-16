import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

// MUI
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
} from '@mui/material';

// Icons
import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';

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
  const [error, setError] = useState('');
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setMounted(true), 50);
    return () => clearTimeout(timer);
  }, []);

  const handleChange = (prop) => (e) => {
    setFormData({ ...formData, [prop]: e.target.value });
  };

  const registerUser = async (e) => {
    e.preventDefault();
    setError('');

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match.');
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
      const backendMessage =
        err.response?.data?.message ||
        err.response?.data?.error ||
        err.message ||
        'Registration failed';

      setError(backendMessage);
    }
  };

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
      <Box sx={{ mt: 8, display: 'flex', flexDirection: 'column', alignItems: 'center', pb: 4 }}>
        
        <Typography 
          variant="h4" 
          sx={{ 
            fontWeight: 900, 
            mb: 1, 
            textTransform: 'uppercase', 
            letterSpacing: '-1px', 
            ...fadeSlide(0) 
          }}
        >
          Register
        </Typography>

        <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 4, color: '#666', ...fadeSlide(50) }}>
          Create a New Account
        </Typography>

        {error && (
          <Alert severity="error" variant="filled" sx={{ width: '100%', mb: 3, borderRadius: '0px', bgcolor: 'black', ...fadeSlide(100) }}>
            {error}
          </Alert>
        )}

        <Box component="form" onSubmit={registerUser} sx={{ width: '100%' }}>
          
          <TextField placeholder="FULL NAME" fullWidth value={formData.name} onChange={handleChange('name')} sx={{ ...inputStyles, ...fadeSlide(150) }} />
          <TextField placeholder="USERNAME" fullWidth value={formData.username} onChange={handleChange('username')} sx={{ ...inputStyles, ...fadeSlide(200) }} />
          <TextField placeholder="EMAIL ADDRESS" fullWidth value={formData.email} onChange={handleChange('email')} sx={{ ...inputStyles, ...fadeSlide(250) }} />
          
          <TextField 
            placeholder="PASSWORD" 
            type={showPassword ? 'text' : 'password'} 
            fullWidth 
            value={formData.password} 
            onChange={handleChange('password')} 
            sx={{ ...inputStyles, ...fadeSlide(300) }}
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={() => setShowPassword(!showPassword)}
                      onMouseDown={(e) => e.preventDefault()}
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

          <TextField 
            placeholder="CONFIRM PASSWORD" 
            type={showConfirmPassword ? 'text' : 'password'} 
            fullWidth 
            value={formData.confirmPassword} 
            onChange={handleChange('confirmPassword')} 
            sx={{ ...inputStyles, mb: 3, ...fadeSlide(350) }}
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      onMouseDown={(e) => e.preventDefault()}
                      edge="end"
                      sx={{ color: 'black' }}
                    >
                      {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              },
            }}
          />

          <Button variant="contained" fullWidth type="submit" disableElevation sx={{ ...actionButtonStyle(true), ...fadeSlide(400) }}>
            Sign Up
          </Button>

          <Divider sx={{ my: 4, fontWeight: 800, textTransform: 'uppercase', ...fadeSlide(450) }}>or</Divider>

          <Button variant="outlined" fullWidth onClick={() => navigate("/login")} disableElevation sx={{ ...actionButtonStyle(false), ...fadeSlide(500) }}>
            Log In
          </Button>

          <Typography variant="body2" align="center" sx={{ mt: 4, color: '#888', fontWeight: 500, ...fadeSlide(550) }}>
            By clicking Sign Up, you agree to our <span style={{ color: 'black', fontWeight: 800, cursor: 'pointer' }}>Terms and Privacy Policy</span>
          </Typography>

        </Box>
      </Box>
    </Container>
  );
}

export default Register;