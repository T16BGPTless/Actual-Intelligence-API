import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

// MUI
import {
  TextField,
  Button,
  Alert,
  Box,
  Container,
  Typography,
  Divider
} from "@mui/material";

const BACKEND_URL = "http://localhost:5000";

function Login() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
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
      const res = await axios.post(`${BACKEND_URL}/v1/auth/login`, {
        email,
        password,
      });

      localStorage.setItem("token", res.data.accessToken);
      localStorage.setItem("email", email);

      navigate("/");
    } catch (err) {
      setError(err.response?.data?.message || "Login failed");
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
          Log In to Your Account
        </Typography>

        {error && (
          <Alert
            severity="error"
            sx={{ width: '100%', mb: 3, borderRadius: '8px', ...fadeSlide(100) }}
          >
            {error}
          </Alert>
        )}

        <Box component="form" onSubmit={handleLogin} sx={{ width: '100%' }}>
          
          <TextField
            placeholder="Email"
            fullWidth
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            sx={{ ...inputStyles, ...fadeSlide(150) }}
          />

          <TextField
            placeholder="Password"
            type="password"
            fullWidth
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            sx={{ ...inputStyles, mb: 3, ...fadeSlide(200) }}
          />

          <Button
            variant="contained"
            fullWidth
            type="submit"
            disableElevation
            sx={{ ...formButtonStyle(true), ...fadeSlide(250) }}
          >
            Sign In
          </Button>

          <Divider sx={{ my: 3, ...fadeSlide(300) }}>
            or
          </Divider>

          <Button
            variant="contained"
            fullWidth
            onClick={() => navigate("/register")}
            disableElevation
            sx={{ ...formButtonStyle(false), ...fadeSlide(350) }}
          >
            Create an Account
          </Button>

          <Typography
            variant="body2"
            align="center"
            sx={{ mt: 4, color: 'text.secondary', ...fadeSlide(400) }}
          >
            Forgot your password?{' '}
            <Box
              component="span"
              sx={{ color: 'black', fontWeight: 600, cursor: 'pointer' }}
            >
              Reset it here
            </Box>
          </Typography>

        </Box>
      </Box>
    </Container>
  );
}

export default Login;