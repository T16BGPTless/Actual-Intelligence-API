import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Box,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  IconButton,
  TextField,
  Tooltip,
  Typography,
  useTheme,
} from "@mui/material";
import SendIcon from "@mui/icons-material/Send";
import TokenIcon from "@mui/icons-material/Token";
import StarIcon from "@mui/icons-material/Star";
import StarBorderIcon from "@mui/icons-material/StarBorder";
import DoNotDisturbOnIcon from "@mui/icons-material/DoNotDisturbOn";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";

const TOKEN_PRESETS = [1, 5, 10, 25, 50, 100];

const MOCK_CHAT = {
  chatID: "mock-123",
  title: "What should I have for lunch today?",
  category: "General",
  status: "closed",
  requesterUsername: "Debug_Cat",
  responderUsername: "Pomni",
  createdAt: new Date(Date.now() - 3600000).toISOString(),
  messages: [
    { messageID: "m1", senderType: "requester", message: "What should I have for lunch today?", createdAt: new Date(Date.now() - 3500000).toISOString() },
    { messageID: "m2", senderType: "responder", message: "Are you feeling like eating out or making something at home?", createdAt: new Date(Date.now() - 3400000).toISOString() }
  ],
  requests: [
    { requestID: "r1", requestText: "What should I have for lunch today?", status: "fulfilled", tokensSpent: 9, createdAt: new Date(Date.now() - 3500000).toISOString() },
  ],
};

function formatTime(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleTimeString("en-AU", { hour: "2-digit", minute: "2-digit" });
}

function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  const diffDays = Math.floor((Date.now() - d) / 86400000);
  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Yesterday";
  return d.toLocaleDateString("en-AU", { day: "numeric", month: "short" });
}

