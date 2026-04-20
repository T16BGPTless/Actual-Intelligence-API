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

const MOCK_CHAT = {
  chatID: "mock-responder",
  title: "What should I have for lunch today?",
  category: "General",
  status: "open",
  requesterUsername: "George",
  responderUsername: null,
  createdAt: new Date(Date.now() - 3600000).toISOString(),
  messages: [
    { messageID: "m1", senderType: "requester", message: "What should I have for lunch today?", createdAt: new Date(Date.now() - 3500000).toISOString() },
  ],
  requests: [
    { requestID: "r1", requestText: "What should I have for lunch today?", status: "active", tokensSpent: 1, createdAt: new Date(Date.now() - 3500000).toISOString() },
  ],
};

export default function ResponderChatPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const theme = useTheme();
  const bottomRef = useRef(null);

  const [chat, setChat] = useState(null);
  const [loading, setLoading] = useState(true);
  const [step, setStep] = useState("claim");
  const [chatTitle, setChatTitle] = useState("");
  const [claiming, setClaiming] = useState(false);
  const [message, setMessage] = useState("");
  const [sending, setSending] = useState(false);
  const [fulfillDialog, setFulfillDialog] = useState(false);
  const [fulfillText, setFulfillText] = useState("");
  const [fulfilling, setFulfilling] = useState(false);
  const [fulfilled, setFulfilled] = useState(false);

  const isDark = theme.palette.mode === "dark";
  const animationsEnabled = localStorage.getItem("ui-animations") !== "false";
  const borderColor = theme.palette.text.primary;
  const mutedColor = theme.palette.text.secondary;
  const primary = theme.palette.primary.main;

  const authHeader = () => ({ Authorization: `Bearer ${localStorage.getItem("token")}` });
  const isDebug = localStorage.getItem("token") === "debug_token";

  const fetchChat = async () => {
    if (isDebug) {
      setChat(MOCK_CHAT);
      setLoading(false);
      return;
    }
    try {
      const res = await fetch(`/v1/responder/chats/${id}`, { headers: authHeader() });
      const data = await res.json();
      if (!res.ok) { setChat(MOCK_CHAT); setLoading(false); return; }
      setChat(data);
      // if already claimed, skip to chat
      if (data.responderUsername) setStep("chat");
    } catch {
      setChat(MOCK_CHAT);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchChat(); }, [id]);
  useEffect(() => {
    if (step !== "chat") return;
    const interval = setInterval(fetchChat, 5000);
    return () => clearInterval(interval);
  }, [step]);
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat?.messages]);

  const handleClaim = async () => {
    setClaiming(true);
    if (isDebug) {
      setTimeout(() => { setClaiming(false); setStep("title"); }, 500);
      return;
    }
    try {
      const res = await fetch(`/v1/responder/chats/${id}/claim`, {
        method: "POST",
        headers: authHeader(),
      });
      if (res.ok) setStep("title");
    } finally {
      setClaiming(false);
    }
  };

  // MAYU REMOVE forgot what backend does
  const handleTitleSubmit = async () => {
    // title is optional
    setStep("chat");
    fetchChat();
  };

  const handleSend = async () => {
    if (!message.trim()) return;
    setSending(true);
    if (isDebug) {
      setChat((prev) => ({
        ...prev,
        messages: [...prev.messages, {
          messageID: `m${Date.now()}`,
          senderType: "responder",
          message: message.trim(),
          createdAt: new Date().toISOString(),
        }],
      }));
      setMessage("");
      setSending(false);
      return;
    }
    try {
      await fetch(`/v1/responder/chats/${id}/messages`, {
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

  const handleFulfill = async () => {
    if (!fulfillText.trim()) return;
    setFulfilling(true);
    if (isDebug) {
      setTimeout(() => {
        setFulfilling(false);
        setFulfillDialog(false);
        setFulfilled(true);
      }, 600);
      return;
    }
    try {
      const res = await fetch(`/v1/responder/chats/${id}/fulfill-request`, {
        method: "POST",
        headers: { ...authHeader(), "Content-Type": "application/json" },
        body: JSON.stringify({ responseText: fulfillText.trim() }),
      });
      if (res.ok) { setFulfillDialog(false); setFulfilled(true); fetchChat(); }
    } finally {
      setFulfilling(false);
    }
  };

  const totalTokens = chat?.requests?.reduce((s, r) => s + (r.tokensSpent || 0), 0) ?? 0;

  // Build sorted timeline
  const timeline = [];
  let lastDate = null;
  (chat?.messages || []).forEach((msg) => {
    const d = formatDate(msg.createdAt);
    if (d !== lastDate) { timeline.push({ type: "divider", label: d }); lastDate = d; }
    timeline.push({ type: "message", ...msg });
  });

  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "60vh" }}>
        <CircularProgress sx={{ color: borderColor }} />
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
            {chatTitle || chat?.title || "Untitled Chat"}
          </Typography>
          <Typography sx={{ fontSize: "0.68rem", color: mutedColor, fontWeight: 600 }}>
            {chat?.category && `${chat.category} · `}
            Requester: {chat?.requesterUsername || "Unknown"}
            {" · "}
            <span style={{ textTransform: "uppercase", letterSpacing: 1 }}>{chat?.status}</span>
          </Typography>
        </Box>
        <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
          <TokenIcon sx={{ fontSize: 13, color: mutedColor }} />
          <Typography sx={{ fontSize: "0.82rem", fontWeight: 700, color: mutedColor }}>{totalTokens}</Typography>
        </Box>
        {step === "chat" && !fulfilled && (
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

      {/* CLAIM STEP */}
      {step === "claim" && (
        <Box sx={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 3, pb: 4 }}>
          {/* Show the initial request */}
          <Box sx={{ width: "100%", maxWidth: 480 }}>
            <Box sx={{ px: 2, py: 1.25, borderRadius: "18px 18px 18px 4px", bgcolor: isDark ? "#2a2a2a" : "#f0f0f0", color: theme.palette.text.primary, fontSize: "0.9rem", lineHeight: 1.55, mb: 1 }}>
              {chat?.requests?.[0]?.requestText || chat?.title}
            </Box>
            <Box sx={{ display: "flex", alignItems: "center", gap: 0.5, pl: 0.5 }}>
              <TokenIcon sx={{ fontSize: 12, color: mutedColor }} />
              <Typography sx={{ fontSize: "0.72rem", color: mutedColor, fontWeight: 600 }}>{totalTokens} tokens</Typography>
            </Box>
          </Box>

          <SystemPill>Once you claim a chat, only you will be able to see it.</SystemPill>

          <Button
            onClick={handleClaim}
            disabled={claiming}
            sx={{
              borderRadius: "99px", px: 5, py: 1.25, fontWeight: 700, fontSize: "0.9rem",
              textTransform: "none", bgcolor: theme.palette.text.primary,
              color: theme.palette.background.default, width: "100%", maxWidth: 320,
              "&:hover": { bgcolor: theme.palette.text.secondary },
            }}
          >
            {claiming ? <CircularProgress size={18} color="inherit" /> : "Claim Chat"}
          </Button>
        </Box>
      )}

      {/* TITLE STEP */}
      {step === "title" && (
        <Box sx={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 3, pb: 4 }}>
          <SystemPill>You are answering this request.</SystemPill>

          <TextField
            variant="standard"
            placeholder="Title Chat"
            value={chatTitle}
            onChange={(e) => setChatTitle(e.target.value)}
            fullWidth
            sx={{
              maxWidth: 400,
              "& .MuiInput-root": {
                fontSize: "1.4rem", fontWeight: 700,
                "&:before": { borderBottom: `2px solid ${borderColor}22` },
                "&:hover:not(.Mui-disabled):before": { borderBottom: `2px solid ${borderColor}66` },
                "&:after": { borderBottom: `2px solid ${borderColor}` },
              },
              "& .MuiInput-input::placeholder": { color: mutedColor, opacity: 1 },
            }}
          />

          <Button
            onClick={handleTitleSubmit}
            sx={{
              borderRadius: "99px", px: 5, py: 1.25, fontWeight: 700, fontSize: "0.9rem",
              textTransform: "none", bgcolor: theme.palette.text.primary,
              color: theme.palette.background.default, width: "100%", maxWidth: 320,
              "&:hover": { bgcolor: theme.palette.text.secondary },
            }}
          >
            Title Chat
          </Button>
        </Box>
      )}

      {/* CHAT STEP */}
      {step === "chat" && (
        <>
          <Box
            sx={{
              flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: 0.75, pb: 2,
              "&::-webkit-scrollbar": { width: 4 },
              "&::-webkit-scrollbar-thumb": { bgcolor: `${borderColor}22`, borderRadius: 2 },
            }}
          >
            <SystemPill>You are answering this request.{chatTitle ? `\nYou have titled this request ${chatTitle}.` : ""}</SystemPill>

            {timeline.map((item, i) => {
              if (item.type === "divider") {
                return <DateDivider key={`d${i}`} label={item.label} borderColor={borderColor} mutedColor={mutedColor} />;
              }
              // Responder persp
              const isMe = item.senderType === "responder";
              return (
                <Box key={item.messageID} sx={{ display: "flex", justifyContent: isMe ? "flex-end" : "flex-start", px: 1 }}>
                  <Box sx={{ maxWidth: "72%", display: "flex", flexDirection: "column", alignItems: isMe ? "flex-end" : "flex-start", gap: 0.25 }}>
                    <Box
                      sx={{
                        px: 2, py: 1.25,
                        borderRadius: isMe ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
                        bgcolor: isMe ? (isDark ? "#fff" : borderColor) : (isDark ? "#2a2a2a" : "#f0f0f0"),
                        color: isMe ? (isDark ? "#000" : theme.palette.background.default) : theme.palette.text.primary,
                        fontSize: "0.9rem", lineHeight: 1.55, wordBreak: "break-word",
                      }}
                    >
                      {item.message}
                    </Box>
                    <Typography sx={{ fontSize: "0.6rem", color: mutedColor, opacity: 0.65, px: 0.5 }}>
                      {formatTime(item.createdAt)}
                    </Typography>
                  </Box>
                </Box>
              );
            })}

            {fulfilled && (
              <SystemPill>
                {"Thank you! Please wait for the requester's confirmation to receive your tokens.\nIf a confirmation is not received within 24 hours, it will be automatically processed."}
              </SystemPill>
            )}

            <div ref={bottomRef} />
          </Box>

          {/* Input */}
          {!fulfilled ? (
            <Box sx={{ display: "flex", gap: 1, alignItems: "flex-end", pt: 2, borderTop: `0.5px solid ${borderColor}22` }}>
              <TextField
                placeholder="Response"
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
                  bgcolor: theme.palette.text.primary, color: theme.palette.background.default,
                  transition: animationsEnabled ? "all 0.15s ease" : "none",
                  "&:hover": { bgcolor: theme.palette.text.secondary, transform: animationsEnabled ? "scale(1.05)" : "none" },
                  "&.Mui-disabled": { opacity: 0.3, bgcolor: theme.palette.text.primary, color: theme.palette.background.default },
                }}
              >
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
        </>
      )}

      {/* fulfilled */}
      <Dialog
        open={fulfillDialog}
        onClose={() => setFulfillDialog(false)}
        PaperProps={{ sx: { borderRadius: "12px", border: `0.5px solid ${borderColor}33`, bgcolor: theme.palette.background.paper, p: 1, minWidth: 340 } }}
      >
        <DialogTitle sx={{ fontWeight: 900, letterSpacing: "-0.5px" }}>Finish Job</DialogTitle>
        <DialogContent sx={{ display: "flex", flexDirection: "column", gap: 2, pt: "8px !important" }}>
          <DialogContentText sx={{ color: mutedColor, fontSize: "0.85rem" }}>
            Provide a final summary or response to complete this task and claim your tokens.
          </DialogContentText>
          <TextField
            label="Final response"
            value={fulfillText}
            onChange={(e) => setFulfillText(e.target.value)}
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
          <Button onClick={() => setFulfillDialog(false)} sx={{ borderRadius: "99px", px: 3, fontWeight: 600, fontSize: "0.8rem", textTransform: "none", color: mutedColor, border: `0.5px solid ${borderColor}33`, "&:hover": { bgcolor: `${borderColor}08` } }}>
            Cancel
          </Button>
          <Button
            onClick={handleFulfill}
            disabled={fulfilling || !fulfillText.trim()}
            sx={{
              borderRadius: "99px", px: 3, fontWeight: 600, fontSize: "0.8rem", textTransform: "none",
              bgcolor: theme.palette.text.primary, color: theme.palette.background.default,
              "&:hover": { bgcolor: theme.palette.text.secondary },
              "&.Mui-disabled": { opacity: 0.35, color: theme.palette.background.default, bgcolor: theme.palette.text.primary },
            }}
          >
            {fulfilling ? <CircularProgress size={14} color="inherit" /> : "Submit & Finish"}
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