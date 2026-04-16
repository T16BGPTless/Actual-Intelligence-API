import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

// MUI
import {
  TextField,
  Button,
  Alert,
  Box,
  Container,
  Typography,
  Divider
} from "@mui/material";

export default function Home() {
  return (
    <div style={{ padding: "2rem" }}>
      <h1>GPTless Actual Intelligence</h1>
      <p>Welcome.</p>
    </div>
  );
}