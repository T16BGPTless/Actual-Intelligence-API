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
  IconButton,
  Tooltip,
  Typography,
  useTheme,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import TokenIcon from "@mui/icons-material/Token";
import ForumIcon from "@mui/icons-material/Forum";
import DoNotDisturbOnIcon from "@mui/icons-material/DoNotDisturbOn";

import catBg from "../assets/cat2.png";

const STATUS_COLORS = {
  open:    { bg: "#e8f5e9", text: "#2e7d32", dark_bg: "#1b5e2033", dark_text: "#66bb6a" },
  closed:  { bg: "#fafafa", text: "#9e9e9e", dark_bg: "#ffffff11", dark_text: "#757575" },
  pending: { bg: "#fff8e1", text: "#f57f17", dark_bg: "#f57f1722", dark_text: "#ffca28" },
};

function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  const diffMs = Date.now() - d;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  if (diffMins < 1) return "just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return d.toLocaleDateString("en-AU", { day: "numeric", month: "short" });
}

const STATUS_FILTERS = ["all", "open", "pending", "closed"];

export default function ChatList() {
  const navigate = useNavigate();
  const theme = useTheme();

  const [chats, setChats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("all");
  const [closingId, setClosingId] = useState(null);
  const [confirmId, setConfirmId] = useState(null);

  const isDark = theme.palette.mode === "dark";
  const animationsEnabled = localStorage.getItem("ui-animations") !== "false";
  const borderColor = theme.palette.text.primary;
  const mutedColor = theme.palette.text.secondary;
  const primary = theme.palette.primary.main;

  const fetchChats = async () => {
    setLoading(true);
    const token = localStorage.getItem("token");
    try {
      const res = await fetch("/v1/requester/chats", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) { setError("Failed to load chats."); return; }
      setChats(Array.isArray(data) ? data : []);
    } catch {
      setError("Network error.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchChats(); }, []);

  const handleCloseChat = async (chatID) => {
    setClosingId(chatID);
    const token = localStorage.getItem("token");
    try {
      await fetch(`/v1/requester/chats/${chatID}/close`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      setChats((prev) =>
        prev.map((c) => c.chatID === chatID ? { ...c, status: "closed" } : c)
      );
    } catch {
      // silently fail — chat will refresh next time
    } finally {
      setClosingId(null);
      setConfirmId(null);
    }
  };

  const filtered = filter === "all" ? chats : chats.filter((c) => c.status === filter);

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
          right: { xs: -60, md: -30 },
          bottom: "5%",
          width: { xs: 180, md: 260 },
          height: "auto",
          opacity: isDark ? 0.06 : 0.1,
          filter: isDark ? "invert(1)" : "none",
          WebkitMaskImage: "linear-gradient(to left, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0) 85%)",
          pointerEvents: "none",
          userSelect: "none",
          zIndex: 0,
        }}
      />

      <Box sx={{ maxWidth: 720, mx: "auto", px: { xs: 2, md: 0 }, position: "relative", zIndex: 1 }}>

        {/* Header */}
        <Box sx={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", mb: 4, flexWrap: "wrap", gap: 2 }}>
          <Box>
            <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: -1 }}>
              <Divider sx={{ width: 30, borderBottomWidth: 3, borderColor: borderColor }} />
              <Typography variant="overline" sx={{ fontWeight: 900, letterSpacing: 4, fontSize: "0.65rem" }}>
                Requester
              </Typography>
            </Box>
            <Typography variant="h3" sx={{ fontWeight: 900, letterSpacing: "-2px" }}>
              MY CHATS
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.5, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", fontSize: "0.7rem" }}>
              {chats.length} chat{chats.length !== 1 ? "s" : ""} total
            </Typography>
          </Box>

          <Button
            onClick={() => navigate("/chat/new")}
            startIcon={<AddIcon />}
            sx={{
              borderRadius: "99px", px: 3, py: 1, fontWeight: 700, fontSize: "0.85rem",
              textTransform: "none", bgcolor: theme.palette.text.primary,
              color: theme.palette.background.default,
              transition: animationsEnabled ? "all 0.2s ease" : "none",
              "&:hover": {
                transform: animationsEnabled ? "translateY(-2px)" : "none",
                bgcolor: theme.palette.text.secondary,
              },
            }}
          >
            New Chat
          </Button>
        </Box>

        {/* Filter chips */}
        <Box sx={{ display: "flex", gap: 1, mb: 3, flexWrap: "wrap" }}>
          {STATUS_FILTERS.map((f) => {
            const selected = filter === f;
            return (
              <Chip
                key={f}
                label={f.charAt(0).toUpperCase() + f.slice(1)}
                onClick={() => setFilter(f)}
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

        {/* Error */}
        {!loading && error && (
          <Typography sx={{ color: theme.palette.error.main, fontWeight: 600, py: 4, textAlign: "center" }}>
            {error}
          </Typography>
        )}

        {/* Empty state */}
        {!loading && !error && filtered.length === 0 && (
          <Box sx={{ textAlign: "center", py: 10 }}>
            <ForumIcon sx={{ fontSize: 48, opacity: 0.15, mb: 2 }} />
            <Typography sx={{ fontWeight: 700, opacity: 0.4, textTransform: "uppercase", letterSpacing: 2, fontSize: "0.85rem" }}>
              {filter === "all" ? "No chats yet" : `No ${filter} chats`}
            </Typography>
            {filter === "all" && (
              <Button
                onClick={() => navigate("/chat/new")}
                sx={{
                  mt: 3, borderRadius: "99px", px: 3, py: 0.75, fontWeight: 600,
                  fontSize: "0.8rem", textTransform: "none",
                  bgcolor: theme.palette.text.primary, color: theme.palette.background.default,
                  "&:hover": { bgcolor: theme.palette.text.secondary },
                }}
              >
                Create your first chat
              </Button>
            )}
          </Box>
        )}

        {/* Chat list */}
        {!loading && !error && filtered.length > 0 && (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
            {filtered.map((chat, i) => {
              const statusStyle = STATUS_COLORS[chat.status] || STATUS_COLORS.pending;
              const isClosed = chat.status === "closed";

              return (
                <Box
                  key={chat.chatID}
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    gap: 2,
                    p: 2,
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
                  onClick={() => navigate(`/chat/${chat.chatID}`)}
                >
                  {/* Status dot */}
                  <Box
                    sx={{
                      width: 8, height: 8, borderRadius: "50%", flexShrink: 0,
                      bgcolor: isDark ? statusStyle.dark_text : statusStyle.text,
                    }}
                  />

                  {/* Main content */}
                  <Box sx={{ flex: 1, minWidth: 0 }}>
                    <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 0.25 }}>
                      <Typography sx={{ fontWeight: 700, fontSize: "0.95rem", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                        {chat.title || "Untitled Chat"}
                      </Typography>
                      {chat.category && (
                        <Typography sx={{ fontSize: "0.65rem", fontWeight: 600, color: mutedColor, flexShrink: 0, opacity: 0.7 }}>
                          · {chat.category}
                        </Typography>
                      )}
                    </Box>
                    <Typography sx={{ fontSize: "0.78rem", color: mutedColor, opacity: 0.8 }}>
                      {formatDate(chat.createdAt)}
                    </Typography>
                  </Box>

                  {/* Tokens */}
                  <Box sx={{ display: "flex", alignItems: "center", gap: 0.5, flexShrink: 0 }}>
                    <TokenIcon sx={{ fontSize: 13, color: mutedColor, opacity: 0.7 }} />
                    <Typography sx={{ fontSize: "0.8rem", fontWeight: 700, color: mutedColor }}>
                      {chat.tokens ?? 0}
                    </Typography>
                  </Box>

                  {/* Status badge */}
                  <Box
                    sx={{
                      px: 1.25, py: 0.25, borderRadius: "99px", flexShrink: 0,
                      bgcolor: isDark ? statusStyle.dark_bg : statusStyle.bg,
                      color: isDark ? statusStyle.dark_text : statusStyle.text,
                      fontSize: "0.68rem", fontWeight: 700,
                      textTransform: "uppercase", letterSpacing: 0.5,
                    }}
                  >
                    {chat.status}
                  </Box>

                  {/* Close button */}
                  {!isClosed && (
                    <Tooltip title="Close chat" placement="top">
                      <IconButton
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          setConfirmId(chat.chatID);
                        }}
                        sx={{
                          flexShrink: 0,
                          color: mutedColor,
                          opacity: 0.4,
                          transition: animationsEnabled ? "all 0.15s ease" : "none",
                          "&:hover": {
                            opacity: 1,
                            color: theme.palette.error.main,
                            bgcolor: `${theme.palette.error.main}15`,
                          },
                        }}
                      >
                        {closingId === chat.chatID
                          ? <CircularProgress size={16} color="inherit" />
                          : <DoNotDisturbOnIcon sx={{ fontSize: 18 }} />
                        }
                      </IconButton>
                    </Tooltip>
                  )}
                </Box>
              );
            })}
          </Box>
        )}
      </Box>

      {/* Confirm close dialog */}
      <Dialog
        open={Boolean(confirmId)}
        onClose={() => setConfirmId(null)}
        PaperProps={{
          sx: {
            borderRadius: "12px",
            border: `0.5px solid ${borderColor}33`,
            bgcolor: theme.palette.background.paper,
            p: 1,
          },
        }}
      >
        <DialogTitle sx={{ fontWeight: 900, letterSpacing: "-0.5px" }}>Close this chat?</DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ color: mutedColor, fontSize: "0.9rem" }}>
            This will permanently close the chat. The responder will no longer be able to respond.
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2, gap: 1 }}>
          <Button
            onClick={() => setConfirmId(null)}
            sx={{
              borderRadius: "99px", px: 3, fontWeight: 600, fontSize: "0.8rem",
              textTransform: "none", color: mutedColor, border: `0.5px solid ${borderColor}33`,
              "&:hover": { bgcolor: `${borderColor}08` },
            }}
          >
            Cancel
          </Button>
          <Button
            onClick={() => handleCloseChat(confirmId)}
            sx={{
              borderRadius: "99px", px: 3, fontWeight: 600, fontSize: "0.8rem",
              textTransform: "none", bgcolor: theme.palette.error.main,
              color: "#fff",
              "&:hover": { bgcolor: theme.palette.error.dark },
            }}
          >
            Close Chat
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
