import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Button,
  Chip,
  CircularProgress,
  Divider,
  Typography,
  useTheme,
} from "@mui/material";
import TokenIcon from "@mui/icons-material/Token";
import InboxIcon from "@mui/icons-material/Inbox";

import catBg from "../../assets/cat5.png";

const CATEGORIES = ["General", "Mathematics", "Science", "Programming", "Writing", "Design", "Research", "Other"];

const MOCK_TASKS = [
  { chatID: "t1", title: "What should I have for lunch today?", requesterUsername: "George", category: "General", tokens: 1, createdAt: new Date(Date.now() - 60000).toISOString() }
];

function timeAgo(iso) {
  if (!iso) return "";
  const mins = Math.floor((Date.now() - new Date(iso)) / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h`;
  return `${Math.floor(hrs / 24)}d`;
}

export default function TaskList() {
  const navigate = useNavigate();
  const theme = useTheme();

  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeCategory, setActiveCategory] = useState("All");
  const [claimingId, setClaimingId] = useState(null);

  const isDark = theme.palette.mode === "dark";
  const animationsEnabled = localStorage.getItem("ui-animations") !== "false";
  const borderColor = theme.palette.text.primary;
  const mutedColor = theme.palette.text.secondary;
  const primary = theme.palette.primary.main;

  const fetchTasks = async () => {
    const token = localStorage.getItem("token");
    if (token === "debug_token") {
      setTasks(MOCK_TASKS);
      setLoading(false);
      return;
    }
    try {
      const params = activeCategory !== "All" ? `?categories=${activeCategory}` : "";
      const res = await fetch(`/v1/responder/chats/unclaimed${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      setTasks(Array.isArray(data) ? data : []);
    } catch {
      setTasks(MOCK_TASKS);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchTasks(); }, [activeCategory]);

  const handleClaim = async (chatID) => {
    setClaimingId(chatID);
    const token = localStorage.getItem("token");
    if (token === "debug_token") {
      navigate(`/tasks/${chatID}`);
      return;
    }
    try {
      const res = await fetch(`/v1/responder/chats/${chatID}/claim`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) navigate(`/tasks/${chatID}`);
    } finally {
      setClaimingId(null);
    }
  };

  const filtered = activeCategory === "All"
    ? tasks
    : tasks.filter((t) => t.category === activeCategory);

  return (
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
      {/* Background cat */}
      <Box
        component="img"
        src={catBg}
        alt=""
        aria-hidden="true"
        sx={{
          position: "absolute",
          right: { xs: -60, md: -20 },
          bottom: "5%",
          width: { xs: 160, md: 230 },
          height: "auto",
          opacity: isDark ? 0.06 : 0.1,
          filter: isDark ? "invert(1)" : "none",
          WebkitMaskImage: "linear-gradient(to left, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0) 85%)",
          pointerEvents: "none",
          userSelect: "none",
          zIndex: 0,
        }}
      />

      <Box sx={{ maxWidth: 680, mx: "auto", px: { xs: 2, md: 0 }, position: "relative", zIndex: 1 }}>

        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: -1 }}>
            <Divider sx={{ width: 30, borderBottomWidth: 3, borderColor: borderColor }} />
            <Typography variant="overline" sx={{ fontWeight: 900, letterSpacing: 4, fontSize: "0.65rem" }}>
              Responder
            </Typography>
          </Box>
          <Typography variant="h3" sx={{ fontWeight: 900, letterSpacing: "-2px" }}>
            TASK LIST
          </Typography>
          <Typography variant="body2" sx={{ opacity: 0.5, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", fontSize: "0.7rem" }}>
            {filtered.length} task{filtered.length !== 1 ? "s" : ""} available
          </Typography>
        </Box>

        {/* Categoriieessss  */}
        <Box sx={{ display: "flex", gap: 1, mb: 3, flexWrap: "wrap" }}>
          {["All", ...CATEGORIES].map((cat) => {
            const selected = activeCategory === cat;
            return (
              <Chip
                key={cat}
                label={cat}
                onClick={() => setActiveCategory(cat)}
                sx={{
                  borderRadius: "99px", fontWeight: 600, fontSize: "0.75rem", height: 28,
                  transition: animationsEnabled ? "all 0.15s ease" : "none",
                  border: `0.5px solid ${selected ? borderColor : `${borderColor}33`}`,
                  bgcolor: selected ? theme.palette.text.primary : "transparent",
                  color: selected ? theme.palette.background.default : mutedColor,
                  "&:hover": {
                    bgcolor: selected ? theme.palette.text.primary : `${borderColor}11`,
                    color: selected ? theme.palette.background.default : theme.palette.text.primary,
                  },
                }}
              />
            );
          })}
        </Box>

        {/* Loading */}
        {loading && (
          <Box sx={{ display: "flex", justifyContent: "center", py: 10 }}>
            <CircularProgress size={32} sx={{ color: borderColor }} />
          </Box>
        )}

        {/* Empty */}
        {!loading && filtered.length === 0 && (
          <Box sx={{ textAlign: "center", py: 10 }}>
            <InboxIcon sx={{ fontSize: 48, opacity: 0.15, mb: 2 }} />
            <Typography sx={{ fontWeight: 700, opacity: 0.4, textTransform: "uppercase", letterSpacing: 2, fontSize: "0.85rem" }}>
              No tasks available
            </Typography>
          </Box>
        )}

        {/* Task rows */}
        {!loading && filtered.length > 0 && (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
            {filtered.map((task, i) => (
              <Box
                key={task.chatID}
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 2,
                  px: 2,
                  py: 1.5,
                  borderRadius: "12px",
                  border: `0.5px solid ${borderColor}22`,
                  bgcolor: isDark ? `${borderColor}06` : theme.palette.background.paper,
                  cursor: "pointer",
                  transition: animationsEnabled ? "all 0.18s ease" : "none",
                  opacity: 0,
                  animation: animationsEnabled ? "fadeSlideIn 0.3s ease forwards" : "none",
                  animationDelay: animationsEnabled ? `${i * 40}ms` : "0ms",
                  "&:hover": {
                    border: `0.5px solid ${borderColor}55`,
                    transform: animationsEnabled ? "translateX(4px)" : "none",
                    bgcolor: isDark ? `${borderColor}0e` : `${primary}08`,
                  },
                }}
                onClick={() => handleClaim(task.chatID)}
              >
                {/* Main info */}
                <Box sx={{ flex: 1, minWidth: 0 }}>
                  <Box sx={{ display: "flex", alignItems: "baseline", gap: 1 }}>
                    <Typography sx={{ fontWeight: 700, fontSize: "0.82rem", flexShrink: 0 }}>
                      {task.requesterUsername || "Anonymous"}
                    </Typography>
                    <Typography sx={{ fontSize: "0.72rem", color: mutedColor, opacity: 0.7 }}>
                      {timeAgo(task.createdAt)}
                    </Typography>
                  </Box>
                  <Typography
                    sx={{
                      fontSize: "0.82rem", color: mutedColor,
                      whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
                    }}
                  >
                    {task.title || "Untitled"}
                  </Typography>
                </Box>

                {/* Token count */}
                <Box sx={{ display: "flex", alignItems: "center", gap: 0.5, flexShrink: 0 }}>
                  <TokenIcon sx={{ fontSize: 13, color: mutedColor, opacity: 0.7 }} />
                  <Typography sx={{ fontSize: "0.82rem", fontWeight: 700, color: mutedColor }}>
                    {task.tokens ?? 0}
                  </Typography>
                </Box>

                {/* Claim button */}
                <Button
                  onClick={(e) => { e.stopPropagation(); handleClaim(task.chatID); }}
                  sx={{
                    borderRadius: "99px", px: 2, py: 0.4, fontWeight: 700, fontSize: "0.72rem",
                    textTransform: "none", flexShrink: 0,
                    bgcolor: theme.palette.text.primary, color: theme.palette.background.default,
                    minWidth: 60,
                    transition: animationsEnabled ? "all 0.15s ease" : "none",
                    "&:hover": { bgcolor: theme.palette.text.secondary },
                  }}
                >
                  {claimingId === task.chatID
                    ? <CircularProgress size={12} color="inherit" />
                    : "Claim"
                  }
                </Button>
              </Box>
            ))}
          </Box>
        )}
      </Box>

      <style>{`
        @keyframes fadeSlideIn {
          from { opacity: 0; transform: translateY(8px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </Box>
  );
}
