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
  Typography,
  useTheme,
} from "@mui/material";
import SendIcon from "@mui/icons-material/Send";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import TokenIcon from "@mui/icons-material/Token";
import DoneAllIcon from "@mui/icons-material/DoneAll";

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

export default function ResponderChatPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const theme = useTheme();
  const bottomRef = useRef(null);

  const [chat, setChat] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [step, setStep] = useState("chat"); // always go straight to chat since claiming happens in TaskList
  const [message, setMessage] = useState("");
  const [sending, setSending] = useState(false);
  const [sendError, setSendError] = useState("");
  const [fulfillDialog, setFulfillDialog] = useState(false);
  const [fulfilling, setFulfilling] = useState(false);
  const [fulfilled, setFulfilled] = useState(false);

  const isDark = theme.palette.mode === "dark";
  const animationsEnabled = localStorage.getItem("ui-animations") !== "false";
  const borderColor = theme.palette.text.primary;
  const mutedColor = theme.palette.text.secondary;

  const authHeader = () => ({ Authorization: `Bearer ${localStorage.getItem("token")}` });

  const fetchChat = async () => {
    try {
      const res = await fetch(`/v1/responder/chats/${id}`, { headers: authHeader() });
      const data = await res.json();
      if (!res.ok) { setLoadError("Chat not found."); return; }
      setChat(data);
    } catch {
      setLoadError("Network error.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchChat(); }, [id]);
  useEffect(() => {
    if (!chat) return;
    const interval = setInterval(fetchChat, 5000);
    return () => clearInterval(interval);
  }, [chat]);
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat?.messages]);

  const handleSend = async () => {
    if (!message.trim()) return;
    setSending(true);
    setSendError("");
    try {
      const res = await fetch(`/v1/responder/chats/${id}/messages`, {
        method: "POST",
        headers: { ...authHeader(), "Content-Type": "application/json" },
        body: JSON.stringify({ message: message.trim() }),
      });
      if (!res.ok) {
        const data = await res.json();
        setSendError(data?.message || "Failed to send message.");
        return;
      }
      setMessage("");
      fetchChat();
    } finally {
      setSending(false);
    }
  };

  const handleFulfill = async () => {
    setFulfilling(true);
    try {
      const res = await fetch(`/v1/responder/chats/${id}/close`, {
        method: "POST",
        headers: authHeader(),
      });
      if (res.ok) { setFulfillDialog(false); setFulfilled(true); fetchChat(); }
    } finally {
      setFulfilling(false);
    }
  };

  const totalTokens = chat?.tokens ?? chat?.tokensSpent ?? chat?.requests?.reduce((s, r) => s + (r.tokensSpent || 0), 0) ?? 0;

  // Build tl
  const timeline = [];
  let lastDate = null;

  const initialEvent = chat?.originalRequest ? {
    type: "message",
    _ts: chat.createdAt,
    messageID: "initial-request",
    senderType: "requester",
    message: chat.originalRequest,
    createdAt: chat.createdAt,
  } : null;

  const allEvents = [
    ...(initialEvent ? [{ ...initialEvent, _ts: initialEvent.createdAt }] : []),
    ...(chat?.messages || []).map((m) => ({ ...m, type: "message", _ts: m.createdAt })),
  ].sort((a, b) => new Date(a._ts) - new Date(b._ts));

  allEvents.forEach((ev) => {
    const d = formatDate(ev._ts);
    if (d !== lastDate) { timeline.push({ type: "divider", label: d }); lastDate = d; }
    timeline.push(ev);
  });

  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "60vh" }}>
        <CircularProgress sx={{ color: borderColor }} />
      </Box>
    );
  }

  if (loadError || !chat) {
    return (
      <Box sx={{ textAlign: "center", py: 10 }}>
        <Typography sx={{ fontWeight: 700, opacity: 0.5 }}>{loadError || "Chat not found."}</Typography>
        <Button onClick={() => navigate("/tasks/claim")} sx={{ mt: 2, borderRadius: "99px", textTransform: "none", fontWeight: 600 }}>
          ← Back
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 720, mx: "auto", display: "flex", flexDirection: "column", height: "calc(100vh - 160px)" }}>

      {/* Header */}
      <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, pb: 2, mb: 1, borderBottom: `0.5px solid ${borderColor}22`, flexWrap: "wrap" }}>
        <IconButton onClick={() => navigate("/tasks/claim")} size="small" sx={{ color: mutedColor, "&:hover": { color: borderColor } }}>
          <ArrowBackIcon fontSize="small" />
        </IconButton>
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Typography sx={{ fontWeight: 900, fontSize: "1rem", letterSpacing: "-0.3px", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
            {chat.title || "Untitled Chat"}
          </Typography>
          <Typography sx={{ fontSize: "0.68rem", color: mutedColor, fontWeight: 600 }}>
            {chat.category && `${chat.category} · `}
            Requester: {chat.requesterUsername || "Unknown"}
            {" · "}
            <span style={{ textTransform: "uppercase", letterSpacing: 1 }}>{chat.status}</span>
          </Typography>
        </Box>
        <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
          <TokenIcon sx={{ fontSize: 13, color: mutedColor }} />
          <Typography sx={{ fontSize: "0.82rem", fontWeight: 700, color: mutedColor }}>{totalTokens}</Typography>
        </Box>
        {!fulfilled && chat.status !== "closing" && chat.status !== "closed" && (
          <Button
            onClick={() => setFulfillDialog(true)}
            startIcon={<DoneAllIcon sx={{ fontSize: "14px !important" }} />}
            sx={{
              borderRadius: "99px", px: 2, py: 0.5, fontWeight: 700, fontSize: "0.72rem",
              textTransform: "none", bgcolor: theme.palette.text.primary,
              color: theme.palette.background.default,
              "&:hover": { bgcolor: theme.palette.text.secondary },
            }}
          >
            Finish Job
          </Button>
        )}
      </Box>

      {/* Messages */}
      <Box sx={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: 0.75, pb: 2, "&::-webkit-scrollbar": { width: 4 }, "&::-webkit-scrollbar-thumb": { bgcolor: `${borderColor}22`, borderRadius: 2 } }}>
        <SystemPill>You are answering this request.{chat.title ? `\nYou have titled this request: ${chat.title}.` : ""}</SystemPill>

        {timeline.map((item, i) => {
          if (item.type === "divider") return <DateDivider key={`d${i}`} label={item.label} borderColor={borderColor} mutedColor={mutedColor} />;
          const isMe = item.senderType === "responder";
          return (
            <Box key={item.messageID} sx={{ display: "flex", justifyContent: isMe ? "flex-end" : "flex-start", px: 1 }}>
              <Box sx={{ maxWidth: "72%", display: "flex", flexDirection: "column", alignItems: isMe ? "flex-end" : "flex-start", gap: 0.25 }}>
                <Box sx={{
                  px: 2, py: 1.25,
                  borderRadius: isMe ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
                  bgcolor: isMe ? (isDark ? "#fff" : borderColor) : (isDark ? "#2a2a2a" : "#f0f0f0"),
                  color: isMe ? (isDark ? "#000" : theme.palette.background.default) : theme.palette.text.primary,
                  fontSize: "0.9rem", lineHeight: 1.55, wordBreak: "break-word",
                }}>
                  {item.message}
                </Box>
                <Typography sx={{ fontSize: "0.6rem", color: mutedColor, opacity: 0.65, px: 0.5 }}>
                  {formatTime(item.createdAt)}
                </Typography>
              </Box>
            </Box>
          );
        })}

        {(fulfilled || chat.status === "closing" || chat.status === "closed") && (
          <SystemPill>
            {"Thank you! Please wait for the requester's confirmation to receive your tokens.\nIf a confirmation is not received within 24 hours, it will be automatically processed."}
          </SystemPill>
        )}

        <div ref={bottomRef} />
      </Box>

      {/* Send error */}
      {sendError && (
        <Typography sx={{ fontSize: "0.75rem", color: theme.palette.error.main, fontWeight: 600, px: 1, pb: 1 }}>
          {sendError}
        </Typography>
      )}

      {/* Input */}
      {!fulfilled && chat.status !== "closing" && chat.status !== "closed" ? (
        <Box sx={{ display: "flex", gap: 1, alignItems: "flex-end", pt: 2, borderTop: `0.5px solid ${borderColor}22` }}>
          <TextField
            placeholder="Response"
            value={message}
            onChange={(e) => { setMessage(e.target.value); if (sendError) setSendError(""); }}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
            multiline maxRows={4} fullWidth variant="outlined"
            sx={{ "& .MuiOutlinedInput-root": { borderRadius: "12px", fontSize: "0.9rem", bgcolor: isDark ? `${borderColor}08` : theme.palette.background.paper, "& fieldset": { border: `0.5px solid ${borderColor}22` }, "&:hover fieldset": { border: `0.5px solid ${borderColor}55` }, "&.Mui-focused fieldset": { border: `1px solid ${borderColor}88` } } }}
          />
          <IconButton onClick={handleSend} disabled={sending || !message.trim()}
            sx={{ width: 44, height: 44, borderRadius: "12px", flexShrink: 0, bgcolor: theme.palette.text.primary, color: theme.palette.background.default, transition: animationsEnabled ? "all 0.15s ease" : "none", "&:hover": { bgcolor: theme.palette.text.secondary, transform: animationsEnabled ? "scale(1.05)" : "none" }, "&.Mui-disabled": { opacity: 0.3, bgcolor: theme.palette.text.primary, color: theme.palette.background.default } }}>
            {sending ? <CircularProgress size={18} color="inherit" /> : <SendIcon sx={{ fontSize: 18 }} />}
          </IconButton>
        </Box>
      ) : (
        <Box sx={{ pt: 2, borderTop: `0.5px solid ${borderColor}22`, textAlign: "center" }}>
          <Typography sx={{ fontSize: "0.72rem", color: mutedColor, fontWeight: 600, textTransform: "uppercase", letterSpacing: 1 }}>
            This conversation is archived. You cannot respond to it.
          </Typography>
        </Box>
      )}

      {/* Finish Job Dialog */}
      <Dialog open={fulfillDialog} onClose={() => setFulfillDialog(false)}
        PaperProps={{ sx: { borderRadius: "12px", border: `0.5px solid ${borderColor}33`, bgcolor: theme.palette.background.paper, p: 1 } }}>
        <DialogTitle sx={{ fontWeight: 900 }}>Finish Job</DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ color: mutedColor, fontSize: "0.9rem" }}>
            Are you sure you're done? This will mark the task as complete and notify the requester to confirm and release your tokens.
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2, gap: 1 }}>
          <Button onClick={() => setFulfillDialog(false)} sx={{ borderRadius: "99px", px: 3, fontWeight: 600, fontSize: "0.8rem", textTransform: "none", color: mutedColor, border: `0.5px solid ${borderColor}33`, "&:hover": { bgcolor: `${borderColor}08` } }}>
            Cancel
          </Button>
          <Button onClick={handleFulfill}
            sx={{ borderRadius: "99px", px: 3, fontWeight: 600, fontSize: "0.8rem", textTransform: "none", bgcolor: theme.palette.text.primary, color: theme.palette.background.default, "&:hover": { bgcolor: theme.palette.text.secondary } }}>
            {fulfilling ? <CircularProgress size={14} color="inherit" /> : "Finish Job"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

function SystemPill({ children }) {
  return (
    <Box sx={{ display: "flex", justifyContent: "center", my: 0.5, px: 2 }}>
      <Typography sx={{ fontSize: "0.68rem", color: "text.secondary", textAlign: "center", opacity: 0.75, fontWeight: 500, whiteSpace: "pre-line" }}>
        {children}
      </Typography>
    </Box>
  );
}

function DateDivider({ label, borderColor, mutedColor }) {
  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 2, my: 1, px: 1 }}>
      <Box sx={{ flex: 1, height: "0.5px", bgcolor: `${borderColor}18` }} />
      <Typography sx={{ fontSize: "0.62rem", fontWeight: 700, color: mutedColor, letterSpacing: 1, textTransform: "uppercase" }}>{label}</Typography>
      <Box sx={{ flex: 1, height: "0.5px", bgcolor: `${borderColor}18` }} />
    </Box>
  );
}
