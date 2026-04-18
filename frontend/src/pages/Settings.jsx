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
        opacity: !animationsEnabled || isVisible ? 1 : 0,
        transform: !animationsEnabled ? "none" : (isVisible ? "translateX(0)" : `translateX(${isEven ? "-50px" : "50px"})`),
        transition: animationsEnabled ? "all 0.8s cubic-bezier(0.16, 1, 0.3, 1), transform 0.4s ease-out" : "none",
        transitionDelay: animationsEnabled ? `${delay}ms` : "0ms",
        width: "100%",
        mb: 4,
        '&:hover': { transform: (animationsEnabled && isVisible) ? 'scale(1.01)' : 'none', zIndex: 5 }
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

  const [accessData, setAccessData] = useState({
    animations: localStorage.getItem("ui-animations") !== "false",
    darkMode: localStorage.getItem("ui-darkmode") === "true"
  });
  const [accessFeedback, setAccessFeedback] = useState(null);

  const themeOptions = [
    { 
        id: 'default', name: 'SYSTEM DEFAULT', 
        preview: { primary: '#000', accent: '#00e5ff', bg: '#fff', text: '#000' }
    },
    { 
        id: 'matrix', name: 'CYBER MATRIX', 
        preview: { primary: '#00ff41', accent: '#003b00', bg: '#0d0d0d', text: '#00ff41' }
    },
    { 
        id: 'vibe', name: 'RETRO VIBE', 
        preview: { primary: '#ff00ff', accent: '#00ffff', bg: '#1a1a2e', text: '#ff00ff' }
    },
    { 
        id: 'fluffy', name: 'FLUFFY', 
        preview: { primary: '#ffafbd', accent: '#ffc3a0', bg: '#fff5f7', text: '#ff80ab' }
    },
    { 
        id: 'warm', name: 'WARM HEARTH', 
        preview: { primary: '#d35400', accent: '#f39c12', bg: '#fdf5e6', text: '#5d4037' }
    },
    { 
        id: 'blood', name: 'BLOOD PROTOCOL', 
        preview: { primary: '#ff5252', accent: '#4a0000', bg: '#0a0a0a', text: '#ff5252' }
    },
  ];

  const triggerFeedback = (setter, type) => {
    setter(type);
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
    localStorage.setItem("ui-darkmode", isNowDark.toString());
    
    setThemeMode(localTheme);
    localStorage.setItem("ui-theme", localTheme);
    triggerFeedback(setThemeFeedback, 'save');
    
    window.dispatchEvent(new Event("storage"));
  };

  const handleThemeReset = () => {
    setLocalTheme("default");
    setThemeMode("default");
    localStorage.setItem("ui-theme", "default");
    triggerFeedback(setThemeFeedback, 'reset');
  };

  const handleAccessSave = () => {
    localStorage.setItem("ui-animations", accessData.animations);
    localStorage.setItem("ui-darkmode", accessData.darkMode);
    triggerFeedback(setAccessFeedback, 'save');
    window.dispatchEvent(new Event("storage")); 
  };

  const handleAccessReset = () => {
    const defaults = { animations: true, darkMode: isDarkMode };
    setAccessData(defaults);
    localStorage.setItem("ui-animations", "true");
    localStorage.setItem("ui-darkmode", isDarkMode.toString());
    triggerFeedback(setAccessFeedback, 'reset');
    window.dispatchEvent(new Event("storage"));
  };

  const buttonBase = (isPrimary) => ({
    py: 1, px: 3, borderRadius: 0, textTransform: "uppercase",
    fontSize: "0.75rem", fontWeight: 900, letterSpacing: "2px",
    border: `2px solid ${theme.palette.text.primary}`,
    bgcolor: isPrimary ? theme.palette.text.primary : "transparent",
    color: isPrimary ? theme.palette.background.default : theme.palette.text.primary,
    transition: accessData.animations ? "all 0.2s ease" : "none",
    "&:hover": {
      bgcolor: isPrimary ? theme.palette.action.hover : theme.palette.text.primary,
      color: theme.palette.background.default,
      transform: accessData.animations ? "translateY(-2px)" : "none",
    },
  });

  const feedbackTextStyle = (status) => ({
    fontWeight: 900, color: status === 'reset' ? theme.palette.text.secondary : theme.palette.primary.main, 
    textAlign: 'right', textTransform: 'uppercase', letterSpacing: '2px', fontSize: '0.7rem', mt: 1
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

  return (
    <Container maxWidth="lg" sx={{ minHeight: "100vh", py: 8 }}>
      
      <ScrollSection index={0}>
        <Box sx={{ textAlign: 'center', mb: 8 }}>
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 2, mb: -1 }}>
            <Divider sx={{ width: 40, borderBottomWidth: 3, borderColor: theme.palette.text.primary }} />
            <Typography variant="overline" sx={{ fontWeight: 900, letterSpacing: 4 }}>System.v1</Typography>
            <Divider sx={{ width: 40, borderBottomWidth: 3, borderColor: theme.palette.text.primary }} />
          </Box>
          <Typography variant="h2" sx={{ fontWeight: 900, letterSpacing: "-2px" }}>
            <span style={{ color: theme.palette.text.disabled }}>CORE</span> SETTINGS
          </Typography>
        </Box>
      </ScrollSection>

      {/* 1. Text Scaling */}
      <ScrollSection index={1}>
        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, border: `3px solid ${theme.palette.text.primary}`, bgcolor: theme.palette.background.paper }}>
          <Box sx={{ flex: 0.3, p: 4, bgcolor: isDarkMode ? 'rgba(255,255,255,0.03)' : '#f9f9f9', borderRight: { md: `3px solid ${theme.palette.text.primary}` } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <TextFieldsIcon fontSize="small" sx={{ color: theme.palette.text.disabled }} />
                <Typography variant="overline" sx={{ fontWeight: 900, color: theme.palette.text.disabled }}>01 // Visuals</Typography>
              </Box>
              <Typography variant="h5" sx={{ fontWeight: 900, mb: 1 }}>TEXT SCALING</Typography>
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
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
              <Button startIcon={<RestartAltIcon />} onClick={handleScaleReset} sx={buttonBase(false)}>Reset</Button>
              <Button startIcon={<SaveIcon />} onClick={handleScaleSave} sx={buttonBase(true)}>Save</Button>
            </Box>
          </Box>
        </Box>
        <Box sx={{ height: '30px' }}><Fade in={!!scaleFeedback}><Typography sx={feedbackTextStyle(scaleFeedback)}>{scaleFeedback === 'reset' ? '[ RESTORED ]' : '[ CALIBRATED ]'}</Typography></Fade></Box>
      </ScrollSection>

      {/* 2. Theme Mode */}
      <ScrollSection index={2}>
        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, border: `3px solid ${theme.palette.text.primary}`, bgcolor: theme.palette.background.paper }}>
          <Box sx={{ flex: 0.3, p: 4, bgcolor: isDarkMode ? 'rgba(255,255,255,0.03)' : '#f9f9f9', borderRight: { md: `3px solid ${theme.palette.text.primary}` } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <PaletteIcon fontSize="small" sx={{ color: theme.palette.text.disabled }} />
                <Typography variant="overline" sx={{ fontWeight: 900, color: theme.palette.text.disabled }}>02 // Environment</Typography>
              </Box>
              <Typography variant="h5" sx={{ fontWeight: 900, mb: 1 }}>THEME MODE</Typography>
          </Box>
          <Box sx={{ flex: 0.7, p: 4, display: 'flex', flexDirection: 'column', gap: 4 }}>
            <Grid container spacing={2} justifyContent="center">
              {themeOptions.map((option) => (
                <Grid item key={option.id}>
                  <Box 
                    onClick={() => setLocalTheme(option.id)}
                    sx={{
                      cursor: 'pointer', width: '140px', height: '80px', p: 1.5, 
                      bgcolor: option.preview.bg, 
                      border: localTheme === option.id ? `4px solid ${theme.palette.text.primary}` : `1px solid ${theme.palette.divider}`,
                      transition: accessData.animations ? '0.2s' : 'none', display: 'flex', flexDirection: 'column', justifyContent: 'space-between'
                    }}
                  >
                    <Typography sx={{ fontWeight: 900, fontSize: '0.6rem', color: option.preview.text }}>{option.name}</Typography>
                    <Box sx={{ display: 'flex', gap: 0.5 }}>
                        <Box sx={{ width: 10, height: 10, bgcolor: option.preview.primary }} />
                        <Box sx={{ width: 10, height: 10, bgcolor: option.preview.accent }} />
                    </Box>
                  </Box>
                </Grid>
              ))}
            </Grid>
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
              <Button startIcon={<RestartAltIcon />} onClick={handleThemeReset} sx={buttonBase(false)}>Reset</Button>
              <Button startIcon={<SaveIcon />} onClick={handleThemeSave} sx={buttonBase(true)}>Save</Button>
            </Box>
          </Box>
        </Box>
        <Box sx={{ height: '30px' }}><Fade in={!!themeFeedback}><Typography sx={feedbackTextStyle(themeFeedback)}>{themeFeedback === 'reset' ? '[ RESET ]' : '[ ENVIRONMENT UPDATED ]'}</Typography></Fade></Box>
      </ScrollSection>

      {/* 3. Accessibility */}
      <ScrollSection index={3}>
        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, border: `3px solid ${theme.palette.text.primary}`, bgcolor: theme.palette.background.paper }}>
          <Box sx={{ flex: 0.3, p: 4, bgcolor: isDarkMode ? 'rgba(255,255,255,0.03)' : '#f9f9f9', borderRight: { md: `3px solid ${theme.palette.text.primary}` } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <SettingsAccessibilityIcon fontSize="small" sx={{ color: theme.palette.text.disabled }} />
                <Typography variant="overline" sx={{ fontWeight: 900, color: theme.palette.text.disabled }}>03 // Logic</Typography>
              </Box>
              <Typography variant="h5" sx={{ fontWeight: 900, mb: 1 }}>ACCESSIBILITY</Typography>
          </Box>
          <Box sx={{ flex: 0.7, p: 0, display: 'flex', flexDirection: 'column' }}>
            {[
              { icon: <GraphicEqIcon />, label: 'ANIMATIONS', key: 'animations' },
              { icon: <Brightness4Icon />, label: 'FORCE DARK MODE', key: 'darkMode' }
            ].map((item, idx) => (
              <Box key={item.key} sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', p: 2.5, borderBottom: idx === 0 ? `1px solid ${theme.palette.divider}` : 'none' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    {item.icon}
                    <Typography variant="body2" sx={{ fontWeight: 900 }}>{item.label}</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <StatusLabel active={accessData[item.key]} />
                    <Switch sx={customSwitch} checked={accessData[item.key]} onChange={(e) => setAccessData({...accessData, [item.key]: e.target.checked})} />
                </Box>
              </Box>
            ))}
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end', p: 3 }}>
              <Button startIcon={<RestartAltIcon />} onClick={handleAccessReset} sx={buttonBase(false)}>Reset</Button>
              <Button startIcon={<SaveIcon />} onClick={handleAccessSave} sx={buttonBase(true)}>Save</Button>
            </Box>
          </Box>
        </Box>
        <Box sx={{ height: '30px' }}><Fade in={!!accessFeedback}><Typography sx={feedbackTextStyle(accessFeedback)}>{accessFeedback === 'reset' ? '[ REVERTED ]' : '[ COMMITTED ]'}</Typography></Fade></Box>
      </ScrollSection>
    </Container>
  );
}