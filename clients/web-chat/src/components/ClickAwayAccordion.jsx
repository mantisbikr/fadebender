/**
 * ClickAwayAccordion Component
 * Accordion that closes when clicking outside
 */

import { useState, useRef, useEffect } from 'react';
import {
  Box,
  Typography,
  Collapse,
  IconButton,
  Paper
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon
} from '@mui/icons-material';

function ClickAwayAccordion({ title, children, sx = {} }) {
  const [expanded, setExpanded] = useState(false);
  const accordionRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (accordionRef.current && !accordionRef.current.contains(event.target)) {
        setExpanded(false);
      }
    }

    if (expanded) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [expanded]);

  return (
    <Paper
      ref={accordionRef}
      variant="outlined"
      sx={{ mt: 1, bgcolor: 'background.paper', ...sx }}
    >
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          p: 1.5,
          cursor: 'pointer',
          '&:hover': {
            bgcolor: 'action.hover'
          }
        }}
        onClick={() => setExpanded(!expanded)}
      >
        <Typography variant="body2" color="text.primary">
          {title}
        </Typography>
        <IconButton
          size="small"
          sx={{
            transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
            transition: 'transform 0.2s'
          }}
        >
          <ExpandMoreIcon />
        </IconButton>
      </Box>
      <Collapse in={expanded}>
        <Box sx={{ p: 1.5, pt: 0, borderTop: '1px solid', borderColor: 'divider' }}>
          {children}
        </Box>
      </Collapse>
    </Paper>
  );
}

export default ClickAwayAccordion;