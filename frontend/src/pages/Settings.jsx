import { useState, useEffect, useRef } from "react";
import { 
  Box, Container, Typography, Divider, MenuItem, TextField, Button, Fade
} from "@mui/material";
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

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
        '&:hover': { transform: isVisible ? 'scale(1.01)' : undefined, zIndex: 5 }
      }}
    >
      {children}
    </Box>
  );
};

export default function Settings({ setTextScale }) {
  const [localScale, setLocalScale] = useState(localStorage.getItem("ui-scale") || "medium");
  const [showSuccess, setShowSuccess] = useState(false);

  const handleScaleChange = (event) => {
    setLocalScale(event.target.value);
    setShowSuccess(false);
  };

  const handleReset = () => {
    setLocalScale("medium");
    setTextScale("medium");
    localStorage.setItem("ui-scale", "medium");
    setShowSuccess(false);
  };

  const handleSave = () => {
    setTextScale(localScale);
    localStorage.setItem("ui-scale", localScale);
    setShowSuccess(true);
    setTimeout(() => setShowSuccess(false), 4000);
  };

  const buttonBase = (isPrimary) => ({
    py: 1.5, px: 4, borderRadius: "0px", textTransform: "uppercase",
    fontSize: "0.8rem", fontWeight: 900, letterSpacing: "2px",
    transition: "all 0.2s ease-in-out", border: "2px solid black",
    bgcolor: isPrimary ? "black" : "transparent",
    color: isPrimary ? "white" : "black",
    "&:hover": {
      bgcolor: isPrimary ? "#333" : "black", color: "white",
      transform: "translateY(-2px)", boxShadow: "6px 6px 0px rgba(0,0,0,0.1)",
    },
  });

  return (
    <Container maxWidth="lg" sx={{ minHeight: "100vh", display: 'flex', flexDirection: 'column', py: 8 }}>
      {/* Header Section */}
      <ScrollSection index={0}>
        <Box sx={{ textAlign: 'center', mb: 8 }}>
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 2, mb: -1 }}>
            <Divider sx={{ width: 40, borderBottomWidth: 3, borderColor: 'black' }} />
            <Typography variant="overline" sx={{ fontWeight: 900, letterSpacing: 4 }}>System.v1</Typography>
            <Divider sx={{ width: 40, borderBottomWidth: 3, borderColor: 'black' }} />
          </Box>
          <Typography variant="h2" sx={{ fontWeight: 900, letterSpacing: "-2px" }}>
            <span style={{ color: '#bbb' }}>CORE</span> SETTINGS
          </Typography>
        </Box>
      </ScrollSection>

      {/* Main Settings Box */}
      <ScrollSection index={1}>
        <Box sx={{ 
            display: 'flex', flexDirection: { xs: 'column', md: 'row' }, border: '3px solid black', bgcolor: 'white',
            transition: 'all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1)',
            '&:hover': { transform: 'scale(1.01)', boxShadow: '15px 15px 0px rgba(0,0,0,0.05)' }
        }}>
          <Box sx={{ flex: 0.3, p: 4, bgcolor: '#f9f9f9', borderRight: { md: '3px solid black' }, borderBottom: { xs: '3px solid black', md: 'none' } }}>
              <Typography variant="overline" sx={{ fontWeight: 900, color: '#bbb' }}>01 // UI Parameters</Typography>
              <Typography variant="h5" sx={{ fontWeight: 900, mb: 2, mt: 1 }}>TEXT SCALING</Typography>
          </Box>

          <Box sx={{ flex: 0.7, p: 6, display: 'flex', flexDirection: 'column', gap: 3 }}>
            <TextField
              select label="SCALE SELECTION" value={localScale} onChange={handleScaleChange} variant="outlined" fullWidth
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 0, fontWeight: 900,
                  '& fieldset': { borderWidth: '2px', borderColor: 'black' },
                }
              }}
            >
              <MenuItem value="small">SMALL (12px)</MenuItem>
              <MenuItem value="medium">MEDIUM (16px)</MenuItem>
              <MenuItem value="large">LARGE (20px)</MenuItem>
            </TextField>

            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
              <Button onClick={handleReset} sx={buttonBase(false)}>Reset</Button>
              <Button onClick={handleSave} sx={buttonBase(true)}>Save Changes</Button>
            </Box>
          </Box>
        </Box>

        {/* Success GUI Below the Section */}
        <Box sx={{ height: '80px', mt: 2 }}>
            <Fade in={showSuccess}>
                <Box sx={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: 2, 
                    bgcolor: 'black', 
                    color: '#00e5ff', 
                    p: 2, 
                    border: '2px solid #00e5ff',
                    boxShadow: '8px 8px 0px rgba(0, 229, 255, 0.2)'
                }}>
                    <CheckCircleIcon />
                    <Typography sx={{ fontWeight: 900, letterSpacing: 1, textTransform: 'uppercase' }}>
                        Global Interface Reconfigured Successfully.
                    </Typography>
                </Box>
            </Fade>
        </Box>
      </ScrollSection>
    </Container>
  );
}