export default function RequesterChatPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const theme = useTheme();
  const bottomRef = useRef(null);

  const [chat, setChat] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [sending, setSending] = useState(false);

  // Add tokens dialog
  const [tokenDialog, setTokenDialog] = useState(false);
  const [tokenAmount, setTokenAmount] = useState(10);
  const [customToken, setCustomToken] = useState("");
  const [tokenText, setTokenText] = useState("");
  const [addingTokens, setAddingTokens] = useState(false);

  // Close chat
  const [closeDialog, setCloseDialog] = useState(false);
  const [closing, setClosing] = useState(false);

  // Inline rating state
  const [thumbRating, setThumbRating] = useState(null);
  const [starRating, setStarRating] = useState(0);
  const [hoverStar, setHoverStar] = useState(0);
  const [ratingSubmitted, setRatingSubmitted] = useState(false);
  const [showRating, setShowRating] = useState(false);

  const isDark = theme.palette.mode === "dark";
  const animationsEnabled = localStorage.getItem("ui-animations") !== "false";
  const borderColor = theme.palette.text.primary;
  const mutedColor = theme.palette.text.secondary;
  const primary = theme.palette.primary.main;

  const authHeader = () => ({ Authorization: `Bearer ${localStorage.getItem("token")}` });

  const fetchChat = async () => {
    const token = localStorage.getItem("token");
    if (token === "debug_token") {
      setChat(MOCK_CHAT);
      setLoading(false);
      return;
    }
    try {
      const res = await fetch(`/v1/requester/chats/${id}`, { headers: authHeader() });
      const data = await res.json();
      if (!res.ok) { setChat(MOCK_CHAT); setLoading(false); return; }
      setChat(data);
    } catch {
      setChat(MOCK_CHAT);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchChat(); }, [id]);
  useEffect(() => {
    if (!chat) return;
    if (chat.status === "closed") {
      const t = setTimeout(() => {
        setShowRating(true);
        setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), 50);
      }, 800);
      return () => clearTimeout(t);
    }
    const interval = setInterval(fetchChat, 5000);
    return () => clearInterval(interval);
  }, [chat]);

  useEffect(() => {
    if (thumbRating) {
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), 50);
    }
  }, [thumbRating]);
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat?.messages, chat?.requests]);

  const handleSend = async () => {
    if (!message.trim()) return;
    setSending(true);
    try {
      await fetch(`/v1/requester/chats/${id}/messages`, {
        method: "POST",
        headers: { ...authHeader(), "Content-Type": "application/json" },
        body: JSON.stringify({ message: message.trim() }),
      });
      setMessage("");
      fetchChat();
    } finally {
      setSending(false);
    }
  };

  const handleAddTokens = async () => {
    if (!tokenText.trim()) return;
    setAddingTokens(true);
    try {
      await fetch(`/v1/requester/chats/${id}/requests`, {
        method: "POST",
        headers: { ...authHeader(), "Content-Type": "application/json" },
        body: JSON.stringify({ requestText: tokenText.trim(), tokensToSpend: tokenAmount }),
      });
      setTokenDialog(false);
      setTokenText("");
      setTokenAmount(10);
      setCustomToken("");
      fetchChat();
    } finally {
      setAddingTokens(false);
    }
  };

  const handleCloseChat = async () => {
    setClosing(true);
    try {
      await fetch(`/v1/requester/chats/${id}/close`, {
        method: "POST",
        headers: authHeader(),
      });
      setCloseDialog(false);
      fetchChat();
    } finally {
      setClosing(false);
    }
  };

  const isTokenPreset = TOKEN_PRESETS.includes(tokenAmount) && customToken === "";
  const isClosed = chat?.status === "closed";
  const totalTokens = chat?.requests?.reduce((s, r) => s + (r.tokensSpent || 0), 0) ?? 0;

  // Build a merged tl of messages + system events
  const timeline = [];
  let lastDate = null;

  const allEvents = [
    ...(chat?.messages || []).map((m) => ({ ...m, _type: "message", _ts: m.createdAt })),
    ...(chat?.requests || []).slice(1).map((r) => ({ ...r, _type: "token_event", _ts: r.createdAt })),
  ].sort((a, b) => new Date(a._ts) - new Date(b._ts));

  allEvents.forEach((ev) => {
    const d = formatDate(ev._ts);
    if (d !== lastDate) {
      timeline.push({ type: "divider", label: d });
      lastDate = d;
    }
    timeline.push(ev);
  });

  // System messages from responder
  const initialRequest = chat?.requests?.[0];
  const responderName = chat?.responderUsername;

  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "60vh" }}>
        <CircularProgress sx={{ color: borderColor }} />
      </Box>
    );
  }

  if (error || !chat) {
    return (
      <Box sx={{ textAlign: "center", py: 10 }}>
        <Typography sx={{ fontWeight: 700, opacity: 0.5 }}>{error || "Chat not found."}</Typography>
        <Button onClick={() => navigate("/chat")} sx={{ mt: 2, borderRadius: "99px", textTransform: "none", fontWeight: 600 }}>
          ← Back
        </Button>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        maxWidth: 720,
        mx: "auto",
        display: "flex",
        flexDirection: "column",
        height: "calc(100vh - 160px)",
      }}
    >
      {/* Header */}
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          gap: 1.5,
          pb: 2,
          mb: 1,
          borderBottom: `0.5px solid ${borderColor}22`,
          flexWrap: "wrap",
        }}
      >
        <IconButton onClick={() => navigate("/chat")} size="small" sx={{ color: mutedColor, "&:hover": { color: borderColor } }}>
          <ArrowBackIcon fontSize="small" />
        </IconButton>

        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Typography sx={{ fontWeight: 900, fontSize: "1rem", letterSpacing: "-0.3px", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
            {chat.title || "Untitled Chat"}
          </Typography>
          <Typography sx={{ fontSize: "0.68rem", color: mutedColor, fontWeight: 600 }}>
            {chat.category && `${chat.category} · `}
            {responderName ? `Responder: ${responderName}` : "Awaiting responder"}
            {" · "}
            <span style={{ textTransform: "uppercase", letterSpacing: 1 }}>{chat.status}</span>
          </Typography>
        </Box>

        {/* Token count */}
        <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
          <TokenIcon sx={{ fontSize: 13, color: mutedColor }} />
          <Typography sx={{ fontSize: "0.82rem", fontWeight: 700, color: mutedColor }}>{totalTokens}</Typography>
        </Box>

        {/* Add tokens */}
        {!isClosed && (
          <Button
            onClick={() => setTokenDialog(true)}
            startIcon={<TokenIcon sx={{ fontSize: "13px !important" }} />}
            sx={{
              borderRadius: "99px", px: 2, py: 0.5, fontWeight: 700, fontSize: "0.72rem",
              textTransform: "none", border: `0.5px solid ${borderColor}33`, color: mutedColor,
              "&:hover": { bgcolor: `${borderColor}0d`, color: borderColor, borderColor: `${borderColor}66` },
            }}
          >
            Add tokens
          </Button>
        )}

        {/* Close */}
        {!isClosed && (
          <Tooltip title="Close chat">
            <IconButton
              onClick={() => setCloseDialog(true)}
              size="small"
              sx={{ color: mutedColor, opacity: 0.4, "&:hover": { opacity: 1, color: theme.palette.error.main, bgcolor: `${theme.palette.error.main}15` } }}
            >
              <DoNotDisturbOnIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        )}
      </Box>

      {/* Messages */}
      <Box
        sx={{
          flex: 1,
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
          gap: 0.75,
          pb: 2,
          "&::-webkit-scrollbar": { width: 4 },
          "&::-webkit-scrollbar-thumb": { bgcolor: `${borderColor}22`, borderRadius: 2 },
        }}
      >
        {/* System note: */}
        {responderName && (
          <SystemPill>{responderName} is answering your request.</SystemPill>
        )}

        {timeline.map((item, i) => {
          if (item.type === "divider") {
            return <DateDivider key={`d${i}`} label={item.label} borderColor={borderColor} mutedColor={mutedColor} />;
          }

          if (item._type === "token_event") {
            return (
              <SystemPill key={item.requestID}>
                +{item.tokensSpent} tokens added · {formatTime(item._ts)}
              </SystemPill>
            );
          }

          const isMe = item.senderType === "requester";
          return (
            <ChatBubble
              key={item.messageID}
              isMe={isMe}
              text={item.message}
              time={formatTime(item.createdAt)}
              primary={primary}
              borderColor={borderColor}
              mutedColor={mutedColor}
              isDark={isDark}
              theme={theme}
            />
          );
        })}

        {/* Inline rating */}
        {isClosed && responderName && !ratingSubmitted && showRating && (
          <Box
            sx={{
              mt: 2,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 2,
              py: 3,
              px: 2,
              borderTop: `0.5px solid ${borderColor}15`,
            }}
          >
            <SystemPill>
              {responderName} has marked this conversation as complete.{"\n"}Did they answer your query?
            </SystemPill>

            {/* y/n */}
            <Box sx={{ display: "flex", gap: 1.5 }}>
              {["No", "Yes"].map((val) => {
                const selected = thumbRating === val.toLowerCase();
                return (
                  <Button
                    key={val}
                    onClick={() => setThumbRating(val.toLowerCase())}
                    sx={{
                      borderRadius: "99px", px: 4, py: 1, fontWeight: 700, fontSize: "0.9rem",
                      textTransform: "none", minWidth: 100,
                      border: `1.5px solid ${selected ? borderColor : `${borderColor}28`}`,
                      bgcolor: selected ? theme.palette.text.primary : "transparent",
                      color: selected ? theme.palette.background.default : mutedColor,
                      transition: animationsEnabled ? "all 0.15s ease" : "none",
                      "&:hover": {
                        bgcolor: selected ? theme.palette.text.primary : `${borderColor}0d`,
                        color: selected ? theme.palette.background.default : borderColor,
                      },
                    }}
                  >
                    {val}
                  </Button>
                );
              })}
            </Box>

            {/* rate */}
            {thumbRating && (
              <>
            <Typography sx={{ fontSize: "0.7rem", fontWeight: 700, color: mutedColor, letterSpacing: 1.5, textTransform: "uppercase" }}>
              Please rate your interaction with {responderName} today.
            </Typography>
            <Box sx={{ display: "flex", gap: 0.25 }}>
              {[1, 2, 3, 4, 5].map((s) => (
                <IconButton
                  key={s}
                  onMouseEnter={() => setHoverStar(s)}
                  onMouseLeave={() => setHoverStar(0)}
                  onClick={() => setStarRating(s)}
                  sx={{ p: 0.5, color: s <= (hoverStar || starRating) ? "#f5a623" : `${borderColor}28`, transition: "color 0.1s ease" }}
                >
                  {s <= (hoverStar || starRating)
                    ? <StarIcon sx={{ fontSize: 32 }} />
                    : <StarBorderIcon sx={{ fontSize: 32 }} />
                  }
                </IconButton>
              ))}
            </Box>
              </>
            )}

            {thumbRating && (
              <Button
                onClick={() => setRatingSubmitted(true)}
                sx={{
                  borderRadius: "99px", px: 4, py: 0.75, fontWeight: 700, fontSize: "0.82rem",
                  textTransform: "none", bgcolor: theme.palette.text.primary,
                  color: theme.palette.background.default,
                  "&:hover": { bgcolor: theme.palette.text.secondary },
                }}
              >
                Submit rating
              </Button>
            )}
          </Box>
        )}

        {isClosed && ratingSubmitted && (
          <SystemPill>Thank you for your rating!</SystemPill>
        )}

        {isClosed && !responderName && (
          <SystemPill>This conversation is archived. You cannot respond to it.</SystemPill>
        )}

        <div ref={bottomRef} />
      </Box>

      {/* Input bar */}
      {!isClosed ? (
        <Box sx={{ display: "flex", gap: 1, alignItems: "flex-end", pt: 2, borderTop: `0.5px solid ${borderColor}22` }}>
          <TextField
            placeholder="Type a message..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
            multiline
            maxRows={4}
            fullWidth
            variant="outlined"
            sx={{
              "& .MuiOutlinedInput-root": {
                borderRadius: "12px", fontSize: "0.9rem",
                bgcolor: isDark ? `${borderColor}08` : theme.palette.background.paper,
                "& fieldset": { border: `0.5px solid ${borderColor}22` },
                "&:hover fieldset": { border: `0.5px solid ${borderColor}55` },
                "&.Mui-focused fieldset": { border: `1px solid ${borderColor}88` },
              },
            }}
          />
          <IconButton
            onClick={handleSend}
            disabled={sending || !message.trim()}
            sx={{
              width: 44, height: 44, borderRadius: "12px", flexShrink: 0,
              bgcolor: primary, color: "#fff",
              transition: animationsEnabled ? "all 0.15s ease" : "none",
              "&:hover": { filter: "brightness(0.9)", transform: animationsEnabled ? "scale(1.05)" : "none" },
              "&.Mui-disabled": { opacity: 0.3, bgcolor: primary, color: "#fff" },
            }}
          >
            {sending ? <CircularProgress size={18} color="inherit" /> : <SendIcon sx={{ fontSize: 18 }} />}
          </IconButton>
        </Box>
      ) : (
        !ratingSubmitted && responderName ? null : (
          <Box sx={{ pt: 2, borderTop: `0.5px solid ${borderColor}22`, textAlign: "center" }}>
            <Typography sx={{ fontSize: "0.72rem", color: mutedColor, fontWeight: 600, textTransform: "uppercase", letterSpacing: 1 }}>
              This conversation is archived. You cannot respond to it.
            </Typography>
          </Box>
        )
      )}

      {/* Add Tokens */}
      <Dialog
        open={tokenDialog}
        onClose={() => setTokenDialog(false)}
        PaperProps={{ sx: { borderRadius: "12px", border: `0.5px solid ${borderColor}33`, bgcolor: theme.palette.background.paper, p: 1, minWidth: 340 } }}
      >
        <DialogTitle sx={{ fontWeight: 900, letterSpacing: "-0.5px" }}>Add Tokens</DialogTitle>
        <DialogContent sx={{ display: "flex", flexDirection: "column", gap: 2, pt: "8px !important" }}>
          <DialogContentText sx={{ color: mutedColor, fontSize: "0.85rem" }}>
            Add a new request with additional tokens to increase priority or expand scope.
          </DialogContentText>
          <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
            {TOKEN_PRESETS.map((t) => {
              const selected = isTokenPreset && tokenAmount === t;
              return (
                <Box
                  key={t}
                  component="button"
                  onClick={() => { setTokenAmount(t); setCustomToken(""); }}
                  sx={{
                    height: 30, px: 2, borderRadius: "99px",
                    border: `1.5px solid ${selected ? borderColor : `${borderColor}28`}`,
                    bgcolor: selected ? theme.palette.text.primary : "transparent",
                    color: selected ? theme.palette.background.default : mutedColor,
                    fontWeight: 700, fontSize: "0.8rem", cursor: "pointer",
                    fontFamily: theme.typography.fontFamily,
                    "&:hover": { border: `1.5px solid ${borderColor}77` },
                  }}
                >
                  {t}
                </Box>
              );
            })}
            <Box
              sx={{
                height: 30, px: 1, borderRadius: "99px", width: 70,
                border: `1.5px solid ${!isTokenPreset && customToken ? borderColor : `${borderColor}28`}`,
                bgcolor: !isTokenPreset && customToken ? theme.palette.text.primary : "transparent",
                display: "flex", alignItems: "center",
              }}
            >
              <input
                value={customToken}
                onChange={(e) => {
                  const raw = e.target.value;
                  if (raw !== "" && !/^\d+$/.test(raw)) return;
                  setCustomToken(raw);
                  const v = parseInt(raw, 10);
                  if (!isNaN(v) && v > 0) setTokenAmount(v);
                }}
                placeholder="custom"
                inputMode="numeric"
                style={{
                  width: "100%", border: "none", outline: "none", background: "transparent",
                  textAlign: "center", fontWeight: 700, fontSize: "0.75rem", fontFamily: "inherit",
                  color: !isTokenPreset && customToken ? theme.palette.background.default : theme.palette.text.secondary,
                }}
              />
            </Box>
          </Box>
          <TextField
            label="What do you need help with?"
            value={tokenText}
            onChange={(e) => setTokenText(e.target.value)}
            multiline
            minRows={3}
            fullWidth
            sx={{
              "& .MuiOutlinedInput-root": {
                borderRadius: "8px", fontSize: "0.9rem",
                "& fieldset": { border: `0.5px solid ${borderColor}33` },
                "&.Mui-focused fieldset": { border: `1px solid ${borderColor}88` },
              },
              "& .MuiInputLabel-root.Mui-focused": { color: borderColor },
            }}
          />
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2, gap: 1 }}>
          <Button onClick={() => setTokenDialog(false)} sx={{ borderRadius: "99px", px: 3, fontWeight: 600, fontSize: "0.8rem", textTransform: "none", color: mutedColor, border: `0.5px solid ${borderColor}33`, "&:hover": { bgcolor: `${borderColor}08` } }}>
            Cancel
          </Button>
          <Button
            onClick={handleAddTokens}
            disabled={addingTokens || !tokenText.trim()}
            sx={{
              borderRadius: "99px", px: 3, fontWeight: 600, fontSize: "0.8rem", textTransform: "none",
              bgcolor: theme.palette.text.primary, color: theme.palette.background.default,
              "&:hover": { bgcolor: theme.palette.text.secondary },
              "&.Mui-disabled": { opacity: 0.35, color: theme.palette.background.default, bgcolor: theme.palette.text.primary },
            }}
          >
            {addingTokens ? <CircularProgress size={14} color="inherit" /> : `Add ${tokenAmount} tokens`}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Close Chat */}
      <Dialog
        open={closeDialog}
        onClose={() => setCloseDialog(false)}
        PaperProps={{ sx: { borderRadius: "12px", border: `0.5px solid ${borderColor}33`, bgcolor: theme.palette.background.paper, p: 1 } }}
      >
        <DialogTitle sx={{ fontWeight: 900 }}>Close this chat?</DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ color: mutedColor, fontSize: "0.9rem" }}>
            The responder will no longer be able to reply. This cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2, gap: 1 }}>
          <Button onClick={() => setCloseDialog(false)} sx={{ borderRadius: "99px", px: 3, fontWeight: 600, fontSize: "0.8rem", textTransform: "none", color: mutedColor, border: `0.5px solid ${borderColor}33`, "&:hover": { bgcolor: `${borderColor}08` } }}>
            Cancel
          </Button>
          <Button
            onClick={handleCloseChat}
            sx={{ borderRadius: "99px", px: 3, fontWeight: 600, fontSize: "0.8rem", textTransform: "none", bgcolor: theme.palette.error.main, color: "#fff", "&:hover": { bgcolor: theme.palette.error.dark } }}
          >
            {closing ? <CircularProgress size={14} color="inherit" /> : "Close Chat"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

// Sub-parts
function ChatBubble({ isMe, text, time, primary, borderColor, mutedColor, isDark, theme }) {
  return (
    <Box sx={{ display: "flex", justifyContent: isMe ? "flex-end" : "flex-start", px: 1 }}>
      <Box sx={{ maxWidth: "72%", display: "flex", flexDirection: "column", alignItems: isMe ? "flex-end" : "flex-start", gap: 0.25 }}>
        <Box
          sx={{
            px: 2, py: 1.25,
            borderRadius: isMe ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
            bgcolor: isMe ? primary : (isDark ? "#2a2a2a" : "#f0f0f0"),
            color: isMe ? "#fff" : theme.palette.text.primary,
            fontSize: "0.9rem",
            lineHeight: 1.55,
            wordBreak: "break-word",
          }}
        >
          {text}
        </Box>
        <Typography sx={{ fontSize: "0.6rem", color: mutedColor, opacity: 0.65, px: 0.5 }}>
          {time}
        </Typography>
      </Box>
    </Box>
  );
}

function SystemPill({ children }) {
  return (
    <Box sx={{ display: "flex", justifyContent: "center", my: 0.5, px: 2 }}>
      <Typography
        sx={{
          fontSize: "0.68rem",
          color: "text.secondary",
          textAlign: "center",
          opacity: 0.75,
          fontWeight: 500,
          whiteSpace: "pre-line",
        }}
      >
        {children}
      </Typography>
    </Box>
  );
}

function DateDivider({ label, borderColor, mutedColor }) {
  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 2, my: 1, px: 1 }}>
      <Box sx={{ flex: 1, height: "0.5px", bgcolor: `${borderColor}18` }} />
      <Typography sx={{ fontSize: "0.62rem", fontWeight: 700, color: mutedColor, letterSpacing: 1, textTransform: "uppercase" }}>
        {label}
      </Typography>
      <Box sx={{ flex: 1, height: "0.5px", bgcolor: `${borderColor}18` }} />
    </Box>
  );
}
