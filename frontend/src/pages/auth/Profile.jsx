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

function Profile() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    "username": '',
    "name": '',
    "email": '',
    "createdAt": ''
  });

  const [error, setError] = useState('');
  const [mounted, setMounted] = useState(false);

  useState(() => {
    setTimeout(() => setMounted(true), 50);
  }, []);

  const handleChange = (prop) => (e) => {
    setFormData({ ...formData, [prop]: e.target.value });
  };

  const getProfile = async (e) => {
    e.preventDefault();
    setError('');

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
}