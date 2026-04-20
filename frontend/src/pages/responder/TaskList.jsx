import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Divider,
  TextField,
  Typography,
  useTheme,
} from "@mui/material";
import TokenIcon from "@mui/icons-material/Token";
import InboxIcon from "@mui/icons-material/Inbox";

import catBg from "../../assets/cat5.png";

const CATEGORIES = ["General", "Mathematics", "Science", "Programming", "Writing", "Design", "Research", "Other"];

const STATUS_COLORS = {
  claimed:  { bg: "#e3f2fd", text: "#1565c0", dark_bg: "#1565c022", dark_text: "#64b5f6" },
  closing:  { bg: "#fff8e1", text: "#f57f17", dark_bg: "#f57f1722", dark_text: "#ffca28" },
  closed:   { bg: "#fafafa", text: "#9e9e9e", dark_bg: "#ffffff11", dark_text: "#757575" },
  open:     { bg: "#e8f5e9", text: "#2e7d32", dark_bg: "#1b5e2033", dark_text: "#66bb6a" },
};

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

  const [tab, setTab] = useState("available"); // "available" | "mine"
  const [available, setAvailable] = useState([]);
  const [mine, setMine] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeCategory, setActiveCategory] = useState("All");

  const [claimTarget, setClaimTarget] = useState(null);
  const [claimTitle, setClaimTitle] = useState("");
  const [claiming, setClaiming] = useState(false);
  const [claimError, setClaimError] = useState("");
  const [loadingPreview, setLoadingPreview] = useState(false);

  const isDark = theme.palette.mode === "dark";
  const animationsEnabled = localStorage.getItem("ui-animations") !== "false";
  const borderColor = theme.palette.text.primary;
  const mutedColor = theme.palette.text.secondary;
  const primary = theme.palette.primary.main;

  const authToken = () => localStorage.getItem("token");

  const fetchAll = async () => {
    setLoading(true);
    const headers = { Authorization: `Bearer ${authToken()}` };
    try {
      const [availRes, mineRes] = await Promise.all([
        fetch("/v1/responder/chats/unclaimed", { headers }),
        fetch("/v1/responder/chats", { headers }),
      ]);
      const [availData, mineData] = await Promise.all([availRes.json(), mineRes.json()]);
      setAvailable(Array.isArray(availData) ? availData : []);
      setMine(Array.isArray(mineData) ? mineData : []);
    } catch {
      setAvailable([]);
      setMine([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAll(); }, []);

  const openClaimDialog = async (task) => {
    setClaimTarget(task);
    setClaimTitle("");
    setClaimError("");
    setLoadingPreview(true);
    try {
      const res = await fetch(`/v1/responder/chats/${task.chatID}`, {
        headers: { Authorization: `Bearer ${authToken()}` },
      });
      const data = await res.json();
      if (res.ok) {
        setClaimTarget({
          ...task,
          requestText: data.originalRequest || data.requests?.[0]?.requestText || "",
        });
      }
    } catch { }
    finally { setLoadingPreview(false); }
  };

  const handleClaim = async () => {
    if (!claimTitle.trim()) { setClaimError("Please enter a title."); return; }
    setClaiming(true);
    setClaimError("");
    try {
      const res = await fetch(`/v1/responder/chats/${claimTarget.chatID}/claim`, {
        method: "POST",
        headers: { Authorization: `Bearer ${authToken()}`, "Content-Type": "application/json" },
        body: JSON.stringify({ title: claimTitle.trim() }),
      });
      if (res.ok) {
        navigate(`/tasks/${claimTarget.chatID}`);
      } else {
        const data = await res.json();
        setClaimError(data?.message || "Failed to claim chat.");
      }
    } catch {
      setClaimError("Network error. Please try again.");
    } finally {
      setClaiming(false);
    }
  };

  const filteredAvailable = activeCategory === "All"
    ? available
    : available.filter((t) => t.category === activeCategory);

  const tabs = [
    { key: "available", label: "Available", count: available.length },
    { key: "mine", label: "My Tasks", count: mine.length },
  ];

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
      <Box component="img" src={catBg} alt="" aria-hidden="true"
        sx={{ position: "absolute", right: { xs: -60, md: -20 }, bottom: "5%", width: { xs: 160, md: 230 }, height: "auto", opacity: isDark ? 0.06 : 0.1, filter: isDark ? "invert(1)" : "none", WebkitMaskImage: "linear-gradient(to left, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0) 85%)", pointerEvents: "none", userSelect: "none", zIndex: 0 }}
      />

      <Box sx={{ maxWidth: 680, mx: "auto", px: { xs: 2, md: 0 }, position: "relative", zIndex: 1 }}>

        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: -1 }}>
            <Divider sx={{ width: 30, borderBottomWidth: 3, borderColor: borderColor }} />
            <Typography variant="overline" sx={{ fontWeight: 900, letterSpacing: 4, fontSize: "0.65rem" }}>Responder</Typography>
          </Box>
          <Typography variant="h3" sx={{ fontWeight: 900, letterSpacing: "-2px" }}>TASK LIST</Typography>
        </Box>

        {/* Tabs */}
        <Box sx={{ display: "flex", gap: 1, mb: 3 }}>
          {tabs.map((t) => {
            const selected = tab === t.key;
            return (
              <Box
                key={t.key}
                onClick={() => setTab(t.key)}
                sx={{
                  px: 2.5, py: 0.75, borderRadius: "99px", cursor: "pointer", display: "flex", alignItems: "center", gap: 1,
                  border: `1.5px solid ${selected ? borderColor : `${borderColor}28`}`,
                  bgcolor: selected ? theme.palette.text.primary : "transparent",
                  transition: animationsEnabled ? "all 0.15s ease" : "none",
                  "&:hover": { border: `1.5px solid ${borderColor}77` },
                }}
              >
                <Typography sx={{ fontWeight: 700, fontSize: "0.82rem", color: selected ? theme.palette.background.default : mutedColor }}>
                  {t.label}
                </Typography>
                <Box sx={{ px: 0.75, py: 0.1, borderRadius: "99px", bgcolor: selected ? `${theme.palette.background.default}33` : `${borderColor}15` }}>
                  <Typography sx={{ fontSize: "0.68rem", fontWeight: 700, color: selected ? theme.palette.background.default : mutedColor }}>
                    {t.count}
                  </Typography>
                </Box>
              </Box>
            );
          })}
        </Box>

        {/* Category filters — only on available tab */}
        {tab === "available" && (
          <Box sx={{ display: "flex", gap: 1, mb: 3, flexWrap: "wrap" }}>
            {["All", ...CATEGORIES].map((cat) => {
              const selected = activeCategory === cat;
              return (
                <Chip key={cat} label={cat} onClick={() => setActiveCategory(cat)}
                  sx={{ borderRadius: "99px", fontWeight: 600, fontSize: "0.75rem", height: 28, transition: animationsEnabled ? "all 0.15s ease" : "none", border: `0.5px solid ${selected ? borderColor : `${borderColor}33`}`, bgcolor: selected ? theme.palette.text.primary : "transparent", color: selected ? theme.palette.background.default : mutedColor, "&:hover": { bgcolor: selected ? theme.palette.text.primary : `${borderColor}11`, color: selected ? theme.palette.background.default : theme.palette.text.primary } }}
                />
              );
            })}
          </Box>
        )}

        {/* Loading */}
        {loading && (
          <Box sx={{ display: "flex", justifyContent: "center", py: 10 }}>
            <CircularProgress size={32} sx={{ color: borderColor }} />
          </Box>
        )}

        {/* Available tab */}
        {!loading && tab === "available" && (
          <>
            {filteredAvailable.length === 0 ? (
              <Box sx={{ textAlign: "center", py: 10 }}>
                <InboxIcon sx={{ fontSize: 48, opacity: 0.15, mb: 2 }} />
                <Typography sx={{ fontWeight: 700, opacity: 0.4, textTransform: "uppercase", letterSpacing: 2, fontSize: "0.85rem" }}>No tasks available</Typography>
              </Box>
            ) : (
              <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                {filteredAvailable.map((task, i) => (
                  <Box key={task.chatID}
                    sx={{ display: "flex", alignItems: "center", gap: 2, px: 2, py: 1.5, borderRadius: "12px", border: `0.5px solid ${borderColor}22`, bgcolor: isDark ? `${borderColor}06` : theme.palette.background.paper, transition: animationsEnabled ? "all 0.18s ease" : "none", opacity: 0, animation: animationsEnabled ? "fadeSlideIn 0.3s ease forwards" : "none", animationDelay: animationsEnabled ? `${i * 40}ms` : "0ms", "&:hover": { border: `0.5px solid ${borderColor}55`, transform: animationsEnabled ? "translateX(4px)" : "none", bgcolor: isDark ? `${borderColor}0e` : `${primary}08` } }}
                  >
                    <Box sx={{ flex: 1, minWidth: 0 }}>
                      <Box sx={{ display: "flex", alignItems: "baseline", gap: 1 }}>
                      <Typography sx={{ fontWeight: 700, fontSize: "0.82rem", flexShrink: 0 }}>{task.category || "General"}</Typography>                        <Typography sx={{ fontSize: "0.72rem", color: mutedColor, opacity: 0.7 }}>{timeAgo(task.createdAt)}</Typography>
                      </Box>
                      <Typography sx={{ fontSize: "0.82rem", color: mutedColor, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                        {task.originalRequest || task.title || "No description"}
                      </Typography>
                    </Box>
                    <Box sx={{ display: "flex", alignItems: "center", gap: 0.5, flexShrink: 0 }}>
                      <TokenIcon sx={{ fontSize: 13, color: mutedColor, opacity: 0.7 }} />
                      <Typography sx={{ fontSize: "0.82rem", fontWeight: 700, color: mutedColor }}>{task.tokens ?? 0}</Typography>
                    </Box>
                    <Button onClick={() => openClaimDialog(task)}
                      sx={{ borderRadius: "99px", px: 2, py: 0.4, fontWeight: 700, fontSize: "0.72rem", textTransform: "none", flexShrink: 0, bgcolor: theme.palette.text.primary, color: theme.palette.background.default, minWidth: 60, transition: animationsEnabled ? "all 0.15s ease" : "none", "&:hover": { bgcolor: theme.palette.text.secondary } }}>
                      Claim
                    </Button>
                  </Box>
                ))}
              </Box>
            )}
          </>
        )}

        {/* My Tasks tab */}
        {!loading && tab === "mine" && (
          <>
            {mine.length === 0 ? (
              <Box sx={{ textAlign: "center", py: 10 }}>
                <InboxIcon sx={{ fontSize: 48, opacity: 0.15, mb: 2 }} />
                <Typography sx={{ fontWeight: 700, opacity: 0.4, textTransform: "uppercase", letterSpacing: 2, fontSize: "0.85rem" }}>No claimed tasks yet</Typography>
              </Box>
            ) : (
              <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                {mine.map((task, i) => {
                  const statusStyle = STATUS_COLORS[task.status] || STATUS_COLORS.claimed;
                  return (
                    <Box key={task.chatID} onClick={() => navigate(`/tasks/${task.chatID}`)}
                      sx={{ display: "flex", alignItems: "center", gap: 2, px: 2, py: 1.5, borderRadius: "12px", border: `0.5px solid ${borderColor}22`, bgcolor: isDark ? `${borderColor}06` : theme.palette.background.paper, cursor: "pointer", transition: animationsEnabled ? "all 0.18s ease" : "none", opacity: 0, animation: animationsEnabled ? "fadeSlideIn 0.3s ease forwards" : "none", animationDelay: animationsEnabled ? `${i * 40}ms` : "0ms", "&:hover": { border: `0.5px solid ${borderColor}55`, transform: animationsEnabled ? "translateX(4px)" : "none", bgcolor: isDark ? `${borderColor}0e` : `${primary}08` } }}
                    >
                      {/* Status dot */}
                      <Box sx={{ width: 8, height: 8, borderRadius: "50%", flexShrink: 0, bgcolor: isDark ? statusStyle.dark_text : statusStyle.text }} />

                      <Box sx={{ flex: 1, minWidth: 0 }}>
                        <Box sx={{ display: "flex", alignItems: "baseline", gap: 1 }}>
                          <Typography sx={{ fontWeight: 700, fontSize: "0.82rem", flexShrink: 0 }}>{task.title || "Untitled"}</Typography>
                          <Typography sx={{ fontSize: "0.72rem", color: mutedColor, opacity: 0.7 }}>{timeAgo(task.createdAt)}</Typography>
                        </Box>
                        <Typography sx={{ fontSize: "0.78rem", color: mutedColor, opacity: 0.8 }}>
                          Requester: {task.requesterUsername || "Unknown"}
                        </Typography>
                      </Box>

                      <Box sx={{ display: "flex", alignItems: "center", gap: 0.5, flexShrink: 0 }}>
                        <TokenIcon sx={{ fontSize: 13, color: mutedColor, opacity: 0.7 }} />
                        <Typography sx={{ fontSize: "0.82rem", fontWeight: 700, color: mutedColor }}>{task.tokens ?? 0}</Typography>
                      </Box>

                      <Box sx={{ px: 1.25, py: 0.25, borderRadius: "99px", flexShrink: 0, bgcolor: isDark ? statusStyle.dark_bg : statusStyle.bg, color: isDark ? statusStyle.dark_text : statusStyle.text, fontSize: "0.68rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: 0.5 }}>
                        {task.status}
                      </Box>
                    </Box>
                  );
                })}
              </Box>
            )}
          </>
        )}
      </Box>

      {/* Claim Dialog */}
      <Dialog open={Boolean(claimTarget)} onClose={() => { setClaimTarget(null); setClaimError(""); }}
        PaperProps={{ sx: { borderRadius: "12px", border: `0.5px solid ${borderColor}33`, bgcolor: theme.palette.background.paper, p: 1, minWidth: 360 } }}>
        <DialogTitle sx={{ fontWeight: 900, letterSpacing: "-0.5px" }}>Claim this chat</DialogTitle>
        <DialogContent sx={{ display: "flex", flexDirection: "column", gap: 2, pt: "8px !important" }}>
          <DialogContentText sx={{ color: mutedColor, fontSize: "0.85rem" }}>
            Give this chat a title so the requester knows you've understood their request.
          </DialogContentText>
          {loadingPreview && <Box sx={{ display: "flex", justifyContent: "center", py: 1 }}><CircularProgress size={16} sx={{ color: mutedColor }} /></Box>}
          {!loadingPreview && claimTarget?.requestText && (
            <Box sx={{ px: 1.5, py: 1, borderRadius: "8px", bgcolor: isDark ? `${borderColor}08` : `${borderColor}06`, border: `0.5px solid ${borderColor}22` }}>
              <Typography sx={{ fontSize: "0.75rem", color: mutedColor, fontWeight: 600, letterSpacing: 1, textTransform: "uppercase", mb: 0.5 }}>Their request</Typography>
              <Typography sx={{ fontSize: "0.85rem", color: theme.palette.text.primary, lineHeight: 1.5 }}>{claimTarget.requestText}</Typography>
            </Box>
          )}
          <TextField label="Title" value={claimTitle} onChange={(e) => { setClaimTitle(e.target.value); setClaimError(""); }} onKeyDown={(e) => { if (e.key === "Enter") handleClaim(); }} fullWidth autoFocus error={Boolean(claimError)} helperText={claimError}
            sx={{ "& .MuiOutlinedInput-root": { borderRadius: "8px", fontSize: "0.9rem", "& fieldset": { border: `0.5px solid ${borderColor}33` }, "&.Mui-focused fieldset": { border: `1px solid ${borderColor}88` } }, "& .MuiInputLabel-root.Mui-focused": { color: borderColor } }}
          />
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2, gap: 1 }}>
          <Button onClick={() => { setClaimTarget(null); setClaimError(""); }} sx={{ borderRadius: "99px", px: 3, fontWeight: 600, fontSize: "0.8rem", textTransform: "none", color: mutedColor, border: `0.5px solid ${borderColor}33`, "&:hover": { bgcolor: `${borderColor}08` } }}>Cancel</Button>
          <Button onClick={handleClaim} disabled={claiming || !claimTitle.trim()}
            sx={{ borderRadius: "99px", px: 3, fontWeight: 600, fontSize: "0.8rem", textTransform: "none", bgcolor: theme.palette.text.primary, color: theme.palette.background.default, "&:hover": { bgcolor: theme.palette.text.secondary }, "&.Mui-disabled": { opacity: 0.35, color: theme.palette.background.default, bgcolor: theme.palette.text.primary } }}>
            {claiming ? <CircularProgress size={14} color="inherit" /> : "Claim Chat"}
          </Button>
        </DialogActions>
      </Dialog>

      <style>{`
        @keyframes fadeSlideIn {
          from { opacity: 0; transform: translateY(8px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </Box>
  );
}
