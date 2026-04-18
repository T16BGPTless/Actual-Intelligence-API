import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";

// MUI
import {
  Button,
  Box,
  Container,
  Typography,
  Divider,
  Grid,
  useTheme,
} from "@mui/material";

// Icons
import TokenIcon from '@mui/icons-material/Token';
import SecurityIcon from '@mui/icons-material/Security';

// Assets
import catLeft from "../assets/cat3.png";
import catRight from "../assets/cat7.png";
import catEconomy from "../assets/cat5.png";
import catIntro from "../assets/cat2.png"; 

const ScrollSection = ({ children, index, delay = 0 }) => {
  const [isVisible, setIsVisible] = useState(false);
  const domRef = useRef();
  const animationsEnabled = localStorage.getItem("ui-animations") !== "false";

  useEffect(() => {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => setIsVisible(entry.isIntersecting));
    }, { threshold: 0.1 });
    const currentRef = domRef.current;
    if (currentRef) observer.observe(currentRef);
    return () => { if (currentRef) observer.unobserve(currentRef); };
  }, []);

  const isEven = index % 2 === 0;

  return (
    <Box
      ref={domRef}
      sx={{
        opacity: animationsEnabled ? (isVisible ? 1 : 0) : 1,
        transform: animationsEnabled 
          ? (isVisible ? "translateX(0)" : `translateX(${isEven ? "-50px" : "50px"})`)
          : "none",
        transition: animationsEnabled ? "all 0.8s cubic-bezier(0.16, 1, 0.3, 1), transform 0.4s ease-out" : "none",
        transitionDelay: animationsEnabled ? `${delay}ms` : "0ms",
        width: "100%",
        '&:hover': {
           transform: (animationsEnabled && isVisible) ? 'scale(1.01)' : undefined,
           zIndex: 5,
        }
      }}
    >
      {children}
    </Box>
  );
};

