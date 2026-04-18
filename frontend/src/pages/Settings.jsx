import { useState, useEffect, useRef } from "react";
import { 
  Box, Container, Typography, Divider, MenuItem, TextField, Button, Fade, Grid, useTheme
} from "@mui/material";

const ScrollSection = ({ children, index, delay = 0 }) => {
  const [isVisible, setIsVisible] = useState(false);
  const domRef = useRef();

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
        opacity: isVisible ? 1 : 0,
        transform: isVisible ? "translateX(0)" : `translateX(${isEven ? "-50px" : "50px"})`,
        transition: "all 0.8s cubic-bezier(0.16, 1, 0.3, 1), transform 0.4s ease-out, box-shadow 0.4s ease-out",
        transitionDelay: `${delay}ms`,
        width: "100%",
        mb: 4,
        '&:hover': { transform: isVisible ? 'scale(1.01)' : undefined, zIndex: 5 }
      }}
    >
      {children}
    </Box>
  );
};

export default function Settings({ setTextScale, setThemeMode }) {
  const theme = useTheme();
  const isDarkMode = theme.palette.mode === 'dark';

  const [localScale, setLocalScale] = useState(localStorage.getItem("ui-scale") || "medium");
  const [scaleFeedback, setScaleFeedback] = useState(null);
  const [localTheme, setLocalTheme] = useState(localStorage.getItem("ui-theme") || "default");
  const [themeFeedback, setThemeFeedback] = useState(null);

  const themeOptions = [
    { id: 'default', name: 'SYSTEM DEFAULT', primary: '#000', accent: '#00e5ff', bg: '#fff' },
    { id: 'matrix', name: 'CYBER MATRIX', primary: '#00ff41', accent: '#003b00', bg: '#0d0d0d' },
    { id: 'vibe', name: 'RETRO VIBE', primary: '#ff00ff', accent: '#00ffff', bg: '#1a1a2e' },
    { id: 'fluffy', name: 'FLUFFY', primary: '#ffafbd', accent: '#ffc3a0', bg: '#fff5f7' },
    { id: 'warm', name: 'WARM HEARTH', primary: '#d35400', accent: '#f39c12', bg: '#fdf5e6' },
    { id: 'blood', name: 'BLOOD PROTOCOL', primary: '#ff5252', accent: '#4a0000', bg: '#0a0a0a' },
  ];

  const handleScaleSave = () => {
    setTextScale(localScale);
    localStorage.setItem("ui-scale", localScale);
    setScaleFeedback('save');
    setTimeout(() => setScaleFeedback(null), 3000);
  };

  const handleScaleReset = () => {
    setLocalScale("medium");
    setTextScale("medium");
    localStorage.setItem("ui-scale", "medium");
    setScaleFeedback('reset');
    setTimeout(() => setScaleFeedback(null), 3000);
  };

  const handleThemeSave = () => {
    setThemeMode(localTheme);
    localStorage.setItem("ui-theme", localTheme);
    setThemeFeedback('save');
    setTimeout(() => setThemeFeedback(null), 3000);
  };

  const handleThemeReset = () => {
    setLocalTheme("default");
    setThemeMode("default");
    localStorage.setItem("ui-theme", "default");
    setThemeFeedback('reset');
    setTimeout(() => setThemeFeedback(null), 3000);
  };

  const sectionContainerStyle = {
    display: 'flex', 
    flexDirection: { xs: 'column', md: 'row' }, 
    border: `3px solid ${theme.palette.text.primary}`, 
    bgcolor: theme.palette.background.paper,
    transition: 'all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1)',
    '&:hover': {
      transform: 'scale(1.02)',
      boxShadow: isDarkMode ? '0 20px 60px rgba(0,0,0,0.5)' : '20px 20px 60px rgba(0,0,0,0.1)',
    }
  };

  const buttonBase = (isPrimary) => ({
    py: 1.5, px: 4, borderRadius: "0px", textTransform: "uppercase",
    fontSize: "0.8rem", fontWeight: 900, letterSpacing: "2px",
    transition: "all 0.2s ease-in-out", border: `2px solid ${theme.palette.text.primary}`,
    bgcolor: isPrimary ? theme.palette.text.primary : "transparent",
    color: isPrimary ? theme.palette.background.default : theme.palette.text.primary,
    "&:hover": {
      bgcolor: isPrimary ? theme.palette.action.hover : theme.palette.text.primary,
      color: theme.palette.background.default,
      transform: "translateY(-2px)",
      boxShadow: `6px 6px 0px ${isDarkMode ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'}`,
    },
  });

  return (
    <Container maxWidth="lg" sx={{ minHeight: "100vh", py: 8 }}>
      
      {/* Header */}
      <ScrollSection index={0}>
        <Box sx={{ textAlign: 'center', mb: 8 }}>
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 2, mb: -1 }}>
            <Divider sx={{ width: 40, borderBottomWidth: 3, borderColor: theme.palette.text.primary }} />
            <Typography variant="overline" sx={{ fontWeight: 900, letterSpacing: 4 }}>System.v1</Typography>
            <Divider sx={{ width: 40, borderBottomWidth: 3, borderColor: theme.palette.text.primary }} />
          </Box>
          <Typography variant="h2" sx={{ fontWeight: 900, letterSpacing: "-2px" }}>
            <span style={{ color: isDarkMode ? '#555' : '#bbb' }}>CORE</span> SETTINGS
          </Typography>
        </Box>
      </ScrollSection>

      {/* 1. Text Scaling */}
      <ScrollSection index={1}>
        <Box sx={sectionContainerStyle}>
          <Box sx={{ flex: 0.3, p: 4, bgcolor: isDarkMode ? '#1a1a1a' : '#f9f9f9', borderRight: { md: `3px solid ${theme.palette.text.primary}` } }}>
              <Typography variant="overline" sx={{ fontWeight: 900, color: theme.palette.text.disabled }}>01 // Visuals</Typography>
              <Typography variant="h5" sx={{ fontWeight: 900, mb: 2, mt: 1 }}>TEXT SCALING</Typography>
              <Typography variant="body2" sx={{ color: theme.palette.text.secondary, lineHeight: 1.6 }}>
                Adjust the optical density of the interface for peak human legibility.
              </Typography>
          </Box>
          <Box sx={{ flex: 0.7, p: 6, display: 'flex', flexDirection: 'column', gap: 3 }}>
            <TextField
              select label="SCALE SELECTION" value={localScale} onChange={(e) => setLocalScale(e.target.value)} variant="outlined" fullWidth
              sx={{ '& .MuiOutlinedInput-root': { borderRadius: 0, fontWeight: 900, '& fieldset': { borderWidth: '2px', borderColor: theme.palette.text.primary } } }}
            >
              <MenuItem value="small">SMALL (12px)</MenuItem>
              <MenuItem value="medium">MEDIUM (16px)</MenuItem>
              <MenuItem value="large">LARGE (20px)</MenuItem>
            </TextField>

            <Box sx={{ 
                border: `1px dashed ${theme.palette.divider}`, 
                p: 3, textAlign: 'center', 
                bgcolor: isDarkMode ? 'rgba(255,255,255,0.02)' : '#fafafa',
                borderRadius: 0
              }}>
              <Typography variant="caption" sx={{ display: 'block', mb: 1, color: theme.palette.text.disabled, fontWeight: 900 }}>RENDER PREVIEW</Typography>
              <Typography sx={{ 
                fontSize: localScale === 'small' ? '0.75rem' : localScale === 'large' ? '1.25rem' : '1rem', 
                fontWeight: 500, 
                color: theme.palette.text.primary 
              }}>
                System calibration in progress...
              </Typography>
            </Box>

            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
              <Button onClick={handleScaleReset} sx={buttonBase(false)}>Reset</Button>
              <Button onClick={handleScaleSave} sx={buttonBase(true)}>Save Changes</Button>
            </Box>
          </Box>
        </Box>
        <Box sx={{ height: '50px', mt: 1 }}>
          <Fade in={scaleFeedback === 'save'}><Typography sx={{ fontWeight: 900, color: '#00e5ff', textAlign: 'right' }}>[ SYSTEM RE-CALIBRATED ]</Typography></Fade>
          <Fade in={scaleFeedback === 'reset'}><Typography sx={{ fontWeight: 900, color: theme.palette.text.secondary, textAlign: 'right' }}>[ SCALING RESTORED ]</Typography></Fade>
        </Box>
      </ScrollSection>

      {/* 2. Theme Mode */}
      <ScrollSection index={2}>
        <Box sx={sectionContainerStyle}>
          <Box sx={{ flex: 0.3, p: 4, bgcolor: isDarkMode ? '#1a1a1a' : '#f9f9f9', borderRight: { md: `3px solid ${theme.palette.text.primary}` } }}>
              <Typography variant="overline" sx={{ fontWeight: 900, color: theme.palette.text.disabled }}>02 // Environment</Typography>
              <Typography variant="h5" sx={{ fontWeight: 900, mb: 2, mt: 1 }}>THEME MODE</Typography>
              <Typography variant="body2" sx={{ color: theme.palette.text.secondary, lineHeight: 1.6 }}>
                Select a chromatic profile. This affects system-wide borders, shadows, and physics.
              </Typography>
          </Box>
          <Box sx={{ flex: 0.7, p: 4, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
            <Grid container spacing={2} justifyContent="center" sx={{ maxWidth: '500px' }}>
              {themeOptions.map((option) => (
                <Grid item key={option.id}>
                  <Box 
                    onClick={() => setLocalTheme(option.id)}
                    sx={{
                      cursor: 'pointer',
                      width: '150px', 
                      height: '100px',
                      display: 'flex', 
                      flexDirection: 'column', 
                      justifyContent: 'space-between',
                      p: 2,
                      bgcolor: option.bg, 
                      border: localTheme === option.id 
                        ? `4px solid ${theme.palette.text.primary}` 
                        : `1px solid ${isDarkMode ? '#444' : '#ddd'}`,
                      borderRadius: 0,
                      transition: 'all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)',
                      transform: localTheme === option.id ? 'translateY(-8px) scale(1.05)' : 'none',
                      boxShadow: localTheme === option.id ? `0 10px 20px rgba(0,0,0,0.2)` : 'none',
                      '&:hover': {
                        transform: 'translateY(-4px)',
                        borderColor: theme.palette.text.primary
                      }
                    }}
                  >
                    <Typography sx={{ 
                      fontWeight: 900, fontSize: '0.6rem', color: option.primary, letterSpacing: 1 
                    }}>
                      {option.name}
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 0.5 }}>
                      <Box sx={{ width: 12, height: 12, bgcolor: option.primary, borderRadius: 0 }} />
                      <Box sx={{ width: 12, height: 12, bgcolor: option.accent, borderRadius: 0 }} />
                    </Box>
                  </Box>
                </Grid>
              ))}
            </Grid>
            <Box sx={{ width: '100%', display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
              <Button onClick={handleThemeReset} sx={buttonBase(false)}>Reset</Button>
              <Button onClick={handleThemeSave} sx={buttonBase(true)}>Save Changes</Button>
            </Box>
          </Box>
        </Box>
        <Box sx={{ height: '50px', mt: 1 }}>
          <Fade in={themeFeedback === 'save'}><Typography sx={{ fontWeight: 900, color: '#00ff41', textAlign: 'right' }}>[ ENVIRONMENT UPDATED ]</Typography></Fade>
          <Fade in={themeFeedback === 'reset'}><Typography sx={{ fontWeight: 900, color: theme.palette.text.secondary, textAlign: 'right' }}>[ THEME RESET ]</Typography></Fade>
        </Box>
      </ScrollSection>
    </Container>
  );
}