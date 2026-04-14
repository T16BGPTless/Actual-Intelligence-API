import { useState } from 'react';
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
  Divider
} from '@mui/material';

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

  const [error, setError] = useState('');
  const [mounted, setMounted] = useState(false);

  useState(() => {
    setTimeout(() => setMounted(true), 50);
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
      borderRadius: '8px',
      backgroundColor: '#fafafa',
    }
  };

  const formButtonStyle = (isPrimary) => ({
    py: 1.5,
    borderRadius: '8px',
    textTransform: 'none',
    fontSize: '1rem',
    fontWeight: 600,
    transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
    bgcolor: isPrimary ? 'black' : 'rgba(255, 255, 255, 0.1)',
    color: isPrimary ? 'white' : '#666',
    border: isPrimary ? 'none' : '1px solid #ddd',
    '&:hover': {
      bgcolor: isPrimary ? '#222' : 'rgba(0, 0, 0, 0.05)',
      transform: 'translateY(-1px)',
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
      <Box
        sx={{
          mt: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          pb: 4
        }}
      >
        <Typography variant="h4" sx={{ fontWeight: 900, mb: 1, ...fadeSlide(0) }}>
          Actual Intelligence
        </Typography>

        <Typography
          variant="subtitle1"
          sx={{ fontWeight: 600, mb: 4, color: '#666', ...fadeSlide(50) }}
        >
          Create a New Account
        </Typography>

        {error && (
          <Alert severity="error" sx={{ width: '100%', mb: 3, borderRadius: '8px', ...fadeSlide(100) }}>
            {error}
          </Alert>
        )}

        <Box component="form" onSubmit={registerUser} sx={{ width: '100%' }}>
          
          <TextField placeholder="Name" fullWidth value={formData.name} onChange={handleChange('name')} sx={{ ...inputStyles, ...fadeSlide(150) }} />
          <TextField placeholder="Username" fullWidth value={formData.username} onChange={handleChange('username')} sx={{ ...inputStyles, ...fadeSlide(200) }} />
          <TextField placeholder="Email" fullWidth value={formData.email} onChange={handleChange('email')} sx={{ ...inputStyles, ...fadeSlide(250) }} />
          <TextField placeholder="Password" type="password" fullWidth value={formData.password} onChange={handleChange('password')} sx={{ ...inputStyles, ...fadeSlide(300) }} />
          <TextField placeholder="Repeat Password" type="password" fullWidth value={formData.confirmPassword} onChange={handleChange('confirmPassword')} sx={{ ...inputStyles, mb: 3, ...fadeSlide(350) }} />

          <Button variant="contained" fullWidth disableElevation sx={{ ...formButtonStyle(true), ...fadeSlide(400) }} type="submit">
            Sign Up
          </Button>

          <Divider sx={{ my: 3, ...fadeSlide(450) }}>or</Divider>

          <Button variant="contained" fullWidth disableElevation sx={{ ...formButtonStyle(false), ...fadeSlide(500) }} onClick={() => navigate("/login")}>
            Sign In
          </Button>

          <Typography variant="body2" align="center" sx={{ mt: 4, color: 'text.secondary', ...fadeSlide(550) }}>
            By clicking Sign Up, you agree to our Terms and Privacy Policy
          </Typography>

        </Box>
      </Box>
    </Container>
  );
}

export default Register;