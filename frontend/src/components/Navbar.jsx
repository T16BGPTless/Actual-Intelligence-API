import { useNavigate } from 'react-router-dom';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';

function Navbar() {
  const navigate = useNavigate();

  return (
    <AppBar position="static">
      <Toolbar>
        <Typography
          variant="h6"
          sx={{ cursor: 'pointer' }}
          onClick={() => navigate('/')}
        >
          GPTless
        </Typography>
      </Toolbar>
    </AppBar>
  );
}

export default Navbar;