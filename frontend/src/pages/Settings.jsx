import { useState, useEffect, useRef } from "react";
import { 
  Box, Container, Typography, Divider, MenuItem, TextField, Button, Fade, Grid, useTheme, Switch
} from "@mui/material";
import { ScrollSection } from "../helpers.jsx"

// Icons
import TextFieldsIcon from '@mui/icons-material/TextFields';
import PaletteIcon from '@mui/icons-material/Palette';
import SettingsAccessibilityIcon from '@mui/icons-material/SettingsAccessibility';
import GraphicEqIcon from '@mui/icons-material/GraphicEq'; 
import Brightness4Icon from '@mui/icons-material/Brightness4'; 
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import SaveIcon from '@mui/icons-material/Save';
import CoffeeIcon from '@mui/icons-material/Coffee';

// Assets
import cat1 from "../assets/cat1.png";
import cat3 from "../assets/cat3.png";
import cat4 from "../assets/cat4.png";
import cat5 from "../assets/cat5.png";
import cat6 from "../assets/cat6.png";

export default function Settings({ setTextScale, setThemeMode, setForceDark }) {
  const theme = useTheme();
  const isDarkMode = theme.palette.mode === 'dark';
  const animationsEnabled = localStorage.getItem("ui-animations") !== "false";
  
  const [localScale, setLocalScale] = useState(localStorage.getItem("ui-scale") || "medium");
  const [scaleFeedback, setScaleFeedback] = useState(null);
  const [localTheme, setLocalTheme] = useState(localStorage.getItem("ui-theme") || "default");
  const [themeFeedback, setThemeFeedback] = useState(null);
  const [accessData, setAccessData] = useState({
    animations: localStorage.getItem("ui-animations") !== "false",
    darkMode: localStorage.getItem("ui-darkmode") === "true"
  });
  const [accessFeedback, setAccessFeedback] = useState(null);
  const [isResetting, setIsResetting] = useState(false);

  const lineRef = useRef(null);
  const [scrollProgress, setScrollProgress] = useState(0);
  const [isDragging, setIsDragging] = useState(false);

  const sectionLabels = ['VISUALS', 'THEME', 'LOGIC', 'RESET'];
  const sectionsCount = sectionLabels.length;

  useEffect(() => {
    const handleScroll = () => {
      const scrollY = window.pageYOffset || document.documentElement.scrollTop;
      const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
      const progress = maxScroll > 0 ? (scrollY / maxScroll) * 100 : 0;
      setScrollProgress(progress);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    handleScroll(); 
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const scrollToPosition = (clientY, smooth = true) => {
    if (!lineRef.current) return;
    const rect = lineRef.current.getBoundingClientRect();
    let clickY = clientY - rect.top;
    clickY = Math.max(0, Math.min(clickY, rect.height)); 
    const clickProgress = clickY / rect.height;
    const totalHeight = document.documentElement.scrollHeight - window.innerHeight;
    window.scrollTo({ top: clickProgress * totalHeight, behavior: smooth ? 'smooth' : 'auto' });
  };

  const handlePointerDown = (e) => {
    setIsDragging(true);
    e.target.setPointerCapture(e.pointerId);
    scrollToPosition(e.clientY, false);
  };

  const handlePointerMove = (e) => {
    if (isDragging) scrollToPosition(e.clientY, false);
  };

  const handlePointerUp = (e) => {
    setIsDragging(false);
    e.target.releasePointerCapture(e.pointerId);
  };

  const themeOptions = [
    { id: 'default', name: 'SYSTEM DEFAULT', primary: '#000', accent: '#00e5ff', bg: '#fff', text: '#000' },
    { id: 'matrix', name: 'CYBER MATRIX', primary: '#00ff41', accent: '#003b00', bg: '#0d0d0d', text: '#00ff41' },
    { id: 'vibe', name: 'RETRO VIBE', primary: '#ff00ff', accent: '#00ffff', bg: '#1a1a2e', text: '#ff00ff' },
    { id: 'fluffy', name: 'FLUFFY', primary: '#ffafbd', accent: '#ffc3a0', bg: '#fff5f7', text: '#ff80ab' },
    { id: 'warm', name: 'WARM HEARTH', primary: '#d35400', accent: '#f39c12', bg: '#fdf5e6', text: '#5d4037' },
    { id: 'blood', name: 'BLOOD PROTOCOL', primary: '#ff5252', accent: '#4a0000', bg: '#0a0a0a', text: '#ff5252' },
  ];

  const triggerFeedback = (setter, status) => {
    setter(status);
    setTimeout(() => setter(null), 3000);
  };

  const handleScaleSave = () => {
    setTextScale(localScale);
    localStorage.setItem("ui-scale", localScale);
    triggerFeedback(setScaleFeedback, 'save');
  };

  const handleScaleReset = () => {
    setLocalScale("medium");
    setTextScale("medium");
    localStorage.setItem("ui-scale", "medium");
    triggerFeedback(setScaleFeedback, 'reset');
  };

  const handleThemeSave = () => {
    const forceDarkThemes = ['matrix', 'vibe', 'blood'];
    const isNowDark = forceDarkThemes.includes(localTheme);
    setAccessData(prev => ({ ...prev, darkMode: isNowDark }));
    setForceDark(isNowDark);
    setThemeMode(localTheme);
    localStorage.setItem("ui-darkmode", isNowDark.toString());
    localStorage.setItem("ui-theme", localTheme);
    triggerFeedback(setThemeFeedback, 'save');
    window.dispatchEvent(new Event("storage"));
  };

  const handleThemeReset = () => {
    setLocalTheme("default");
    setThemeMode("default");
    setForceDark(false);
    localStorage.setItem("ui-theme", "default");
    localStorage.setItem("ui-darkmode", "false");
    triggerFeedback(setThemeFeedback, 'reset');
  };

  const handleAccessSave = () => {
    localStorage.setItem("ui-animations", accessData.animations.toString());
    localStorage.setItem("ui-darkmode", accessData.darkMode.toString());
    setForceDark(accessData.darkMode);
    triggerFeedback(setAccessFeedback, 'save');
    window.dispatchEvent(new Event("storage")); 
  };

  const handleAccessReset = () => {
    const forceDarkThemes = ['matrix', 'vibe', 'blood'];
    const themeRequiresDark = forceDarkThemes.includes(localTheme);
    const defaults = { animations: true, darkMode: themeRequiresDark };
    setAccessData(defaults);
    setForceDark(themeRequiresDark);
    localStorage.setItem("ui-animations", "true");
    localStorage.setItem("ui-darkmode", themeRequiresDark.toString());
    triggerFeedback(setAccessFeedback, 'reset');
    window.dispatchEvent(new Event("storage"));
  };

  const handleGlobalReset = () => {
    setIsResetting(true);
    setTimeout(() => {
      localStorage.clear();
      setLocalScale("medium");
      setLocalTheme("default");
      setAccessData({ animations: true, darkMode: false });
      setTextScale("medium");
      setThemeMode("default");
      setForceDark(false);
      window.dispatchEvent(new Event("storage"));
      setIsResetting(false);
    }, 1200);
  };

  const buttonBase = (isPrimary) => ({
    py: 1, px: 3, borderRadius: 0, textTransform: "uppercase",
    fontSize: "0.75rem", fontWeight: 900, letterSpacing: "2px",
    border: `2px solid ${theme.palette.text.primary}`,
    bgcolor: isPrimary ? theme.palette.text.primary : "transparent",
    color: isPrimary ? theme.palette.background.default : theme.palette.text.primary,
    transition: "all 0.2s ease",
    "&:hover": { bgcolor: theme.palette.text.primary, color: theme.palette.background.default },
  });

  const customSwitch = {
    '& .MuiSwitch-switchBase.Mui-checked': { color: theme.palette.text.primary },
    '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': { backgroundColor: theme.palette.text.primary, opacity: 1 },
    '& .MuiSwitch-track': { borderRadius: 0, border: `1px solid ${theme.palette.text.primary}`, bgcolor: 'transparent' },
    '& .MuiSwitch-thumb': { borderRadius: 0 }
  };

  const StatusLabel = ({ active }) => (
    <Typography variant="caption" sx={{ fontWeight: 900, color: active ? theme.palette.primary.main : theme.palette.text.disabled, ml: 1, minWidth: '45px' }}>
      [ {active ? 'ON' : 'OFF'} ]
    </Typography>
  );

  const feedbackTextStyle = (status) => ({
    fontWeight: 900, color: status === 'reset' ? theme.palette.text.secondary : theme.palette.primary.main, 
    textAlign: 'right', textTransform: 'uppercase', letterSpacing: '2px', fontSize: '0.7rem', mt: 1
  });

  const sectionContainerStyle = {
    display: 'flex', flexDirection: { xs: 'column', md: 'row' }, 
    border: `3px solid ${theme.palette.text.primary}`, 
    bgcolor: theme.palette.background.paper,
    transition: 'all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1)',
    '&:hover': {
      transform: (animationsEnabled && !isResetting) ? 'scale(1.02)' : undefined,
      boxShadow: (animationsEnabled && !isResetting) ? `0 20px 60px ${theme.palette.primary.main}44` : 'none',
      zIndex: 10
    }
  };

  const centralizedCatStyle = {
    width: '140px',
    height: '140px',
    margin: '20px auto 0 auto',
    display: 'block',
    transition: 'transform 0.3s ease',
    '&:hover': { transform: 'scale(1.15)' },
  };

  const resetCatStyle = {
    width: '130px', height: '130px', position: 'absolute', top: '50%',
    transform: 'translateY(-50%)', transition: 'all 0.2s ease',
    animation: isResetting ? 'catShake 0.2s infinite' : 'none',
    '@keyframes catShake': {
      '0%': { transform: 'translateY(-50%) translateX(0)' },
      '25%': { transform: 'translateY(-50%) translateX(-10px)' },
      '50%': { transform: 'translateY(-50%) translateX(10px)' },
      '100%': { transform: 'translateY(-50%) translateX(0)' },
    },
    '&:hover': { animation: 'catShake 0.3s infinite' },
  };

  const getLatestActiveIndex = () => {
    const nodeStep = 100 / (sectionsCount - 1);
    let latest = 0;
    for (let i = 0; i < sectionsCount; i++) {
        if (scrollProgress >= (i * nodeStep) - 0.5) { latest = i; }
    }
    return latest;
  };

  const latestIdx = getLatestActiveIndex();

  return (
    <>
      {/* Side GUI */}
      <Box 
        ref={lineRef}
        sx={{
          position: 'fixed',
          left: { xs: '15px', sm: '25px', md: '40px', lg: '60px' },
          top: '50%',
          transform: 'translateY(-50%)',
          height: '40vh', 
          width: '140px', 
          display: 'flex', 
          justifyContent: 'flex-start', 
          alignItems: 'center',
          zIndex: 2000, 
          cursor: isDragging ? 'grabbing' : 'grab', 
          touchAction: 'none', 
          userSelect: 'none',
          filter: isResetting ? 'grayscale(1)' : 'none'
        }}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
      >
        <Box sx={{ position: 'absolute', top: 0, bottom: 0, left: '12px', width: '4px', bgcolor: theme.palette.text.primary, opacity: 0.1, borderRadius: '4px' }} />
        <Box sx={{ position: 'absolute', top: 0, left: '12px', width: '4px', bgcolor: theme.palette.primary.main, height: `${scrollProgress}%`, borderRadius: '4px', transition: isDragging ? 'none' : 'height 0.1s linear', boxShadow: `0 0 15px ${theme.palette.primary.main}` }} />

        {sectionLabels.map((label, i) => {
          const nodeThreshold = i * (100 / (sectionsCount - 1));
          const isFilled = scrollProgress >= (nodeThreshold - 0.5); 
          const isLatest = latestIdx === i && isFilled;

          return (
            <Box key={label} sx={{ position: 'absolute', top: `${nodeThreshold}%`, left: '14px', width: '100%', display: 'flex', alignItems: 'center', transform: 'translateY(-50%)' }}>
              <Box sx={{
                  width: '10px', height: '10px', borderRadius: '50%',
                  bgcolor: isFilled ? theme.palette.primary.main : theme.palette.background.paper,
                  border: `2px solid ${isFilled ? theme.palette.primary.main : theme.palette.text.disabled}`,
                  transition: 'all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)',
                  transform: isLatest ? 'scale(2.5)' : 'scale(1)',
                  boxShadow: isLatest ? `0 0 25px ${theme.palette.primary.main}` : 'none',
                  flexShrink: 0, marginLeft: '-5px', zIndex: 2
                }}
              />
              <Typography variant="caption" sx={{ 
                  ml: 4, letterSpacing: '3px',
                  fontWeight: isLatest ? 900 : 400,
                  fontSize: isLatest ? '0.75rem' : '0.6rem',
                  color: isLatest ? theme.palette.primary.main : theme.palette.text.disabled,
                  opacity: isFilled ? 1 : 0.3, transition: 'all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)', textTransform: 'uppercase', fontFamily: 'monospace',
                  transform: isLatest ? 'translateX(5px)' : 'translateX(0px)',
                  textShadow: isLatest ? `0 0 10px ${theme.palette.primary.main}55` : 'none'
                }}>
                {label}
              </Typography>
            </Box>
          );
        })}
      </Box>

      <Container sx={{ 
        maxWidth: "900px !important", minHeight: "100vh", py: 8, mx: "auto", 
        display: 'flex', flexDirection: 'column', alignItems: 'center',
        pl: { xs: '150px', sm: '180px', md: '0px' }, 
      }}>
        
        {/* Intro */}
        <ScrollSection index={0} isResetting={isResetting}>
          <Box sx={{ textAlign: 'center', mb: 8 }}>
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 2, mb: -1 }}>
              <Divider sx={{ width: 40, borderBottomWidth: 3, borderColor: theme.palette.text.primary }} />
              <Typography variant="overline" sx={{ fontWeight: 900, letterSpacing: 4 }}>Cat.v1</Typography>
              <Divider sx={{ width: 40, borderBottomWidth: 3, borderColor: theme.palette.text.primary }} />
            </Box>
            <Typography variant="h2" sx={{ fontWeight: 900, letterSpacing: "-2px" }}>SETTINGS</Typography>
            <Typography variant="body2" sx={{ opacity: 0.6, fontWeight: 700, letterSpacing: 1, textTransform: 'uppercase' }}>
              Personalize your interface and system logic.
            </Typography>
          </Box>
        </ScrollSection>

        {/* Section 1: Visuals */}
        <ScrollSection index={1} isResetting={isResetting}>
          <Box sx={sectionContainerStyle}>
            <Box sx={{ flex: 0.3, p: 4, bgcolor: isDarkMode ? 'rgba(255,255,255,0.03)' : '#f9f9f9', borderRight: { md: `3px solid ${theme.palette.text.primary}` } }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}><TextFieldsIcon fontSize="small" sx={{ color: theme.palette.text.disabled }} /><Typography variant="overline" sx={{ fontWeight: 900, color: theme.palette.text.disabled }}>01 // Visuals</Typography></Box>
                <Typography variant="h5" sx={{ fontWeight: 900, mb: 1 }}>TEXT SCALING</Typography>
                <Typography variant="body2" sx={{ color: theme.palette.text.secondary, lineHeight: 1.6 }}>Adjust text magnification.</Typography>
                <Box component="img" src={cat1} alt="Cat 1" sx={centralizedCatStyle} />
            </Box>
            <Box sx={{ flex: 0.7, p: { xs: 3, md: 6 }, display: 'flex', flexDirection: 'column', gap: 3 }}>
              <TextField select label="SCALE" value={localScale} onChange={(e) => setLocalScale(e.target.value)} variant="outlined" fullWidth sx={{ '& .MuiOutlinedInput-root': { borderRadius: 0 } }}>
                <MenuItem value="small">SMALL (12px)</MenuItem>
                <MenuItem value="medium">MEDIUM (16px)</MenuItem>
                <MenuItem value="large">LARGE (20px)</MenuItem>
              </TextField>
              <Box sx={{ border: `1px dashed ${theme.palette.divider}`, p: 3, textAlign: 'center', bgcolor: isDarkMode ? 'rgba(255,255,255,0.02)' : '#fafafa' }}>
                <Typography variant="caption" sx={{ display: 'block', mb: 1, color: theme.palette.text.disabled, fontWeight: 900 }}>CAT RENDER PREVIEW</Typography>
                <Typography sx={{ fontSize: localScale === 'small' ? '0.75rem' : localScale === 'large' ? '1.4rem' : '1rem', fontWeight: 900, textTransform: 'uppercase' }}>
                  {localScale === 'small' ? "Tiny kitten detected... ^._.^" : localScale === 'large' ? "ABSOLUTE CHONK UNIT INCOMING." : "Standard issue feline observed."}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                <Button startIcon={<RestartAltIcon />} onClick={handleScaleReset} sx={buttonBase(false)}>RESET</Button>
                <Button startIcon={<SaveIcon />} onClick={handleScaleSave} sx={buttonBase(true)}>SAVE CHANGES</Button>
              </Box>
            </Box>
          </Box>
          <Box sx={{ height: '30px' }}><Fade in={!!scaleFeedback}><Typography sx={feedbackTextStyle(scaleFeedback)}>{scaleFeedback === 'reset' ? '[ RESTORED ]' : '[ CALIBRATED ]'}</Typography></Fade></Box>
        </ScrollSection>

        {/* Section 2: Environment */}
        <ScrollSection index={2} isResetting={isResetting}>
          <Box sx={sectionContainerStyle}>
            <Box sx={{ flex: 0.3, p: 4, bgcolor: isDarkMode ? 'rgba(255,255,255,0.03)' : '#f9f9f9', borderRight: { md: `3px solid ${theme.palette.text.primary}` } }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}><PaletteIcon fontSize="small" sx={{ color: theme.palette.text.disabled }} /><Typography variant="overline" sx={{ fontWeight: 900, color: theme.palette.text.disabled }}>02 // Environment</Typography></Box>
                <Typography variant="h5" sx={{ fontWeight: 900, mb: 1 }}>THEME MODE</Typography>
                <Typography variant="body2" sx={{ color: theme.palette.text.secondary, lineHeight: 1.6 }}>Select chromatic profile.</Typography>
                <Box component="img" src={cat3} alt="Cat 3" sx={centralizedCatStyle} />
            </Box>
            <Box sx={{ flex: 0.7, p: 4, display: 'flex', flexDirection: 'column', gap: 4 }}>
              <Grid container spacing={2} justifyContent="center">
                {themeOptions.map((option) => (
                  <Grid item key={option.id}>
                    <Box onClick={() => setLocalTheme(option.id)} sx={{
                        cursor: 'pointer', width: { xs: '100px', sm: '140px' }, height: '80px', p: 1.5, bgcolor: option.bg, 
                        border: localTheme === option.id ? `4px solid ${theme.palette.text.primary}` : `1px solid ${theme.palette.divider}`,
                        display: 'flex', flexDirection: 'column', justifyContent: 'space-between', transition: 'all 0.2s ease',
                        '&:hover': { transform: 'translateY(-4px)' }
                      }}>
                      <Typography sx={{ fontWeight: 900, fontSize: '0.6rem', color: option.text }}>{option.name}</Typography>
                      <Box sx={{ display: 'flex', gap: 0.5 }}><Box sx={{ width: 10, height: 10, bgcolor: option.primary }} /><Box sx={{ width: 10, height: 10, bgcolor: option.accent }} /></Box>
                    </Box>
                  </Grid>
                ))}
              </Grid>
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                <Button startIcon={<RestartAltIcon />} onClick={handleThemeReset} sx={buttonBase(false)}>RESET</Button>
                <Button startIcon={<SaveIcon />} onClick={handleThemeSave} sx={buttonBase(true)}>SAVE CHANGES</Button>
              </Box>
            </Box>
          </Box>
          <Box sx={{ height: '30px' }}><Fade in={!!themeFeedback}><Typography sx={feedbackTextStyle(themeFeedback)}>{themeFeedback === 'reset' ? '[ RESET ]' : '[ ENVIRONMENT UPDATED ]'}</Typography></Fade></Box>
        </ScrollSection>

        {/* Section 3: Logic */}
        <ScrollSection index={3} isResetting={isResetting}>
          <Box sx={sectionContainerStyle}>
            <Box sx={{ flex: 0.3, p: 4, bgcolor: isDarkMode ? 'rgba(255,255,255,0.03)' : '#f9f9f9', borderRight: { md: `3px solid ${theme.palette.text.primary}` } }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}><SettingsAccessibilityIcon fontSize="small" sx={{ color: theme.palette.text.disabled }} /><Typography variant="overline" sx={{ fontWeight: 900, color: theme.palette.text.disabled }}>03 // Logic</Typography></Box>
                <Typography variant="h5" sx={{ fontWeight: 900, mb: 1 }}>ACCESSIBILITY</Typography>
                <Typography variant="body2" sx={{ color: theme.palette.text.secondary, lineHeight: 1.6 }}>System motion and lighting.</Typography>
                <Box component="img" src={cat4} alt="Cat 4" sx={centralizedCatStyle} />
            </Box>
            <Box sx={{ flex: 0.7, p: 0, display: 'flex', flexDirection: 'column' }}>
              {[
                { icon: <GraphicEqIcon />, label: 'ANIMATIONS', key: 'animations' },
                { icon: <Brightness4Icon />, label: 'FORCE DARK MODE', key: 'darkMode' }
              ].map((item, idx) => (
                <Box key={item.key} sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', p: 2.5, borderBottom: idx === 0 ? `1px solid ${theme.palette.divider}` : 'none' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>{item.icon}<Typography variant="body2" sx={{ fontWeight: 900 }}>{item.label}</Typography></Box>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}><StatusLabel active={accessData[item.key]} /><Switch sx={customSwitch} checked={accessData[item.key]} onChange={(e) => setAccessData({...accessData, [item.key]: e.target.checked})} /></Box>
                </Box>
              ))}
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end', p: 3 }}>
                <Button startIcon={<RestartAltIcon />} onClick={handleAccessReset} sx={buttonBase(false)}>RESET</Button>
                <Button startIcon={<SaveIcon />} onClick={handleAccessSave} sx={buttonBase(true)}>SAVE CHANGES</Button>
              </Box>
            </Box>
          </Box>
          <Box sx={{ height: '30px' }}><Fade in={!!accessFeedback}><Typography sx={feedbackTextStyle(accessFeedback)}>{accessFeedback === 'reset' ? '[ REVERTED ]' : '[ COMMITTED ]'}</Typography></Fade></Box>
        </ScrollSection>

        {/* Section 4: Master Reset */}
        <ScrollSection index={4} isResetting={false}>
          <Box sx={{ 
              border: `3px solid ${isResetting ? theme.palette.primary.main : theme.palette.divider}`, p: 4, textAlign: 'center', width: '100%',
              bgcolor: isDarkMode ? 'rgba(255, 255, 255, 0.02)' : 'rgba(0, 0, 0, 0.02)',
              transition: 'all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)',
              position: 'relative', minHeight: '180px', display: 'flex', flexDirection: 'column',
              justifyContent: 'center', alignItems: 'center', overflow: 'hidden',
              transform: isResetting ? 'scale(1.05)' : 'scale(1)', zIndex: isResetting ? 100 : 1,
              '&:hover': { borderColor: theme.palette.text.primary, bgcolor: isDarkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)' }
            }}>
            <Box component="img" src={cat5} alt="Cat 5" sx={{ ...resetCatStyle, left: '15%', display: { xs: 'none', lg: 'block' } }} />
            <Typography variant="h6" sx={{ fontWeight: 900, mb: 0.5, letterSpacing: 1 }}>LOOKING FOR A FRESH START?</Typography>
            <Typography variant="body2" sx={{ mb: 3, opacity: 0.6 }}>No judgment. We'll wipe the slate clean.</Typography>
            <Button 
              startIcon={<CoffeeIcon />} onClick={handleGlobalReset} disabled={isResetting}
              sx={{ ...buttonBase(isResetting), zIndex: 2, transform: isResetting ? 'rotate(5deg) scale(0.9)' : 'rotate(0deg) scale(1)', transition: 'all 0.2s ease' }}
            >
              {isResetting ? "CLEARING..." : "DEFAULT RESET"}
            </Button>
            <Box component="img" src={cat6} alt="Cat 6" sx={{ ...resetCatStyle, right: '15%', display: { xs: 'none', lg: 'block' } }} />
          </Box>
        </ScrollSection>

        {/* Footer */}
        <ScrollSection index={5} isResetting={false}>
          <Typography variant="caption" sx={{ mt: 4, display: 'block', textAlign: 'center', opacity: 0.5, fontWeight: 700, letterSpacing: 2 }}>
            © 2026 ACTUAL INTELLIGENCE — POWERED BY HUMAN INTELLIGENCE
          </Typography>
        </ScrollSection>
      </Container>
    </>
  );
}