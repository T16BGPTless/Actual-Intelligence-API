import { Routes, Route } from "react-router-dom";
import { Box, Container } from "@mui/material";

import Navbar from "./components/Navbar";

import Home from "./pages/Home";
import Login from "./pages/auth/Login";
import Register from "./pages/auth/Register";
import Profile from "./pages/auth/Profile";
import Tokens from "./pages/Tokens";

import ChatList from "./pages/ChatList";
import ChatPage from "./pages/ChatPage";
import ChatCreate from "./pages/requester/ChatCreate";

import TaskList from "./pages/responder/TaskList";

function App() {
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        minHeight: "100vh",
        bgcolor: "#fff",
      }}
    >
      <Navbar />

      <Box component="main" sx={{ flexGrow: 1, pt: "64px" }}>
        <Container maxWidth="lg" sx={{ py: 4, px: { xs: 2, lg: 0 } }}>
          <Routes>
            <Route path="/" element={<Home />} />

            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            <Route path="/profile" element={<Profile />} />
            <Route path="/tokens" element={<Tokens />} />

            <Route path="/chat" element={<ChatList />} />
            <Route path="/chat/new" element={<ChatCreate />} />
            <Route path="/chat/:id" element={<ChatPage />} />

            <Route path="/tasks/claim" element={<TaskList />} />
          </Routes>
        </Container>
      </Box>
    </Box>
  );
}

export default App;