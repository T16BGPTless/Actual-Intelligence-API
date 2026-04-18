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

  useEffect(() => {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => setIsVisible(entry.isIntersecting));
    }, { threshold: 0.1 });

    const currentRef = domRef.current;
    if (currentRef) observer.observe(currentRef);
    
    return () => {
      if (currentRef) observer.unobserve(currentRef);
    };
  }, []);

  const isEven = index % 2 === 0;

  return (
    <Box
      ref={domRef}
      sx={{
        opacity: isVisible ? 1 : 0,
        transform: isVisible 
          ? "translateX(0)" 
          : `translateX(${isEven ? "-50px" : "50px"})`,
        transition: "all 0.8s cubic-bezier(0.16, 1, 0.3, 1), transform 0.4s ease-out, box-shadow 0.4s ease-out",
        transitionDelay: `${delay}ms`,
        width: "100%",
        '&:hover': {
           transform: isVisible ? 'scale(1.01)' : undefined,
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
  const isDarkMode = theme.palette.mode === 'dark';
  
  // Theme Detection
  const currentThemeId = localStorage.getItem("ui-theme") || "default";
  const isDefault = currentThemeId === 'default';
  const isCyber = currentThemeId === 'matrix'; 

  const catFilter = isCyber ? 'none' : 'invert(1) brightness(1.2)';

  const sectionTextColor = isCyber ? '#000' : '#fff';
  const sectionOutlineColor = isCyber ? 'rgba(0,0,0,0.4)' : 'rgba(255,255,255,0.4)';
  const sectionHoverOutlineColor = isCyber ? '#000' : '#fff';

  const isAuthenticated = Boolean(localStorage.getItem("token"));
  const username = localStorage.getItem("username") || "User";

  const [isMeowing, setIsMeowing] = useState(false);
  const [isShaking, setIsShaking] = useState(false);
  const [isPurring, setIsPurring] = useState(false);

  const meowTimer = useRef(null);
  const purrTimer = useRef(null);

  const handleHover = () => {
    if (meowTimer.current) clearTimeout(meowTimer.current);
    setIsMeowing(false); 
    setTimeout(() => setIsMeowing(true), 10);
    meowTimer.current = setTimeout(() => setIsMeowing(false), 800);
  };

  const handleClick = () => {
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
    transition: 'all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1)',
    position: 'relative',
    '&:hover': {
      bgcolor: theme.palette.background.paper,
      zIndex: 10,
      transform: 'scale(1.03)',
      boxShadow: `0 20px 60px ${theme.palette.primary.main}33`,
    }
  };

  const userButtonStyle = {
    ml: 2, px: 3, py: 0.5,
    borderRadius: 0,
    color: sectionTextColor,
    border: `2px solid ${sectionOutlineColor}`,
    fontWeight: 900,
    fontSize: { xs: '1.2rem', md: '2.2rem' },
    lineHeight: 1.2,
    letterSpacing: '2px',
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    textTransform: 'uppercase',
    position: 'relative',
    display: 'flex',
    alignItems: 'center',
    '&:hover': {
      borderColor: sectionHoverOutlineColor,
      bgcolor: isCyber ? 'rgba(0, 0, 0, 0.05)' : 'rgba(255, 255, 255, 0.1)',
      transform: 'translateY(-2px)',
      boxShadow: `0 5px 15px ${isCyber ? 'rgba(0,0,0,0.1)' : 'rgba(255, 255, 255, 0.2)'}`,
      letterSpacing: '6px',
      pl: 5,
    },
    '&::before': {
      content: '">"',
      position: 'absolute',
      left: '15px',
      opacity: 0,
      transition: 'all 0.3s ease',
    },
    '&:hover::before': {
      opacity: 1,
      left: '15px',
    }
  };

  const buttonBase = (isPrimary, isGrey = false) => ({
    py: 2, px: 4,
    width: "100%",
    maxWidth: "280px",
    borderRadius: 0,
    textTransform: "uppercase",
    fontSize: "0.9rem",
    fontWeight: 900,
    letterSpacing: "2px",
    transition: "all 0.2s ease-in-out",
    border: `2px solid ${theme.palette.text.primary}`,
    bgcolor: isGrey 
        ? theme.palette.action.disabledBackground
        : (isPrimary ? theme.palette.text.primary : "transparent"),
    color: isPrimary ? theme.palette.background.default : theme.palette.text.primary,
    "&:hover": {
      bgcolor: isPrimary ? theme.palette.text.secondary : theme.palette.text.primary,
      color: theme.palette.background.default,
      transform: "translateY(-2px)",
      boxShadow: `6px 6px 0px ${theme.palette.text.primary}44`,
    },
  });

  return (
    <Container maxWidth="lg" sx={{ minHeight: "100vh", display: 'flex', flexDirection: 'column', py: 8 }}>
      
      {/* 0. Header Section */}
      <ScrollSection index={0}>
        <Box sx={{ textAlign: 'center', mb: 8, position: 'relative' }}>
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 2, mb: -1 }}>
            <Divider sx={{ width: 40, borderBottomWidth: 3, borderColor: theme.palette.text.primary }} />
            <Typography variant="overline" sx={{ fontWeight: 900, letterSpacing: 4 }}>Cat.v1</Typography>
            <Divider sx={{ width: 40, borderBottomWidth: 3, borderColor: theme.palette.text.primary }} />
          </Box>
          <Typography variant="h2" sx={{ fontWeight: 900, letterSpacing: "-2px" }}>
            <span style={{ color: theme.palette.text.disabled }}>ACTUAL</span> INTELLIGENCE
          </Typography>
          <Typography variant="h6" sx={{ fontWeight: 500, color: theme.palette.text.secondary, mt: 1, textTransform: 'uppercase', letterSpacing: 1 }}>
            Human Logic. Ethical Processing. Verified Results.
          </Typography>
        </Box>
      </ScrollSection>

      {/* 1. Welcome / Mission Section */}
      <ScrollSection index={1}>
        {!isAuthenticated ? (
          <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, border: `3px solid ${theme.palette.text.primary}`, mb: 10, bgcolor: theme.palette.background.paper }}>
            <Box sx={{ ...subSectionStyle, p: 4, textAlign: 'left', bgcolor: 'rgba(0,0,0,0.02)', borderRight: { md: `3px solid ${theme.palette.text.primary}` } }}>
                <Typography variant="overline" sx={{ fontWeight: 900, color: theme.palette.text.disabled }}>01 // The Mission</Typography>
                <Typography variant="h5" sx={{ fontWeight: 900, mb: 2, mt: 1 }}>DECENTRALIZING COGNITION</Typography>
                <Typography variant="body2" sx={{ color: theme.palette.text.primary, lineHeight: 1.8 }}>
                    Current automated models are environmentally unsustainable and spiritually hollow. 
                    <strong> Actual Intelligence</strong> restores the human element.
                </Typography>
            </Box>
            <Box sx={{ flex: 0.8, bgcolor: theme.palette.text.primary, display: 'flex', alignItems: 'center', justifyContent: 'center', p: 4 }}>
               <Box 
                  component="img"
                  src={catIntro}
                  sx={{
                    maxHeight: "150px",
                    width: "auto",
                    filter: catFilter,
                    objectFit: "contain"
                  }}
                />
            </Box>
          </Box>
        ) : (
          <Box sx={{ 
            display: 'flex', 
            border: `3px solid ${theme.palette.text.primary}`, 
            mb: 10, 
            bgcolor: isDefault ? '#000' : theme.palette.primary.main, 
            height: { xs: 'auto', md: '250px' }, 
            overflow: 'hidden' 
          }}>
              <Box sx={{ flex: 1.2, display: { xs: 'none', md: 'block' }, position: 'relative', p: 2 }}>
                <Box sx={{
                  width: '100%', height: '100%',
                  backgroundImage: `url(${catLeft})`,
                  backgroundSize: 'contain', backgroundRepeat: 'no-repeat', backgroundPosition: 'center right',
                  filter: catFilter,
                  WebkitMaskImage: 'linear-gradient(to right, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 90%)',
                  maskImage: 'linear-gradient(to right, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 90%)'
                }} />
              </Box>

              <Box sx={{ flex: 3, p: 6, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', color: sectionTextColor, zIndex: 1 }}>
                  <Typography variant="overline" sx={{ letterSpacing: 3, opacity: 0.7, mb: 1 }}>Connection Established // Session Active</Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', flexWrap: 'wrap' }}>
                    <Typography variant="h3" sx={{ fontWeight: 900, letterSpacing: '-1px' }}>WELCOME,</Typography>
                    <Button onClick={() => navigate("/profile")} sx={userButtonStyle}>{username}</Button>
                  </Box>
                  <Typography variant="body1" sx={{ color: sectionTextColor, opacity: 0.8, maxWidth: '500px', lineHeight: 1.6, mt: 3 }}>
                      Your workspace is synchronized. Proceed to interface with the human intelligence network.
                  </Typography>
              </Box>

              <Box sx={{ flex: 1.2, display: { xs: 'none', md: 'block' }, position: 'relative', p: 2 }}>
                <Box sx={{
                  width: '100%', height: '100%',
                  backgroundImage: `url(${catRight})`,
                  backgroundSize: 'contain', backgroundRepeat: 'no-repeat', backgroundPosition: 'center left',
                  filter: catFilter,
                  WebkitMaskImage: 'linear-gradient(to left, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 90%)',
                  maskImage: 'linear-gradient(to left, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 90%)'
                }} />
              </Box>
          </Box>
        )}
      </ScrollSection>

      {/* 2. Main Dashboard Panel */}
      <ScrollSection index={2}>
        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, borderTop: `3px solid ${theme.palette.text.primary}`, borderBottom: `3px solid ${theme.palette.text.primary}`, bgcolor: theme.palette.background.default, mb: 8, overflow: 'visible' }}>
          
          <Box sx={{ ...subSectionStyle, p: { xs: 4, md: 8 }, display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
            <Typography variant="h4" sx={{ fontWeight: 900, mb: 2 }}>{isAuthenticated ? 'REQUESTER' : 'LOGIN'}</Typography>
            <Typography variant="body2" sx={{ mb: 4, color: theme.palette.text.secondary, maxWidth: "320px", lineHeight: 1.8 }}>
              {isAuthenticated ? "Deploy tasks to our global network of specialists." : "Securely re-authenticate your session."}
            </Typography>
            <Button onClick={() => navigate(isAuthenticated ? "/chat/new" : "/login")} sx={{ ...buttonBase(true), mt: 'auto' }}>
              {isAuthenticated ? 'Create Chat' : 'Log In'}
            </Button>
          </Box>

          <Divider orientation="vertical" flexItem sx={{ borderRightWidth: 3, borderColor: theme.palette.text.primary, display: { xs: 'none', md: 'block' }, zIndex: 11 }} />
          
          <Box sx={{ ...subSectionStyle, p: { xs: 4, md: 8 }, display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
            <Typography variant="h4" sx={{ fontWeight: 900, mb: 2 }}>{isAuthenticated ? 'RESPONDER' : 'REGISTER'}</Typography>
            <Typography variant="body2" sx={{ mb: 4, color: theme.palette.text.secondary, maxWidth: "320px", lineHeight: 1.8 }}>
                {isAuthenticated ? "Monetize your unique cognitive abilities." : "Join the premier marketplace for sustainable labor."}
            </Typography>
            <Button onClick={() => navigate(isAuthenticated ? "/tasks/claim" : "/register")} sx={{ ...buttonBase(false), mt: 'auto' }}>
              {isAuthenticated ? 'Claim Tasks' : 'Sign Up'}
            </Button>
          </Box>
        </Box>
      </ScrollSection>

      {/* 3. Economy Section */}
      {isAuthenticated && (
        <ScrollSection index={3}>
          <Box sx={{ 
            mt: 4, mb: 8, p: { xs: 4, md: 6 }, 
            border: `2px solid ${theme.palette.text.primary}`, 
            bgcolor: isDefault ? '#000' : theme.palette.primary.main, 
            color: sectionTextColor,
            position: 'relative',
            overflow: 'hidden',
            transition: 'transform 0.4s ease',
            '&:hover': { transform: 'translateY(-10px)', boxShadow: `0 20px 40px ${theme.palette.text.primary}33` }
          }}>
            <Typography variant="h1" sx={{ 
              position: 'absolute', right: -20, bottom: -40, 
              fontWeight: 900, opacity: isCyber ? 0.05 : 0.15, color: isCyber ? '#000' : '#fff',
              userSelect: 'none', zIndex: 0
            }}>
              ◈
            </Typography>

            <Grid container spacing={4} alignItems="center" sx={{ position: 'relative', zIndex: 2 }}>
              <Grid item xs={12} md={5}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <SecurityIcon sx={{ color: isDefault ? '#FFD700' : 'inherit' }} />
                  <Typography variant="overline" sx={{ fontWeight: 900, letterSpacing: 3 }}>
                    TOKENOMICS
                  </Typography>
                </Box>
                <Typography variant="h4" sx={{ fontWeight: 900, mb: 2, letterSpacing: '-1px' }}>
                  RESERVE MANAGEMENT
                </Typography>
                <Typography variant="body2" sx={{ opacity: 0.8, maxWidth: '450px', lineHeight: 1.8 }}>
                  Gather more tokens to allocate your Tasks.
                </Typography>
              </Grid>

              <Grid item xs={12} md={3} sx={{ display: 'flex', justifyContent: { md: 'flex-start' }, alignItems: 'center' }}>
                <Button 
                  onClick={() => navigate("/tokens")} 
                  startIcon={<TokenIcon sx={{ transition: '0.3s' }} />}
                  sx={{ 
                    border: `2px solid ${sectionOutlineColor}`,
                    borderRadius: 0,
                    px: 6, py: 2.5,
                    color: sectionTextColor,
                    fontWeight: 900,
                    fontSize: '1.1rem',
                    letterSpacing: '2px',
                    transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
                    position: 'relative',
                    overflow: 'hidden',
                    zIndex: 3,
                    '&:hover': {
                      color: sectionTextColor, 
                      bgcolor: isCyber ? 'rgba(0,0,0,0.05)' : 'rgba(255, 255, 255, 0.1)',
                      boxShadow: `0 0 20px ${isCyber ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.2)'}`,
                      borderColor: sectionHoverOutlineColor,
                      transform: 'scale(1.02)',
                      '& .MuiButton-startIcon': {
                        transform: 'rotate(180deg) scale(1.2)',
                      }
                    },
                    '&::after': {
                      content: '""',
                      position: 'absolute',
                      top: 0, left: '-100%',
                      width: '100%', height: '100%',
                      background: `linear-gradient(90deg, transparent, ${isCyber ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.2)'}, transparent)`,
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
                display: { xs: 'none', md: 'flex' },
                alignItems: 'center', justifyContent: 'flex-end',
                pointerEvents: 'none', zIndex: 1
              }}>
                {(isMeowing || isPurring) && (
                  <Typography 
                    key={Math.random()} 
                    sx={{ 
                      position: 'absolute', 
                      top: `${Math.floor(Math.random() * 20) + 10}%`,
                      right: '45%',
                      fontWeight: 900, color: sectionTextColor,
                      fontSize: isPurring ? '1.5rem' : '1.2rem',
                      animation: 'floatUp 0.6s ease-out forwards',
                      textShadow: isCyber ? 'none' : '0 0 10px rgba(0,0,0,0.4)',
                      pointerEvents: 'none', zIndex: 10,
                      transform: `rotate(${Math.floor(Math.random() * 40) - 20}deg)`
                    }}>
                    {isPurring ? 'PURRR!' : 'MEOW!'}
                  </Typography>
                )}
                
                <Box 
                  component="img"
                  src={catEconomy}
                  onMouseEnter={handleHover}
                  onClick={handleClick}
                  sx={{
                    height: '130%', width: 'auto',
                    filter: catFilter,
                    transition: 'all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)',
                    cursor: 'pointer', pointerEvents: 'auto',
                    transform: `translateX(30px) ${isShaking ? 'rotate(3deg)' : ''}`,
                    '&:hover': { transform: 'translateX(5px) scale(1.05)' },
                    animation: isShaking ? 'shake 0.1s infinite' : 'none',
                  }}
                />
              </Box>
            </Grid>
          </Box>
        </ScrollSection>
      )}

      {/* 4. Footer */}
      <ScrollSection index={4}>
        <Typography variant="caption" sx={{ mt: 4, display: 'block', textAlign: 'center', opacity: 0.5, fontWeight: 700, color: theme.palette.text.primary }}>
          © 2026 ACTUAL INTELLIGENCE — POWERED BY HUMAN INTELLIGENCE
        </Typography>
      </ScrollSection>

      <style>
        {`
          @keyframes floatUp {
            0% { opacity: 0; transform: translateY(20px) scale(0.5); }
            20% { opacity: 1; transform: translateY(0) scale(1.2); }
            100% { opacity: 0; transform: translateY(-60px) scale(1); }
          }
          @keyframes shake {
            0%, 100% { transform: translateX(30px) rotate(0deg); }
            25% { transform: translateX(28px) rotate(-4deg); }
            75% { transform: translateX(32px) rotate(4deg); }
          }
        `}
      </style>
    </Container>
  );
}