import {
  Box,
  Typography,
  Paper,
  Button,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  useTheme,
} from "@mui/material";
import { useState, useEffect, useRef } from "react";
import axios from "axios";
import starterCat from "../assets/tokens/starter.png";
import basicCat from "../assets/tokens/basic.png";
import advancedCat from "../assets/tokens/advanced.png";
import proCat from "../assets/tokens/pro.png";
import { ScrollSection, getSubSectionStyle } from "../helpers.jsx"

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL

function Tokens() {
  const theme = useTheme();

  const [balance, setBalance] = useState(0);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isConfirmPurchaseOpen, setIsConfirmPurchaseOpen] = useState(false);
  const [selectedPackage, setSelectedPackage] = useState(null);
  const [isRedeemOpen, setIsRedeemOpen] = useState(false);
  const [redeemAmount, setRedeemAmount] = useState("");

  // theme stuff taken from joey idk how it works fully - bevn
  const isDarkMode = theme.palette.mode === "dark";
  const animationsEnabled = localStorage.getItem("ui-animations") !== "false";

  const sectionShadow = isDarkMode
    ? `0 20px 60px ${theme.palette.primary.main}44`
    : "0 20px 40px rgba(0,0,0,0.1)";

  const subSectionStyle = getSubSectionStyle();

  const packages = [
    {
      name: "Starter",
      tokens: 10,
      price: 20,
      cat: starterCat,
    },
    {
      name: "Basic",
      tokens: 20,
      price: 35,
      cat: basicCat,
    },
    {
      name: "Advanced",
      tokens: 50,
      price: 70,
      cat: advancedCat,
    },
    {
      name: "Pro",
      tokens: 100,
      price: 100,
      cat: proCat,
    },
  ];

  useEffect(() => {
    const fetchBalance = async () => {
      try {
        const accessToken = localStorage.getItem("token");

        if (!accessToken) {
          setError("No access token found. Please log in again.");
          return;
        }

        const res = await axios.get(`${BACKEND_URL}/v1/tokens`, {
          headers: {
            AccessToken: accessToken,
          },
        });

        setBalance(res.data.tokenBalance);
      } catch (err) {
        setError(err.response?.data?.message || "Could not load token balance");
      }
    };

    fetchBalance();
  }, []);

  const openConfirmPurchase = (pkg) => {
    setSelectedPackage(pkg);
    setIsConfirmPurchaseOpen(true);
  };

  const closeConfirmPurchase = () => {
    setIsConfirmPurchaseOpen(false);
    setSelectedPackage(null);
  };

  const openRedeem = () => {
    setRedeemAmount("");
    setIsRedeemOpen(true);
  };

  const closeRedeem = () => {
    setIsRedeemOpen(false);
    setRedeemAmount("");
  };

  const handleBuy = async (tokenAmount, cost) => {
    try {
      setLoading(true);
      setError("");
      setMessage("");

      const accessToken = localStorage.getItem("token");

      if (!accessToken) {
        setError("No access token found. Please log in again.");
        return false;
      }

      const res = await axios.post(
        `${BACKEND_URL}/v1/tokens/buy`,
        {
          tokens: tokenAmount,
          cost: cost,
        },
        {
          headers: {
            AccessToken: accessToken,
          },
        }
      );

      setBalance(res.data.tokenBalance);
      setMessage(`Added ${res.data.tokensAdded} tokens successfully`);
      return true;
    } catch (err) {
      closeConfirmPurchase();
      closeRedeem();
      setError(err.response?.data?.message || "Error buying tokens");
      return false;
    } finally {
      setLoading(false);
    }
  };

  const confirmPurchase = async () => {
    if (!selectedPackage) return;

    const success = await handleBuy(selectedPackage.tokens, selectedPackage.price);
    if (success) {
      closeConfirmPurchase();
    }
  };

  const handleRedeem = async () => {
    try {
      setLoading(true);
      setError("");
      setMessage("");

      const accessToken = localStorage.getItem("token");

      if (!accessToken) {
        setError("No access token found. Please log in again.");
        return;
      }

      const amount = Number(redeemAmount);

      if (!redeemAmount || isNaN(amount) || amount <= 0 || amount > balance) {
        setError("Enter a valid number of tokens to redeem.");
        closeRedeem();
        return;
      }

      const res = await axios.post(
        `${BACKEND_URL}/v1/tokens/redeem`,
        {
          tokens: amount,
        },
        {
          headers: {
            AccessToken: accessToken,
          },
        }
      );

      setBalance(res.data.tokenBalance);
      setMessage(`Redeemed ${res.data.tokensRedeemed} tokens successfully`);
      closeRedeem();
    } catch (err) {
      closeConfirmPurchase();
      closeRedeem();
      setError(err.response?.data?.message || "Error redeeming tokens");
    } finally {
      setLoading(false);
    }
  };

  const buttonBase = (isPrimary) => ({
    py: 2,
    px: 4,
    width: "100%",
    maxWidth: "280px",
    borderRadius: 0,
    textTransform: "uppercase",
    fontSize: "0.9rem",
    fontWeight: 900,
    letterSpacing: "2px",
    transition: animationsEnabled ? "all 0.2s ease-in-out" : "none",
    border: `2px solid ${theme.palette.text.primary}`,
    bgcolor: isPrimary ? theme.palette.text.primary : "transparent",
    color: isPrimary
      ? theme.palette.background.default
      : theme.palette.text.primary,
    "&:hover": {
      bgcolor: isPrimary
        ? theme.palette.text.secondary
        : theme.palette.text.primary,
      color: theme.palette.background.default,
      transform: animationsEnabled ? "translateY(-2px)" : "none",
      boxShadow: animationsEnabled
        ? `6px 6px 0px ${theme.palette.text.primary}44`
        : "none",
    },
    "&.Mui-disabled": {
      bgcolor: isPrimary ? theme.palette.text.primary : "transparent",
      color: isPrimary
        ? theme.palette.background.default
        : theme.palette.text.primary,
      border: `2px solid ${theme.palette.text.primary}`,
      opacity: 0.6,
    },
  });

  return (
    <Box
      sx={{
        minHeight: "100vh",
        py: 8,
        px: 3,
        bgcolor: theme.palette.background.default,
      }}
    >
      <Box sx={{ maxWidth: 1100, mx: "auto" }}>
        {/* Title text */}
        <ScrollSection index={0}>
          <Box sx={{ textAlign: "center", mb: 8 }}>
            <Box
              sx={{
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                gap: 2,
                mb: -1,
              }}
            >
              <Box
                sx={{
                  width: 40,
                  borderBottom: `3px solid ${theme.palette.text.primary}`,
                }}
              />

              <Typography
                variant="overline"
                sx={{
                  fontWeight: 900,
                  letterSpacing: 4,
                  color: theme.palette.text.primary,
                }}
              >
                CAT.v1
              </Typography>

              <Box
                sx={{
                  width: 40,
                  borderBottom: `3px solid ${theme.palette.text.primary}`,
                }}
              />
            </Box>

            <Typography
              variant="h2"
              sx={{
                fontWeight: 900,
                letterSpacing: "-2px",
                color: theme.palette.text.primary,
              }}
            >
              TOKENS
            </Typography>

            <Typography
              variant="body2"
              sx={{
                opacity: 0.6,
                fontWeight: 700,
                letterSpacing: 1,
                textTransform: "uppercase",
                color: theme.palette.text.primary,
              }}
            >
              Purr-chase and redeem tokens
            </Typography>
          </Box>
        </ScrollSection>

        {/* Error window */}
        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: {
              xs: "1fr",
              sm: "1fr 1fr",
            },
            gap: 3,
          }}
        >
          {message && (
            <Box
              sx={{
                gridColumn: {
                  xs: "span 1",
                  sm: "span 2",
                },
              }}
            >
              <Alert
                severity="success"
                sx={{
                  borderRadius: 0,
                  fontWeight: 700,
                }}
              >
                {message}
              </Alert>
            </Box>
          )}

          {error && (
            <Box
              sx={{
                gridColumn: {
                  xs: "span 1",
                  sm: "span 2",
                },
              }}
            >
              <Alert
                severity="error"
                sx={{
                  borderRadius: 0,
                  fontWeight: 700,
                }}
              >
                {error}
              </Alert>
            </Box>
          )}
          {/* Table containing all of the boxy items  */}
          <Box
            sx={{
              gridColumn: {
                xs: "span 1",
                sm: "span 2",
              },
            }}
          >
            {/* Tokens display, is 2 wide in the table */}
            <ScrollSection index={1}>
              <Paper
                elevation={0}
                sx={{
                  p: 4,
                  borderRadius: 0,
                  border: `3px solid ${theme.palette.text.primary}`,
                  bgcolor: theme.palette.background.paper,
                  color: theme.palette.text.primary,
                  boxShadow: "none",
                  transition: "all 0.3s ease",
                  "&:hover": {
                    boxShadow: animationsEnabled ? sectionShadow : "none",
                    transform: animationsEnabled ? "translateY(-4px)" : "none",
                  },
                }}
              >
                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    gap: 2,
                    flexWrap: "wrap",
                  }}
                >
                  <Box>
                    <Typography
                      variant="overline"
                      sx={{
                        color: theme.palette.text.secondary,
                        fontWeight: 900,
                        letterSpacing: 3,
                      }}
                    >
                      Current Balance
                    </Typography>

                    <Typography
                      variant="h2"
                      sx={{
                        fontWeight: 900,
                        color: theme.palette.text.primary,
                        lineHeight: 1.1,
                      }}
                    >
                      {balance} Tokens
                    </Typography>
                  </Box>

                  <Button
                    onClick={openRedeem}
                    disabled={loading}
                    sx={{
                      ...buttonBase(true),
                      maxWidth: "unset",
                      width: "auto",
                      minWidth: "170px",
                    }}
                  >
                    Redeem
                  </Button>
                </Box>
              </Paper>
            </ScrollSection>
          </Box>

          {/* 4 different token bundles */}
          {packages.map((pkg, index) => (
            <ScrollSection
              key={pkg.name}
              index={index + 2}
              delay={index * 80}
            >
              <Paper
                elevation={0}
                sx={{
                  ...subSectionStyle,
                  p: 3,
                  minHeight: 320,
                  justifyContent: "space-between",
                  alignItems: "stretch",
                  borderRadius: 0,
                  border: `3px solid ${theme.palette.text.primary}`,
                  boxShadow: "none",
                  overflow: "hidden",
                }}
              >
                <Box>
                  <Box
                    sx={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      mb: 3,
                      pb: 2,
                      borderBottom: `2px solid ${theme.palette.text.primary}`,
                    }}
                  >
                    <Typography
                      variant="h4"
                      sx={{
                        fontWeight: 900,
                        color: theme.palette.text.primary,
                      }}
                    >
                      {pkg.name}
                    </Typography>

                    <Typography
                      variant="h5"
                      sx={{
                        fontWeight: 900,
                        color: theme.palette.text.primary,
                      }}
                    >
                      ${pkg.price}
                    </Typography>
                  </Box>

                  <Box
                    sx={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      gap: 2,
                      mb: 3,
                    }}
                  >
                    <Box>
                      <Typography
                        variant="h2"
                        sx={{
                          fontWeight: 900,
                          color: theme.palette.text.primary,
                          lineHeight: 1,
                        }}
                      >
                        {pkg.tokens}
                      </Typography>

                      <Typography
                        variant="body2"
                        sx={{
                          color: theme.palette.text.secondary,
                          fontWeight: 700,
                          textTransform: "uppercase",
                          letterSpacing: 1,
                        }}
                      >
                        Tokens
                      </Typography>
                    </Box>

                    <Box
                      component="img"
                      src={pkg.cat}
                      alt={`${pkg.name} cat`}
                      sx={{
                        width: { xs: 180, md: 260 },
                        height: { xs: 120, md: 170 },
                        objectFit: "contain",
                        flexShrink: 0,
                        filter: isDarkMode
                          ? "invert(1) contrast(1.15)"
                          : "none",
                        transition: "filter 0.3s ease",
                      }}
                    />
                  </Box>
                </Box>

                <Button
                  disabled={loading}
                  onClick={() => openConfirmPurchase(pkg)}
                  sx={buttonBase(true)}
                >
                  Buy Tokens
                </Button>
              </Paper>
            </ScrollSection>
          ))}
        </Box>
      </Box>

      {/* Purchase confirm popup */}
      <Dialog
        open={isConfirmPurchaseOpen}
        onClose={closeConfirmPurchase}
        fullWidth
        maxWidth="sm"
        PaperProps={{
          sx: {
            borderRadius: 0,
            border: `3px solid ${theme.palette.text.primary}`,
            bgcolor: theme.palette.background.paper,
            boxShadow: sectionShadow,
          },
        }}
      >
        <DialogTitle
          sx={{
            fontWeight: 900,
            fontSize: "1.4rem",
            pb: 1,
            color: theme.palette.text.primary,
          }}
        >
          Confirm Purr-chase
        </DialogTitle>

        <DialogContent sx={{ pt: 1 }}>
          <Typography
            variant="body1"
            sx={{ color: theme.palette.text.primary, mb: 1.5 }}
          >
            Your card on file will be charged, and you will receive an invoice
            email.
          </Typography>

          <Typography
            variant="body2"
            sx={{
              color: theme.palette.text.secondary,
              mb: 3,
              fontStyle: "italic",
            }}
          >
            Note: as this is still a demo, we have not implemented card
            charging.
          </Typography>

          <Typography
            variant="subtitle2"
            sx={{
              color: theme.palette.text.secondary,
              textTransform: "uppercase",
              letterSpacing: "0.06em",
              mb: 1.5,
              fontWeight: 700,
            }}
          >
            Package
          </Typography>

          {selectedPackage && (
            <Box
              sx={{
                border: `2px solid ${theme.palette.text.primary}`,
                borderRadius: 0,
                p: 2.5,
                bgcolor: theme.palette.background.default,
              }}
            >
              <Box
                sx={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  mb: 2,
                }}
              >
                <Typography
                  variant="h6"
                  sx={{ fontWeight: 900, color: theme.palette.text.primary }}
                >
                  {selectedPackage.name}
                </Typography>

                <Typography
                  variant="h6"
                  sx={{ fontWeight: 900, color: theme.palette.text.primary }}
                >
                  ${selectedPackage.price}
                </Typography>
              </Box>

              <Box
                sx={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  gap: 2,
                }}
              >
                <Box>
                  <Typography
                    variant="h4"
                    sx={{
                      fontWeight: 900,
                      color: theme.palette.text.primary,
                      lineHeight: 1,
                    }}
                  >
                    {selectedPackage.tokens}
                  </Typography>

                  <Typography
                    variant="body2"
                    sx={{ color: theme.palette.text.secondary }}
                  >
                    Tokens
                  </Typography>
                </Box>

                {selectedPackage.cat && (
                  <Box
                    component="img"
                    src={selectedPackage.cat}
                    alt={`${selectedPackage.name} cat`}
                    sx={{
                      width: 220,
                      height: 140,
                      objectFit: "contain",
                      filter: isDarkMode
                        ? "invert(1) contrast(1.15)"
                        : "none",
                      transition: "filter 0.3s ease",
                    }}
                  />
                )}
              </Box>
            </Box>
          )}
        </DialogContent>

        <DialogActions sx={{ px: 3, pb: 3, pt: 1, gap: 1 }}>
          <Button
            onClick={closeConfirmPurchase}
            disabled={loading}
            sx={{
              ...buttonBase(false),
              maxWidth: "unset",
              width: "auto",
              py: 1,
              px: 3,
            }}
          >
            Cancel
          </Button>

          <Button
            onClick={confirmPurchase}
            disabled={loading || !selectedPackage}
            sx={{
              ...buttonBase(true),
              maxWidth: "unset",
              width: "auto",
              py: 1,
              px: 3,
            }}
          >
            {loading ? "Processing..." : "Confirm"}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Redeem tokens popup */}
      <Dialog
        open={isRedeemOpen}
        onClose={closeRedeem}
        fullWidth
        maxWidth="xs"
        PaperProps={{
          sx: {
            borderRadius: 0,
            border: `3px solid ${theme.palette.text.primary}`,
            bgcolor: theme.palette.background.paper,
            boxShadow: sectionShadow,
          },
        }}
      >
        <DialogTitle
          sx={{
            fontWeight: 900,
            fontSize: "1.4rem",
            pb: 1,
            color: theme.palette.text.primary,
          }}
        >
          Redeem Tokens
        </DialogTitle>

        <DialogContent sx={{ pt: 1 }}>
          <Typography
            variant="body1"
            sx={{ color: theme.palette.text.primary, mb: 2 }}
          >
            Enter the number of tokens you want to redeem and the money will be
            sent to the given account.
          </Typography>

          <Typography
            variant="body2"
            sx={{
              color: theme.palette.text.secondary,
              mb: 3,
              fontStyle: "italic",
            }}
          >
            Note: as this is still a demo, we have not implemented payouts.
          </Typography>

          <TextField
            fullWidth
            label="Tokens to redeem"
            type="number"
            value={redeemAmount}
            onChange={(e) => setRedeemAmount(e.target.value)}
            sx={{
              "& .MuiOutlinedInput-root": {
                borderRadius: 0,
              },
            }}
          />

          <Box
            sx={{
              mt: 3,
              p: 2.5,
              borderRadius: 0,
              bgcolor: theme.palette.background.default,
              border: `2px solid ${theme.palette.text.primary}`,
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <Typography
              variant="h5"
              sx={{
                color: theme.palette.text.primary,
                fontWeight: 700,
              }}
            >
              Payout:
            </Typography>

            <Typography
              variant="h5"
              sx={{
                fontWeight: 900,
                color: theme.palette.text.primary,
              }}
            >
              ${((Number(redeemAmount) || 0) * 0.8).toFixed(2)}
            </Typography>
          </Box>
        </DialogContent>

        <DialogActions sx={{ px: 3, pb: 3, pt: 1, gap: 1 }}>
          <Button
            onClick={closeRedeem}
            disabled={loading}
            sx={{
              ...buttonBase(false),
              maxWidth: "unset",
              width: "auto",
              py: 1,
              px: 3,
            }}
          >
            Cancel
          </Button>

          <Button
            onClick={handleRedeem}
            disabled={loading}
            sx={{
              ...buttonBase(true),
              maxWidth: "unset",
              width: "auto",
              py: 1,
              px: 3,
            }}
          >
            {loading ? "Processing..." : "Redeem"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default Tokens;