import { useEffect, useRef, useState } from "react";
import { Box, useTheme } from "@mui/material";

// note buttonBase is not a helper function as it varies too much page to page
// I did try but got annoyed as very little of it was consistent - Bevyn :)

export function ScrollSection({ children, index, delay = 0 }) {
  const [isVisible, setIsVisible] = useState(false);
  const domRef = useRef();
  const animationsEnabled = localStorage.getItem("ui-animations") !== "false";

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => setIsVisible(entry.isIntersecting));
      },
      { threshold: 0.1 }
    );

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
        opacity: animationsEnabled ? (isVisible ? 1 : 0) : 1,
        transform: animationsEnabled
          ? isVisible
            ? "translateX(0)"
            : `translateX(${isEven ? "-50px" : "50px"})`
          : "none",
        transition: animationsEnabled
          ? "all 0.8s cubic-bezier(0.16, 1, 0.3, 1), transform 0.4s ease-out"
          : "none",
        transitionDelay: animationsEnabled ? `${delay}ms` : "0ms",
        width: "100%",
        "&:hover": {
          transform:
            animationsEnabled && isVisible ? "scale(1.01)" : undefined,
          zIndex: 5,
        },
      }}
    >
      {children}
    </Box>
  );
};

export function getSubSectionStyle() {
  const theme = useTheme();
  const isDarkMode = theme.palette.mode === "dark";
  const animationsEnabled =
    localStorage.getItem("ui-animations") !== "false";

  const sectionShadow = isDarkMode
    ? `0 20px 60px ${theme.palette.primary.main}44`
    : "0 20px 40px rgba(0,0,0,0.1)";
  return {
    flex: 1,
    transition: animationsEnabled
      ? "all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1)"
      : "none",
    position: "relative",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    bgcolor: theme.palette.background.paper,
    "&:hover": {
      bgcolor: theme.palette.background.paper,
      zIndex: 10,
      transform: animationsEnabled ? "scale(1.03)" : "none",
      boxShadow: animationsEnabled ? sectionShadow : "none",
    },
  }
}