export default function Home() {
  const navigate = useNavigate();
  const theme = useTheme(); 
  
  const currentThemeId = localStorage.getItem("ui-theme") || "default";
  const isDarkMode = theme.palette.mode === 'dark';
  const animationsEnabled = localStorage.getItem("ui-animations") !== "false";

  const bannerBg = isDarkMode ? theme.palette.primary.main : (currentThemeId === 'default' ? '#000' : theme.palette.primary.main);
  const bannerText = isDarkMode ? theme.palette.background.default : '#fff';
  const bannerOutline = isDarkMode ? theme.palette.background.default : 'rgba(255,255,255,0.4)';

  const sectionShadow = isDarkMode 
    ? `0 20px 60px ${theme.palette.primary.main}44` 
    : '0 20px 40px rgba(0,0,0,0.1)';

  const isAuthenticated = Boolean(localStorage.getItem("token"));
  const username = localStorage.getItem("username") || "User";

  const [isMeowing, setIsMeowing] = useState(false);
  const [isShaking, setIsShaking] = useState(false);
  const [isPurring, setIsPurring] = useState(false);

  const meowTimer = useRef(null);
  const purrTimer = useRef(null);

  const handleHover = () => {
    if (!animationsEnabled) return;
    if (meowTimer.current) clearTimeout(meowTimer.current);
    setIsMeowing(false); 
    setTimeout(() => setIsMeowing(true), 10);
    meowTimer.current = setTimeout(() => setIsMeowing(false), 800);
  };

  const handleClick = () => {
    if (!animationsEnabled) return;
    if (purrTimer.current) clearTimeout(purrTimer.current);
    setIsShaking(false);
    setIsPurring(false);
    setTimeout(() => {
      setIsShaking(true);
      setIsPurring(true);
    }, 10);
    purrTimer.current = setTimeout(() => {
      setIsShaking(false);
      setIsPurring(false);
    }, 600);
  };

  const subSectionStyle = {
    flex: 1,
    transition: animationsEnabled ? 'all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1)' : 'none',
    position: 'relative',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center', 
    justifyContent: 'center', 
    bgcolor: theme.palette.background.paper,
    '&:hover': {
      bgcolor: theme.palette.background.paper,
      zIndex: 10,
      transform: animationsEnabled ? 'scale(1.03)' : 'none',
      boxShadow: (animationsEnabled) ? sectionShadow : 'none',
    }
  };

  const userButtonStyle = {
    ml: 2, px: 3, py: 0.5,
    borderRadius: 0,
    color: bannerText,
    border: `2px solid ${bannerOutline}`,
    fontWeight: 900,
    fontSize: { xs: '1.2rem', md: '2.2rem' },
    lineHeight: 1.2,
    letterSpacing: animationsEnabled ? '2px' : '4px',
    transition: animationsEnabled ? 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)' : 'none',
    textTransform: 'uppercase',
    position: 'relative',
    display: 'flex',
    alignItems: 'center',
    '&:hover': {
      borderColor: bannerText,
      bgcolor: 'rgba(255, 255, 255, 0.1)',
      transform: animationsEnabled ? 'translateY(-2px)' : 'none',
      letterSpacing: animationsEnabled ? '6px' : '4px',
      pl: animationsEnabled ? 5 : 3,
    },
    '&::before': {
      content: '">"',
      position: 'absolute', left: '15px', opacity: 0,
      transition: animationsEnabled ? 'all 0.3s ease' : 'none',
    },
    '&:hover::before': { opacity: animationsEnabled ? 1 : 0 }
  };

  const buttonBase = (isPrimary) => ({
    py: 2, px: 4, width: "100%", maxWidth: "280px", borderRadius: 0,
    textTransform: "uppercase", fontSize: "0.9rem", fontWeight: 900,
    letterSpacing: "2px", transition: animationsEnabled ? "all 0.2s ease-in-out" : "none",
    border: `2px solid ${theme.palette.text.primary}`,
    bgcolor: isPrimary ? theme.palette.text.primary : "transparent",
    color: isPrimary ? theme.palette.background.default : theme.palette.text.primary,
    "&:hover": {
      bgcolor: isPrimary ? theme.palette.text.secondary : theme.palette.text.primary,
      color: theme.palette.background.default,
      transform: animationsEnabled ? "translateY(-2px)" : "none",
      boxShadow: animationsEnabled ? `6px 6px 0px ${theme.palette.text.primary}44` : "none",
    },
  });

  return (
    <Container maxWidth="lg" sx={{ minHeight: "100vh", display: 'flex', flexDirection: 'column', py: 8 }}>
      
      {/* 0. Header Section */}
      <ScrollSection index={0}>
        <Box sx={{ textAlign: 'center', mb: 8 }}>
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 2, mb: -1 }}>
            <Divider sx={{ width: 40, borderBottomWidth: 3, borderColor: theme.palette.text.primary }} />
            <Typography variant="overline" sx={{ fontWeight: 900, letterSpacing: 4 }}>System.v1</Typography>
            <Divider sx={{ width: 40, borderBottomWidth: 3, borderColor: theme.palette.text.primary }} />
          </Box>
          <Typography variant="h2" sx={{ fontWeight: 900, letterSpacing: "-2px" }}>HOME</Typography>
          <Typography variant="body2" sx={{ opacity: 0.6, fontWeight: 700, letterSpacing: 1, textTransform: 'uppercase' }}>
            Human Logic. Ethical Processing. Verified Results.
          </Typography>
        </Box>
      </ScrollSection>

      {/* 1. Welcome / Mission Section */}
      <ScrollSection index={1}>
        {!isAuthenticated ? (
          <Box sx={{ 
            display: 'flex', flexDirection: { xs: 'column', md: 'row' }, 
            border: `3px solid ${theme.palette.text.primary}`, mb: 10, 
            bgcolor: theme.palette.background.paper,
            '&:hover': { boxShadow: sectionShadow }
          }}>
            <Box sx={{ ...subSectionStyle, p: 4, textAlign: 'left', alignItems: 'flex-start', borderRight: { md: `3px solid ${theme.palette.text.primary}` } }}>
                <Typography variant="overline" sx={{ fontWeight: 900, color: theme.palette.text.disabled }}>01 // The Mission</Typography>
                <Typography variant="h5" sx={{ fontWeight: 900, mb: 1, mt: 1 }}>DECENTRALIZING COGNITION</Typography>
                <Typography variant="body2" sx={{ color: theme.palette.text.secondary, lineHeight: 1.6 }}>
                    Current automated models are environmentally unsustainable and spiritually hollow. 
                    <strong> Actual Intelligence</strong> restores the human element to the grid.
                </Typography>
            </Box>
            <Box sx={{ flex: 0.8, bgcolor: theme.palette.text.primary, display: 'flex', alignItems: 'center', justifyContent: 'center', p: 4 }}>
               <Box 
                  component="img" src={catIntro}
                  sx={{ maxHeight: "150px", width: "auto", filter: 'invert(1) brightness(1.2)', objectFit: "contain" }}
                />
            </Box>
          </Box>
        ) : (
          <Box sx={{ 
            display: 'flex', border: `3px solid ${theme.palette.text.primary}`, mb: 10, 
            bgcolor: bannerBg, height: { xs: 'auto', md: '250px' }, overflow: 'hidden',
            transition: 'box-shadow 0.3s ease', '&:hover': { boxShadow: sectionShadow }
          }}>
              <Box sx={{ flex: 1.2, display: { xs: 'none', md: 'block' }, position: 'relative', p: 2 }}>
                <Box sx={{
                  width: '100%', height: '100%', backgroundImage: `url(${catLeft})`,
                  backgroundSize: 'contain', backgroundRepeat: 'no-repeat', backgroundPosition: 'center right',
                  filter: isDarkMode ? 'none' : 'invert(1) brightness(1.2)',
                  WebkitMaskImage: 'linear-gradient(to right, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 90%)'
                }} />
              </Box>

              <Box sx={{ flex: 3, p: 6, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', color: bannerText, zIndex: 1 }}>
                  <Typography variant="overline" sx={{ letterSpacing: 3, opacity: 0.7, mb: 1, color: bannerText }}>Connection Established</Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', flexWrap: 'wrap' }}>
                    <Typography variant="h3" sx={{ fontWeight: 900, letterSpacing: '-1px', color: bannerText }}>WELCOME,</Typography>
                    <Button onClick={() => navigate("/profile")} sx={userButtonStyle}>{username}</Button>
                  </Box>
                  <Typography variant="body1" sx={{ color: bannerText, opacity: 0.8, mt: 3, maxWidth: '500px' }}>
                      Systems are live. Interface with the network to start processing tasks.
                  </Typography>
              </Box>

              <Box sx={{ flex: 1.2, display: { xs: 'none', md: 'block' }, position: 'relative', p: 2 }}>
                <Box sx={{
                  width: '100%', height: '100%', backgroundImage: `url(${catRight})`,
                  backgroundSize: 'contain', backgroundRepeat: 'no-repeat', backgroundPosition: 'center left',
                  filter: isDarkMode ? 'none' : 'invert(1) brightness(1.2)',
                  WebkitMaskImage: 'linear-gradient(to left, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 90%)'
                }} />
              </Box>
          </Box>
        )}
      </ScrollSection>

      {/* 2. Main Dashboard Panel */}
      <ScrollSection index={2}>
        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, borderTop: `3px solid ${theme.palette.text.primary}`, borderBottom: `3px solid ${theme.palette.text.primary}`, bgcolor: theme.palette.background.default, mb: 8 }}>
          
          <Box sx={{ ...subSectionStyle, p: { xs: 4, md: 8 }, textAlign: 'center', borderRight: { md: `3px solid ${theme.palette.text.primary}` } }}>
            <Typography variant="h4" sx={{ fontWeight: 900, mb: 1 }}>{isAuthenticated ? 'REQUESTER' : 'LOGIN'}</Typography>
            <Typography variant="body2" sx={{ mb: 4, color: theme.palette.text.secondary, maxWidth: "320px" }}>
              {isAuthenticated ? "Got questions? Outsource your logic to our human network." : "Re-enter the marketplace."}
            </Typography>
            <Button onClick={() => navigate(isAuthenticated ? "/chat/new" : "/login")} sx={{ ...buttonBase(true) }}>
              {isAuthenticated ? 'Create Chat' : 'Log In'}
            </Button>
          </Box>
          
          <Box sx={{ ...subSectionStyle, p: { xs: 4, md: 8 }, textAlign: 'center' }}>
            <Typography variant="h4" sx={{ fontWeight: 900, mb: 1 }}>{isAuthenticated ? 'RESPONDER' : 'REGISTER'}</Typography>
            <Typography variant="body2" sx={{ mb: 4, color: theme.palette.text.secondary, maxWidth: "320px" }}>
                {isAuthenticated ? "Ready to work? Solve tasks and secure your tokens." : "Start monetizing your brainpower."}
            </Typography>
            <Button onClick={() => navigate(isAuthenticated ? "/tasks/claim" : "/register")} sx={{ ...buttonBase(false) }}>
              {isAuthenticated ? 'Claim Tasks' : 'Sign Up'}
            </Button>
          </Box>
        </Box>
      </ScrollSection>

      {/* 3. Economy Section */}
      {isAuthenticated && (
        <ScrollSection index={3}>
          <Box sx={{ 
            mt: 4, mb: 8, p: { xs: 4, md: 6 }, border: `2px solid ${theme.palette.text.primary}`, 
            bgcolor: bannerBg, color: bannerText, position: 'relative', overflow: 'hidden',
            transition: 'all 0.4s ease', '&:hover': { transform: animationsEnabled ? 'translateY(-10px)' : 'none', boxShadow: sectionShadow }
          }}>
            <Grid container spacing={4} alignItems="center" sx={{ position: 'relative', zIndex: 2 }}>
              <Grid item xs={12} md={5}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <SecurityIcon sx={{ color: bannerText }} />
                  <Typography variant="overline" sx={{ fontWeight: 900, letterSpacing: 3, color: bannerText }}>TOKENOMICS</Typography>
                </Box>
                <Typography variant="h4" sx={{ fontWeight: 900, mb: 1, color: bannerText }}>RESERVE MANAGEMENT</Typography>
                <Typography variant="body2" sx={{ opacity: 0.8, color: bannerText }}>
                  Refill your digital wallet to keep the intelligence flowing.
                </Typography>
              </Grid>
              
              <Grid item xs={12} md={3} sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                <Button 
                  onClick={() => navigate("/tokens")} 
                  startIcon={<TokenIcon sx={{ transition: '0.4s ease' }} />}
                  sx={{ 
                    border: `2px solid ${bannerOutline}`, borderRadius: 0, px: 6, py: 2.5,
                    color: bannerText, fontWeight: 900, fontSize: '1.1rem',
                    position: 'relative', overflow: 'hidden', width: '100%',
                    transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
                    '&:hover': { 
                      bgcolor: 'rgba(255, 255, 255, 0.1)', 
                      borderColor: bannerText,
                      transform: 'scale(1.02)',
                      '& .MuiButton-startIcon': { transform: 'rotate(180deg) scale(1.2)' }
                    },
                    '&::after': {
                      content: '""', position: 'absolute', top: 0, left: '-100%', width: '100%', height: '100%',
                      background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent)',
                      transition: '0.5s'
                    },
                    '&:hover::after': { left: '100%' }
                  }}
                >
                  BUY TOKENS ◈
                </Button>
              </Grid>

              <Box sx={{ 
                position: 'absolute', right: '-20px', top: 0, bottom: 0, width: '350px',
                display: { xs: 'none', md: 'flex' }, alignItems: 'center', justifyContent: 'flex-end', zIndex: 1
              }}>
                {(isMeowing || isPurring) && animationsEnabled && (
                  <Typography 
                    sx={{ 
                      position: 'absolute', top: '20%', right: '40%', fontWeight: 900, color: bannerText,
                      animation: 'floatUp 0.6s ease-out forwards', pointerEvents: 'none', zIndex: 10
                    }}>
                    {isPurring ? 'PURRR!' : 'MEOW!'}
                  </Typography>
                )}
                
                <Box 
                  component="img" src={catEconomy} onMouseEnter={handleHover} onClick={handleClick}
                  sx={{
                    height: '130%', width: 'auto', filter: isDarkMode ? 'none' : 'invert(1) brightness(1.2)',
                    transition: 'all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)', cursor: 'pointer',
                    transform: `translateX(30px) ${isShaking ? 'rotate(3deg)' : ''}`,
                    '&:hover': { transform: 'translateX(5px) scale(1.05)' },
                    animation: (animationsEnabled && isShaking) ? 'shake 0.1s infinite' : 'none',
                  }}
                />
              </Box>
            </Grid>
          </Box>
        </ScrollSection>
      )}

      {/* 4. Footer */}
      <ScrollSection index={4}>
        <Typography variant="caption" sx={{ mt: 4, display: 'block', textAlign: 'center', opacity: 0.5, fontWeight: 700 }}>
          © 2026 ACTUAL INTELLIGENCE — POWERED BY HUMAN INTELLIGENCE
        </Typography>
      </ScrollSection>

      <style>
        {`
          @keyframes floatUp {
            0% { opacity: 0; transform: translateY(20px) scale(0.5); }
            50% { opacity: 1; }
            100% { opacity: 0; transform: translateY(-60px) scale(1); }
          }
          @keyframes shake {
            0% { transform: translateX(30px) rotate(0deg); }
            25% { transform: translateX(28px) rotate(-4deg); }
            75% { transform: translateX(32px) rotate(4deg); }
            100% { transform: translateX(30px) rotate(0deg); }
          }
        `}
      </style>
    </Container>
  );
}