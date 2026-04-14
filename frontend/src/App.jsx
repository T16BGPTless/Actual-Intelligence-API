import { Routes, Route } from "react-router-dom";
import { Box, Container } from "@mui/material";
import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import Login from "./pages/auth/Login";
import Register from "./pages/auth/Register";

function App() {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>  
      <Navbar />
      <Box component="main" sx={{ flexGrow: 1, pt: '64px' }}>
        <Container 
          maxWidth="lg" 
          sx={{ 
            py: 4,
            px: { xs: 2, lg: 0 }
          }}
        >
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
          </Routes>
        </Container>
      </Box>

    </Box>
  );
}

export default App;