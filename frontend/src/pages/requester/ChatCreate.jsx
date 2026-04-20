import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Button,
  Chip,
  CircularProgress,
  Alert,
  TextField,
  Typography,
  useTheme,
} from "@mui/material";
import SendIcon from "@mui/icons-material/Send";

import catLeft from "../../assets/cat3.png";
import catRight from "../../assets/cat7.png";

const CATEGORIES = [
  "General",
  "Mathematics",
  "Science",
  "Programming",
  "Writing",
  "Design",
  "Research",
  "Other",
];

const TOKEN_PRESETS = [1, 5, 10, 25, 50, 100];

export default function ChatCreate() {
  const navigate = useNavigate();
  const theme = useTheme();

  const [category, setCategory] = useState("General");
  const [requestText, setRequestText] = useState("");
  const [tokensToSpend, setTokensToSpend] = useState(10);
  const [customToken, setCustomToken] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const isDark = theme.palette.mode === "dark";
  const animationsEnabled = localStorage.getItem("ui-animations") !== "false";
  const borderColor = theme.palette.text.primary;
  const mutedColor = theme.palette.text.secondary;
  const primary = theme.palette.primary.main;

  const handleTokenChip = (amount) => {
    setTokensToSpend(amount);
    setCustomToken("");
  };

  const handleCustomToken = (e) => {
    const raw = e.target.value;
    if (raw !== "" && !/^\d+$/.test(raw)) return;
    setCustomToken(raw);
    if (raw === "") return;
    const v = parseInt(raw, 10);
    if (!isNaN(v) && v > 0) setTokensToSpend(v);
  };

  const isPreset = TOKEN_PRESETS.includes(tokensToSpend) && customToken === "";
  const customActive = customToken !== "" && !isPreset;

  const handleSubmit = async () => {
    if (!requestText.trim()) {
      setError("Please enter your request before submitting.");
      return;
    }
    setError("");
    setLoading(true);

    const token = localStorage.getItem("token");

    try {
      const res = await fetch("/v1/requester/chats", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          category: category || undefined,
          requestText: requestText.trim(),
          tokensToSpend,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data?.message || "Failed to create chat.");
        return;
      }

      navigate(`/chat/${data.chatID}`);
    } catch {
      setError("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    /* Full-width gradient strip */
    <Box
      sx={{
        width: "100%",
        minHeight: "100%",
        background: `linear-gradient(135deg, ${primary}14 0%, transparent 45%, ${primary}0a 100%)`,
        position: "relative",
        overflow: "hidden",
        py: { xs: 4, md: 6 },
      }}
    >
      {/* Cat mewo*/}
      <Box
        component="img"
        src={catLeft}
        alt=""
        aria-hidden="true"
        sx={{
          position: "absolute",
          left: { xs: -50, md: -20 },
          bottom: "10%",
          width: { xs: 160, md: 220 },
          height: "auto",
          opacity: isDark ? 0.12 : 0.22,
          filter: isDark ? "invert(1)" : "none",
          WebkitMaskImage: "linear-gradient(to right, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0) 85%)",
          pointerEvents: "none",
          userSelect: "none",
          zIndex: 0,
        }}
      />

      {/* Cat meow hehe */}
      <Box
        component="img"
        src={catRight}
        alt=""
        aria-hidden="true"
        sx={{
          position: "absolute",
          right: { xs: -50, md: -20 },
          bottom: "10%",
          width: { xs: 160, md: 220 },
          height: "auto",
          opacity: isDark ? 0.12 : 0.22,
          filter: isDark ? "invert(1)" : "none",
          WebkitMaskImage: "linear-gradient(to left, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0) 85%)",
          pointerEvents: "none",
          userSelect: "none",
          zIndex: 0,
        }}
      />

      {/* Form content */}
      <Box
        sx={{
          maxWidth: 660,
          mx: "auto",
          px: { xs: 2, md: 0 },
          display: "flex",
          flexDirection: "column",
          position: "relative",
          zIndex: 1,
        }}
      >
        {/* Categories */}
        <Box sx={{ mb: 4 }}>
          <Typography variant="overline" sx={{ fontSize: "0.65rem", fontWeight: 700, letterSpacing: 3, color: mutedColor, display: "block", mb: 1.5 }}>
            Category
          </Typography>
          <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
            {CATEGORIES.map((c) => (
              <Chip
                key={c}
                label={c}
                onClick={() => setCategory(c)}
                sx={{
                  borderRadius: "99px",
                  fontWeight: 600,
                  fontSize: "0.75rem",
                  height: 28,
                  transition: animationsEnabled ? "all 0.15s ease" : "none",
                  border: `0.5px solid ${category === c ? borderColor : `${borderColor}33`}`,
                  bgcolor: category === c ? theme.palette.text.primary : "transparent",
                  color: category === c ? theme.palette.background.default : mutedColor,
                  "&:hover": {
                    bgcolor: category === c ? theme.palette.text.primary : `${borderColor}11`,
                    color: category === c ? theme.palette.background.default : theme.palette.text.primary,
                  },
                }}
              />
            ))}
          </Box>
        </Box>

        {/* Request textarea */}
        <Box sx={{ mb: 4 }}>
          <Typography variant="overline" sx={{ fontSize: "0.65rem", fontWeight: 700, letterSpacing: 3, color: mutedColor, display: "block", mb: 1.5 }}>
            Your Request
          </Typography>
          <TextField
            placeholder="What would you like to know?"
            value={requestText}
            onChange={(e) => setRequestText(e.target.value)}
            multiline
            minRows={5}
            maxRows={14}
            fullWidth
            variant="outlined"
            sx={{
              "& .MuiOutlinedInput-root": {
                borderRadius: "12px",
                fontSize: "0.95rem",
                bgcolor: isDark ? `${borderColor}08` : theme.palette.background.paper,
                "& fieldset": { border: `0.5px solid ${borderColor}22` },
                "&:hover fieldset": { border: `0.5px solid ${borderColor}55` },
                "&.Mui-focused fieldset": { border: `1px solid ${borderColor}88` },
              },
            }}
          />
        </Box>

        {/* Token selector */}
        <Box sx={{ mb: 4 }}>
          <Typography variant="overline" sx={{ fontSize: "0.65rem", fontWeight: 700, letterSpacing: 3, color: mutedColor, display: "block", mb: 1.5 }}>
            Token Stake
          </Typography>

          <Box sx={{ display: "flex", alignItems: "center", gap: 1, flexWrap: "wrap" }}>
            {TOKEN_PRESETS.map((t) => {
              const selected = isPreset && tokensToSpend === t;
              return (
                <Box
                  key={t}
                  component="button"
                  onClick={() => handleTokenChip(t)}
                  sx={{
                    height: 32,
                    px: 2,
                    borderRadius: "99px",
                    border: `1.5px solid ${selected ? borderColor : `${borderColor}28`}`,
                    bgcolor: selected ? theme.palette.text.primary : "transparent",
                    color: selected ? theme.palette.background.default : mutedColor,
                    fontWeight: 700,
                    fontSize: "0.8rem",
                    cursor: "pointer",
                    fontFamily: theme.typography.fontFamily,
                    transition: animationsEnabled ? "all 0.15s ease" : "none",
                    "&:hover": {
                      border: `1.5px solid ${borderColor}77`,
                      color: selected ? theme.palette.background.default : theme.palette.text.primary,
                      bgcolor: selected ? theme.palette.text.primary : `${borderColor}0d`,
                    },
                  }}
                >
                  {t}
                </Box>
              );
            })}

            {/* Custom input */}
            <Box
              sx={{
                height: 32,
                px: 1,
                borderRadius: "99px",
                border: `1.5px solid ${customActive ? borderColor : `${borderColor}28`}`,
                bgcolor: customActive ? theme.palette.text.primary : "transparent",
                display: "flex",
                alignItems: "center",
                width: 70,
                transition: animationsEnabled ? "all 0.15s ease" : "none",
                "&:hover": {
                  border: `1.5px solid ${borderColor}77`,
                  bgcolor: customActive ? theme.palette.text.primary : `${borderColor}0d`,
                },
              }}
            >
              <input
                value={customToken}
                onChange={handleCustomToken}
                placeholder="custom"
                inputMode="numeric"
                style={{
                  width: "100%",
                  border: "none",
                  outline: "none",
                  background: "transparent",
                  textAlign: "center",
                  fontWeight: 700,
                  fontSize: "0.75rem",
                  fontFamily: "inherit",
                  color: customActive
                    ? theme.palette.background.default
                    : theme.palette.text.secondary,
                }}
              />
            </Box>
          </Box>

          <Typography variant="caption" sx={{ display: "block", mt: 1.5, color: mutedColor, fontWeight: 600, fontSize: "0.72rem" }}>
            ◈ {tokensToSpend} token{tokensToSpend !== 1 ? "s" : ""} will be staked on this request
          </Typography>
        </Box>

        {/* Error */}
        {error && (
          <Alert
            severity="error"
            sx={{ mb: 3, borderRadius: "8px", border: `0.5px solid ${theme.palette.error.main}`, fontSize: "0.85rem" }}
          >
            {error}
          </Alert>
        )}

        {/* Bottom action bar */}
        <Box sx={{ display: "flex", justifyContent: "flex-end", gap: 1.5, alignItems: "center" }}>
          <Button
            onClick={() => navigate("/chat")}
            sx={{
              borderRadius: "99px", px: 3, py: 0.75, fontWeight: 600, fontSize: "0.8rem",
              color: mutedColor, border: `0.5px solid ${borderColor}33`, textTransform: "none",
              transition: animationsEnabled ? "all 0.15s ease" : "none",
              "&:hover": { bgcolor: `${borderColor}08`, color: theme.palette.text.primary, borderColor: `${borderColor}66` },
            }}
          >
            Cancel
          </Button>

          <Button
            onClick={handleSubmit}
            disabled={loading || !requestText.trim()}
            endIcon={
              loading
                ? <CircularProgress size={14} color="inherit" />
                : <SendIcon sx={{ fontSize: "14px !important" }} />
            }
            sx={{
              borderRadius: "99px", px: 3, py: 0.75, fontWeight: 600, fontSize: "0.8rem",
              textTransform: "none", bgcolor: theme.palette.text.primary,
              color: theme.palette.background.default, border: `0.5px solid transparent`,
              transition: animationsEnabled ? "all 0.2s ease" : "none",
              "&:hover": {
                bgcolor: theme.palette.text.secondary,
                transform: animationsEnabled ? "translateY(-1px)" : "none",
              },
              "&.Mui-disabled": {
                opacity: 0.35,
                color: theme.palette.background.default,
                bgcolor: theme.palette.text.primary,
              },
            }}
          >
            {loading ? "Sending..." : "Send request"}
          </Button>
        </Box>
      </Box>
    </Box>
  );
}
