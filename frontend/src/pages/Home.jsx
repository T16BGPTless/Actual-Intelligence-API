import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

// MUI
import {
  Button,
  Box,
  Container,
  Typography,
  Divider,
} from "@mui/material";

export default function Home() {
  const navigate = useNavigate();
  const [mounted, setMounted] = useState(false);
  const isAuthenticated = Boolean(localStorage.getItem("token"));

  useEffect(() => {
    const timer = setTimeout(() => setMounted(true), 50);
    return () => clearTimeout(timer);
  }, []);

  const fadeSlide = (delay = 0) => ({
    opacity: mounted ? 1 : 0,
    transform: mounted ? "translateX(0px)" : "translateX(-20px)",
    transition: "all 0.5s cubic-bezier(0.16, 1, 0.3, 1)",
    transitionDelay: `${delay}ms`,
  });

  const buttonBase = (isPrimary) => ({
    py: 2,
    px: 4,
    width: "100%",
    maxWidth: "280px",
    borderRadius: "0px",
    textTransform: "uppercase",
    fontSize: "0.9rem",
    fontWeight: 900,
    letterSpacing: "2px",
    transition: "all 0.2s ease-in-out",
    border: "2px solid black",
    bgcolor: isPrimary ? "black" : "transparent",
    color: isPrimary ? "white" : "black",
    "&:hover": {
      bgcolor: isPrimary ? "#333" : "black",
      color: "white",
      transform: "translateY(-2px)",
      boxShadow: "6px 6px 0px rgba(0,0,0,0.1)",
    },
  });

  return (
    <Container maxWidth="lg" sx={{ minHeight: "90vh", display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
      
      {/* Top Header */}
      <Box sx={{ textAlign: 'center', mb: 8 }}>
        <Typography variant="h2" sx={{ fontWeight: 900, letterSpacing: "-2px", ...fadeSlide(0) }}>
          ACTUAL INTELLIGENCE
        </Typography>
        <Typography variant="h6" sx={{ fontWeight: 500, color: "#666", mt: 1, ...fadeSlide(50) }}>
          Human Logic. Ethical Processing. Verified Results.
        </Typography>
      </Box>

      {/* Main Table */}
      <Box 
        sx={{ 
          display: 'flex', 
          flexDirection: { xs: 'column', md: 'row' },
          borderTop: '3px solid black', 
          borderBottom: '3px solid black',
          ...fadeSlide(150)
        }}
      >
        {/* Left Panel */}
        <Box sx={{ 
          flex: 1, 
          p: { xs: 4, md: 8 }, 
          display: 'flex', 
          flexDirection: 'column', 
          alignItems: 'center', 
          justifyContent: 'center',
          textAlign: 'center'
        }}>
          {!isAuthenticated ? (
            <>
              <Typography variant="h4" sx={{ fontWeight: 900, mb: 1 }}>LOGIN</Typography>
              <Typography variant="body2" sx={{ mb: 4, color: "#777", maxWidth: "300px" }}>
                Return to your dashboard to manage your existing tasks and chats.
              </Typography>
              <Button onClick={() => navigate("/login")} sx={buttonBase(true)}>Log In</Button>
            </>
          ) : (
            <>
              <Typography variant="h4" sx={{ fontWeight: 900, mb: 1 }}>REQUESTER</Typography>
              <Typography variant="body2" sx={{ mb: 4, color: "#777", maxWidth: "300px" }}>
                Outsource tasks to human specialists for high-fidelity, ethical results.
              </Typography>
              <Button onClick={() => navigate("/chat/new")} sx={buttonBase(true)}>Create Chat</Button>
            </>
          )}
        </Box>

        {/* Verticle Divider */}
        <Divider 
          orientation="vertical" 
          flexItem 
          sx={{ borderRightWidth: 3, borderColor: 'black', display: { xs: 'none', md: 'block' } }} 
        />
        {/* HORIZONTAL DIVIDER (Visible only on Mobile) */}
        <Divider sx={{ display: { xs: 'block', md: 'none' }, borderColor: 'black', borderBottomWidth: 2 }} />

        {/* Right Panel */}
        <Box sx={{ 
          flex: 1, 
          p: { xs: 4, md: 8 }, 
          display: 'flex', 
          flexDirection: 'column', 
          alignItems: 'center', 
          justifyContent: 'center',
          textAlign: 'center'
        }}>
          {!isAuthenticated ? (
            <>
              <Typography variant="h4" sx={{ fontWeight: 900, mb: 1 }}>REGISTER</Typography>
              <Typography variant="body2" sx={{ mb: 4, color: "#777", maxWidth: "300px" }}>
                New to the platform? Join the network of human-driven intelligence.
              </Typography>
              <Button onClick={() => navigate("/register")} sx={buttonBase(false)}>Sign Up</Button>
            </>
          ) : (
            <>
              <Typography variant="h4" sx={{ fontWeight: 900, mb: 1 }}>RESPONDER</Typography>
              <Typography variant="body2" sx={{ mb: 4, color: "#777", maxWidth: "300px" }}>
                Monetize your cognitive skills by completing human-verified tasks.
              </Typography>
              <Button onClick={() => navigate("/tasks/claim")} sx={buttonBase(true)}>Claim Tasks</Button>
            </>
          )}
        </Box>
      </Box>

      {/* Footer Section */}
      {isAuthenticated && (
        <Box sx={{ mt: 6, textAlign: 'center', ...fadeSlide(300) }}>
          <Typography variant="overline" sx={{ fontWeight: 900, letterSpacing: 2, color: "#888" }}>
            Economy Management
          </Typography>
          <Box sx={{ mt: 1 }}>
            <Button onClick={() => navigate("/tokens")} sx={{ ...buttonBase(false), maxWidth: "200px", py: 1 }}>
              Buy Tokens
            </Button>
          </Box>
        </Box>
      )}

      <Typography variant="caption" sx={{ mt: 6, textAlign: 'center', opacity: 0.5, ...fadeSlide(400) }}>
        © 2026 ACTUAL INTELLIGENCE — SUSTAINABLE COGNITIVE LABOR
      </Typography>

    </Container>
  );
}