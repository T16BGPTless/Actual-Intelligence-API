import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';

// MUI
import {
  TextField,
  Button,
  Alert,
  Box,
  Container,
  Typography,
} from '@mui/material';

const BACKEND_URL = "http://localhost:5000";

function Register() {
  const navigate = useNavigate();

  const [name, setName] = useState('');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');

  const registerUser = async (e) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
        setError('Passwords do not match.');
        return;
    }

    try {
        const res = await axios.post(`${BACKEND_URL}/v1/auth/register`, {
        email,
        password,
        name,
        username,
        });

        localStorage.setItem('token', res.data.accessToken);
        localStorage.setItem('email', email);

        navigate('/');
    } catch (err) {
        console.log(err);

        const backendMessage =
        err.response?.data?.message ||
        err.response?.data?.error ||
        err.message ||
        'Registration failed';

        setError(backendMessage);
    }
    };

  return (
    <Container maxWidth="sm">
      <Box sx={{
        mt: 8,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center'
      }}>
        <Typography variant="h4" sx={{ mb: 3 }}>
          Register for GPTless
        </Typography>

        {error && (
          <Alert severity="error" sx={{ width: '100%', mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box component="form" onSubmit={registerUser} sx={{ width: '100%' }}>
          <TextField
            label="Name"
            fullWidth
            margin="normal"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />

          <TextField
            label="Username"
            fullWidth
            margin="normal"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />

          <TextField
            label="Email"
            fullWidth
            margin="normal"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />

          <TextField
            label="Password"
            type="password"
            fullWidth
            margin="normal"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />

          <TextField
            label="Confirm Password"
            type="password"
            fullWidth
            margin="normal"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
          />

          <Button
            variant="contained"
            fullWidth
            sx={{ mt: 3 }}
            onClick={registerUser}
            type="submit"
          >
            Register
          </Button>

          <Link to="/login">Already registered? Login now</Link>
        </Box>
      </Box>
    </Container>
  );
}

export default Register;