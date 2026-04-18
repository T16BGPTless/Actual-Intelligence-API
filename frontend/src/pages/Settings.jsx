import { useState, useEffect, useRef } from "react";
import { 
  Box, Container, Typography, Divider, MenuItem, TextField, Button, Fade, Grid, useTheme, Switch
} from "@mui/material";

// Icons
import TextFieldsIcon from '@mui/icons-material/TextFields';
import PaletteIcon from '@mui/icons-material/Palette';
import SettingsAccessibilityIcon from '@mui/icons-material/SettingsAccessibility';
import GraphicEqIcon from '@mui/icons-material/GraphicEq'; 
import Brightness4Icon from '@mui/icons-material/Brightness4'; 
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import SaveIcon from '@mui/icons-material/Save';
import CoffeeIcon from '@mui/icons-material/Coffee';

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
    <Box ref={domRef} sx={{
        opacity: !animationsEnabled || isVisible ? 1 : 0,
        transform: !animationsEnabled ? "none" : (isVisible ? "translateX(0)" : `translateX(${isEven ? "-50px" : "50px"})`),
        transition: animationsEnabled ? "all 0.8s cubic-bezier(0.16, 1, 0.3, 1), transform 0.4s ease-out" : "none",
        transitionDelay: animationsEnabled ? `${delay}ms` : "0ms",
        width: "100%", mb: 4,
        '&:hover': {
           transform: (animationsEnabled && isVisible) ? 'scale(1.01)' : undefined,
           zIndex: 5,
        }
      }}>
      {children}
    </Box>
  );
};

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

  const themeOptions = [
    { id: 'default', name: 'SYSTEM DEFAULT', primary: '#000', accent: '#00e5ff', bg: '#fff', text: '#000' },
    { id: 'matrix', name: 'CYBER MATRIX', primary: '#00ff41', accent: '#003b00', bg: '#0d0d0d', text: '#00ff41' },
    { id: 'vibe', name: 'RETRO VIBE', primary: '#ff00ff', accent: '#00ffff', bg: '#1a1a2e', text: '#ff00ff' },
    { id: 'fluffy', name: 'FLUFFY', primary: '#ffafbd', accent: '#ffc3a0', bg: '#fff5f7', text: '#ff80ab' },
    { id: 'warm', name: 'WARM HEARTH', primary: '#d35400', accent: '#f39c12', bg: '#fdf5e6', text: '#5d4037' },
    { id: 'blood', name: 'BLOOD PROTOCOL', primary: '#ff5252', accent: '#4a0000', bg: '#0a0a0a', text: '#ff5252' },
  ];

  const sectionShadow = isDarkMode 
    ? `0 20px 60px ${theme.palette.primary.main}44` 
    : '0 20px 40px rgba(0,0,0,0.1)';

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
    localStorage.clear();
    setLocalScale("medium");
    setLocalTheme("default");
    setAccessData({ animations: true, darkMode: false });
    setTextScale("medium");
    setThemeMode("default");
    setForceDark(false);
    window.dispatchEvent(new Event("storage"));
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
    transition: animationsEnabled ? 'all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1)' : 'none',
    '&:hover': {
      transform: animationsEnabled ? 'scale(1.02)' : 'none',
      boxShadow: animationsEnabled ? sectionShadow : 'none',
      zIndex: 10
    }
  };

  return (
    <Container maxWidth="lg" sx={{ minHeight: "100vh", py: 8 }}>
      <ScrollSection index={0}>
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

      {/* 1. Text Scaling */}
      <ScrollSection index={1}>
        <Box sx={sectionContainerStyle}>
          <Box sx={{ flex: 0.3, p: 4, bgcolor: isDarkMode ? 'rgba(255,255,255,0.03)' : '#f9f9f9', borderRight: { md: `3px solid ${theme.palette.text.primary}` } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}><TextFieldsIcon fontSize="small" sx={{ color: theme.palette.text.disabled }} /><Typography variant="overline" sx={{ fontWeight: 900, color: theme.palette.text.disabled }}>01 // Visuals</Typography></Box>
              <Typography variant="h5" sx={{ fontWeight: 900, mb: 1 }}>TEXT SCALING</Typography>
              <Typography variant="body2" sx={{ color: theme.palette.text.secondary, lineHeight: 1.6 }}>Adjust the zoom until your eyes stop squinting.</Typography>
          </Box>
          <Box sx={{ flex: 0.7, p: 6, display: 'flex', flexDirection: 'column', gap: 3 }}>
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
              <Typography sx={{ fontSize: localScale === 'small' ? '0.7rem' : localScale === 'large' ? '1.1rem' : '0.9rem', opacity: 0.7 }}>
                If you can read this, the cat is currently sitting on your keyboard.
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

      {/* 2. Theme Mode */}
      <ScrollSection index={2}>
        <Box sx={sectionContainerStyle}>
          <Box sx={{ flex: 0.3, p: 4, bgcolor: isDarkMode ? 'rgba(255,255,255,0.03)' : '#f9f9f9', borderRight: { md: `3px solid ${theme.palette.text.primary}` } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}><PaletteIcon fontSize="small" sx={{ color: theme.palette.text.disabled }} /><Typography variant="overline" sx={{ fontWeight: 900, color: theme.palette.text.disabled }}>02 // Environment</Typography></Box>
              <Typography variant="h5" sx={{ fontWeight: 900, mb: 1 }}>THEME MODE</Typography>
              <Typography variant="body2" sx={{ color: theme.palette.text.secondary, lineHeight: 1.6 }}>Select chromatic profile.</Typography>
          </Box>
          <Box sx={{ flex: 0.7, p: 4, display: 'flex', flexDirection: 'column', gap: 4 }}>
            <Grid container spacing={2} justifyContent="center">
              {themeOptions.map((option) => (
                <Grid item key={option.id}>
                  <Box onClick={() => setLocalTheme(option.id)} sx={{
                      cursor: 'pointer', width: '140px', height: '80px', p: 1.5, bgcolor: option.bg, 
                      border: localTheme === option.id ? `4px solid ${theme.palette.text.primary}` : `1px solid ${theme.palette.divider}`,
                      display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
                      transition: 'all 0.2s ease',
                      '&:hover': { transform: 'translateY(-4px)', boxShadow: '0 4px 20px rgba(0,0,0,0.1)' }
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

      {/* 3. Accessibility */}
      <ScrollSection index={3}>
        <Box sx={sectionContainerStyle}>
          <Box sx={{ flex: 0.3, p: 4, bgcolor: isDarkMode ? 'rgba(255,255,255,0.03)' : '#f9f9f9', borderRight: { md: `3px solid ${theme.palette.text.primary}` } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}><SettingsAccessibilityIcon fontSize="small" sx={{ color: theme.palette.text.disabled }} /><Typography variant="overline" sx={{ fontWeight: 900, color: theme.palette.text.disabled }}>03 // Logic</Typography></Box>
              <Typography variant="h5" sx={{ fontWeight: 900, mb: 1 }}>ACCESSIBILITY</Typography>
              <Typography variant="body2" sx={{ color: theme.palette.text.secondary, lineHeight: 1.6 }}>System motion and lighting.</Typography>
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

      {/* 4. Casual Master Reset */}
      <ScrollSection index={4}>
        <Box sx={{ 
            border: `3px solid ${theme.palette.divider}`, p: 4, textAlign: 'center', 
            bgcolor: isDarkMode ? 'rgba(255, 255, 255, 0.02)' : 'rgba(0, 0, 0, 0.02)',
            transition: 'all 0.3s ease',
            '&:hover': {
              borderColor: theme.palette.text.primary,
              bgcolor: isDarkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)',
            }
          }}>
          <Typography variant="h6" sx={{ fontWeight: 900, mb: 0.5, letterSpacing: 1 }}>LOOKING FOR A FRESH START?</Typography>
          <Typography variant="body2" sx={{ mb: 3, opacity: 0.6 }}>No judgment. We'll wipe the slate clean and put everything back to normal.</Typography>
          <Button 
            startIcon={<CoffeeIcon />} 
            onClick={handleGlobalReset}
            sx={{ 
                ...buttonBase(false), 
                '&:hover': { bgcolor: theme.palette.text.primary, color: theme.palette.background.default }
            }}
          >
            DEFAULT RESET (ALL SECTIONS)
          </Button>
        </Box>
      </ScrollSection>

      {/* 5. Footer */}
      <ScrollSection index={5}>
        <Typography variant="caption" sx={{ mt: 4, display: 'block', textAlign: 'center', opacity: 0.5, fontWeight: 700, letterSpacing: 2 }}>
          © 2026 ACTUAL INTELLIGENCE — POWERED BY HUMAN INTELLIGENCE
        </Typography>
      </ScrollSection>
    </Container>
  );
}