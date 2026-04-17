import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

// MUI
import {
  Button,
  Box,
  Container,
  Typography,
  Divider,
} from "@mui/material";

const BACKEND_URL = "http://localhost:5000";

export default function Home() {
  const navigate = useNavigate();
  const [mounted, setMounted] = useState(false);
  const [tokenBalance, setTokenBalance] = useState(null);
  
  const token = localStorage.getItem("token");
  const isAuthenticated = Boolean(token);
  // Ensure 'accountName' (or 'username') is saved to localStorage on login/register
  const accountName = localStorage.getItem("accountName") || localStorage.getItem("username");

  useEffect(() => {
    const timer = setTimeout(() => setMounted(true), 50);
    return () => clearTimeout(timer);
  }, []);

  // Fetch Tokens when authenticated
  useEffect(() => {
    if (isAuthenticated && accountName) {
      const fetchTokens = async () => {
        try {
          const res = await axios.get(`${BACKEND_URL}/v1/tokens`, {
            headers: { Authorization: `Bearer ${token}` },
            // Pass the body payload for the GET request as expected by the Flask backend
            data: { accountName: accountName } 
          });
          setTokenBalance(res.data.tokenBalance);
        } catch (err) {
          console.error("Failed to fetch token balance", err);
        }
      };
      fetchTokens();
    }
  }, [isAuthenticated, accountName, token]);

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
      <Box sx={{ textAlign: 'center', mb: 8, mt: 4, position: 'relative' }}>
        {/* Aesthetic brutalist tracking line */}
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', mb: 3, ...fadeSlide(0) }}>
          <Box sx={{ height: '2px', width: '40px', bgcolor: 'black', mr: 2 }} />
          <Typography variant="caption" sx={{ fontWeight: 800, letterSpacing: 4, textTransform: 'uppercase' }}>
            Cat Protocol 1.0
          </Typography>
          <Box sx={{ height: '2px', width: '40px', bgcolor: 'black', ml: 2 }} />
        </Box>

        <Typography variant="h2" sx={{ fontWeight: 900, letterSpacing: "-2px", ...fadeSlide(50) }}>
          <Box component="span" sx={{ color: '#b0b0b0' }}>ACTUAL</Box> INTELLIGENCE
        </Typography>
        <Typography variant="h6" sx={{ fontWeight: 600, color: "#555", mt: 2, letterSpacing: "1px", ...fadeSlide(100) }}>
          Human Logic. Ethical Processing. Verified Results.
        </Typography>
      </Box>

      {/* Main Table */}
      <Box 
        sx={{ 
          display: 'flex', 
          flexDirection: { xs: 'column', md: 'row' },
          borderTop: '4px solid black', 
          borderBottom: '4px solid black',
          backgroundColor: '#fff',
          ...fadeSlide(150)
        }}
      >
        {/* Left Panel */}
        <Box sx={{ 
          flex: 1, 
          p: { xs: 5, md: 8 }, 
          display: 'flex', 
          flexDirection: 'column', 
          alignItems: 'center', 
          justifyContent: 'center',
          textAlign: 'center'
        }}>
          {!isAuthenticated ? (
            <>
              <Typography variant="h4" sx={{ fontWeight: 900, mb: 2, letterSpacing: "1px" }}>LOGIN</Typography>
              <Typography variant="body1" sx={{ mb: 5, color: "#666", maxWidth: "340px", lineHeight: 1.6, fontWeight: 500 }}>
                Return to your secure dashboard to manage your existing task queues, review completed cognitive cycles, and monitor your intelligence ecosystem.
              </Typography>
              <Button onClick={() => navigate("/login")} sx={buttonBase(true)}>Log In</Button>
            </>
          ) : (
            <>
              <Typography variant="h4" sx={{ fontWeight: 900, mb: 2, letterSpacing: "1px" }}>REQUESTER</Typography>
              <Typography variant="body1" sx={{ mb: 5, color: "#666", maxWidth: "340px", lineHeight: 1.6, fontWeight: 500 }}>
                Outsource your complex computational and cognitive tasks to our global network of verified human specialists. Ensure high-fidelity, ethical results with full transparency and zero algorithmic hallucination.
              </Typography>
              <Button onClick={() => navigate("/chat/new")} sx={buttonBase(true)}>Create Chat</Button>
            </>
          )}
        </Box>

        {/* Vertical Divider */}
        <Divider 
          orientation="vertical" 
          flexItem 
          sx={{ borderRightWidth: 4, borderColor: 'black', display: { xs: 'none', md: 'block' } }} 
        />
        {/* HORIZONTAL DIVIDER (Visible only on Mobile) */}
        <Divider sx={{ display: { xs: 'block', md: 'none' }, borderColor: 'black', borderBottomWidth: 4 }} />

        {/* Right Panel */}
        <Box sx={{ 
          flex: 1, 
          p: { xs: 5, md: 8 }, 
          display: 'flex', 
          flexDirection: 'column', 
          alignItems: 'center', 
          justifyContent: 'center',
          textAlign: 'center',
          bgcolor: '#fafafa' // Slight off-white to distinguish panels
        }}>
          {!isAuthenticated ? (
            <>
              <Typography variant="h4" sx={{ fontWeight: 900, mb: 2, letterSpacing: "1px" }}>REGISTER</Typography>
              <Typography variant="body1" sx={{ mb: 5, color: "#666", maxWidth: "340px", lineHeight: 1.6, fontWeight: 500 }}>
                New to the platform? Join the decentralized network of human-driven intelligence. Become a node in the ethical data economy and monetize your unique cognitive abilities.
              </Typography>
              <Button onClick={() => navigate("/register")} sx={buttonBase(false)}>Sign Up</Button>
            </>
          ) : (
            <>
              <Typography variant="h4" sx={{ fontWeight: 900, mb: 2, letterSpacing: "1px" }}>RESPONDER</Typography>
              <Typography variant="body1" sx={{ mb: 5, color: "#666", maxWidth: "340px", lineHeight: 1.6, fontWeight: 500 }}>
                Monetize your unique cognitive skills and domain expertise. Claim verified micro-tasks, process data with human intuition, and earn tokens in our sustainable intelligence economy.
              </Typography>
              <Button onClick={() => navigate("/tasks/claim")} sx={buttonBase(false)}>Claim Tasks</Button>
            </>
          )}
        </Box>
      </Box>

      {/* Footer Section */}
      {isAuthenticated && (
        <Box sx={{ mt: 8, textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', ...fadeSlide(300) }}>
          
          {/* Token Display Box */}
          <Box sx={{ 
            border: '2px solid black', 
            py: 2, 
            px: 4, 
            display: 'inline-flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            mb: 3,
            bgcolor: 'black',
            color: 'white'
          }}>
            <Typography variant="overline" sx={{ fontWeight: 700, letterSpacing: 2, mr: 2, color: "#aaa" }}>
              Available Balance
            </Typography>
            <Typography variant="h5" sx={{ fontWeight: 900, display: 'flex', alignItems: 'center' }}>
              {tokenBalance !== null ? tokenBalance : "—"} 
              <Box component="span" sx={{ ml: 1, color: '#FFD700', fontSize: '1.2rem' }}>◈</Box>
            </Typography>
          </Box>

          <Button onClick={() => navigate("/tokens")} sx={{ ...buttonBase(false), maxWidth: "200px", py: 1, fontSize: '0.8rem' }}>
            Manage Tokens
          </Button>
        </Box>
      )}

      <Typography variant="caption" sx={{ mt: isAuthenticated ? 6 : 10, textAlign: 'center', fontWeight: 600, color: '#aaa', letterSpacing: 1, ...fadeSlide(400) }}>
        © 2026 ACTUAL INTELLIGENCE — SUSTAINABLE COGNITIVE LABOR
      </Typography>

    </Container>
  );
}