/**
 * ChatInput Component
 * Handles user input with validation and submission
 */

import { useState, useEffect, useRef, useMemo } from 'react';
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  Container,
  Chip,
  Fade,
  Button,
} from '@mui/material';
import { Send as SendIcon, Undo as UndoIcon, Clear as ClearIcon } from '@mui/icons-material';

// Common DAW typo corrections (defaults; merged with server-provided)
const DEFAULT_AUTOCORRECT_MAP = {
  // Track references
  'trak': 'track',
  'tracj': 'track',
  // Additional common typos
  'trac': 'track',
  'trck': 'track',

  // Volume terms
  'volum': 'volume',
  'vollume': 'volume',
  'loudr': 'louder',
  'quiter': 'quieter',
  'quietr': 'quieter',
  'incrase': 'increase',
  'increse': 'increase',
  'increace': 'increase',

  // Reduce/decrease
  'redducce': 'reduce',
  'redduce': 'reduce',
  'reduuce': 'reduce',
  'reducce': 'reduce',

  // Pan terms
  'pann': 'pan',
  'centre': 'center',
  'centr': 'center',

  // Effects
  'revreb': 'reverb',
  'reverbb': 'reverb',
  'revebr': 'reverb',
  'reverv': 'reverb',

  // Returns
  'retrun': 'return',
  'retun': 'return',

  // Common
  'strereo': 'stereo',
  'streo': 'stereo',
  'stere': 'stereo',
};

// Fuzzy match for typos (handle doubled chars, etc.)
function findBestMatch(word, AUTOCORRECT_MAP) {
  const lower = word.toLowerCase();

  // Don't autocorrect very short words (they're often valid)
  if (lower.length < 4) {
    // Only exact matches for short words
    return AUTOCORRECT_MAP[lower] || null;
  }

  // Exact match first
  if (AUTOCORRECT_MAP[lower]) {
    return AUTOCORRECT_MAP[lower];
  }

  // Try removing doubled characters (redducce → reduce)
  const dedoubled = lower.replace(/(.)\1+/g, '$1');
  if (AUTOCORRECT_MAP[dedoubled] && dedoubled !== lower) {
    return AUTOCORRECT_MAP[dedoubled];
  }

  // For longer words (5+ chars), try fuzzy matching
  if (lower.length >= 5) {
    for (const [typo, correction] of Object.entries(AUTOCORRECT_MAP)) {
      // Only match if lengths are similar
      if (Math.abs(typo.length - lower.length) > 2) continue;

      const distance = levenshteinDistance(lower, typo);
      if (distance === 1) {  // Only 1 character difference (very conservative)
        return correction;
      }
    }
  }

  return null;
}

// Simple Levenshtein distance for fuzzy matching
function levenshteinDistance(a, b) {
  const matrix = [];

  for (let i = 0; i <= b.length; i++) {
    matrix[i] = [i];
  }

  for (let j = 0; j <= a.length; j++) {
    matrix[0][j] = j;
  }

  for (let i = 1; i <= b.length; i++) {
    for (let j = 1; j <= a.length; j++) {
      if (b.charAt(i - 1) === a.charAt(j - 1)) {
        matrix[i][j] = matrix[i - 1][j - 1];
      } else {
        matrix[i][j] = Math.min(
          matrix[i - 1][j - 1] + 1,
          matrix[i][j - 1] + 1,
          matrix[i - 1][j] + 1
        );
      }
    }
  }

  return matrix[b.length][a.length];
}

export default function ChatInput({ onSubmit, onHelp, disabled, draft, typoCorrections }) {
  const [input, setInput] = useState('');
  const [lastCorrection, setLastCorrection] = useState(null); // {from, to, position}
  const [showUndo, setShowUndo] = useState(false);
  const textFieldRef = useRef(null);

  const focusInput = () => {
    try {
      const root = textFieldRef.current;
      if (!root) return;
      const inputEl = root.querySelector('input');
      if (inputEl) {
        inputEl.focus();
        // place cursor at end
        const val = inputEl.value || '';
        inputEl.setSelectionRange(val.length, val.length);
      }
    } catch {}
  };

  // Merge defaults with server-provided corrections
  const AUTOCORRECT_MAP = useMemo(() => {
    const ext = (typoCorrections && typeof typoCorrections === 'object') ? typoCorrections : {};
    const merged = { ...DEFAULT_AUTOCORRECT_MAP };
    Object.entries(ext).forEach(([k, v]) => {
      if (typeof k === 'string' && typeof v === 'string') {
        merged[String(k).toLowerCase()] = String(v).toLowerCase();
      }
    });
    return merged;
  }, [typoCorrections]);

  useEffect(() => {
    if (draft && typeof draft.text === 'string') {
      setInput(draft.text);
    }
  }, [draft?.ts]);

  useEffect(() => {
    if (showUndo) {
      const timer = setTimeout(() => setShowUndo(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [showUndo]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || disabled) return;

    // Unified handler - the backend will determine if it's a command or help query
    onSubmit(input.trim());
    setInput('');
    // Return cursor focus to input immediately
    setTimeout(() => focusInput(), 0);
  };

  const applyAutocorrect = (text, cursorPosition) => {
    // Find the word before cursor
    const beforeCursor = text.substring(0, cursorPosition);
    const words = beforeCursor.split(/\s+/);
    const lastWord = words[words.length - 1];

    if (!lastWord) return { text, newPosition: cursorPosition, correction: null };

    // Use fuzzy matching to find best correction
    const correction = findBestMatch(lastWord, AUTOCORRECT_MAP);
    if (correction && correction !== lastWord.toLowerCase()) {
      // Replace the last word with correction
      const beforeWord = beforeCursor.substring(0, beforeCursor.lastIndexOf(lastWord));
      const afterCursor = text.substring(cursorPosition);
      const newText = beforeWord + correction + afterCursor;
      const newPosition = beforeWord.length + correction.length;

      return {
        text: newText,
        newPosition,
        correction: { from: lastWord, to: correction, originalText: text, position: beforeWord.length }
      };
    }

    return { text, newPosition: cursorPosition, correction: null };
  };

  const handleUndo = () => {
    if (lastCorrection) {
      setInput(lastCorrection.originalText);
      setLastCorrection(null);
      setShowUndo(false);

      // Restore cursor position
      setTimeout(() => {
        if (textFieldRef.current) {
          const inputElement = textFieldRef.current.querySelector('input');
          if (inputElement) {
            const pos = lastCorrection.position + lastCorrection.from.length;
            inputElement.setSelectionRange(pos, pos);
          }
        }
      }, 0);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
      return;
    }

    // Auto-correct on space or tab
    if (e.key === ' ' || e.key === 'Tab') {
      const cursorPosition = e.target.selectionStart;
      const { text: newText, newPosition, correction } = applyAutocorrect(input, cursorPosition);

      if (newText !== input && correction) {
        e.preventDefault();
        setInput(newText + (e.key === ' ' ? ' ' : ''));
        setLastCorrection(correction);
        setShowUndo(true);

        // Restore cursor position after React updates
        setTimeout(() => {
          const newCursor = newPosition + (e.key === ' ' ? 1 : 0);
          e.target.setSelectionRange(newCursor, newCursor);
        }, 0);
      }
    }
  };

  // After processing completes, ensure the input regains focus
  useEffect(() => {
    if (!disabled) {
      focusInput();
    }
  }, [disabled]);

  return (
    <Paper elevation={2} sx={{ borderTop: 1, borderColor: 'divider' }}>
      <Container id="chat-input-root" maxWidth="lg" sx={{ py: 1.5, position: 'relative' }}>
        {/* Autocorrect Undo Button - iPhone style */}
        <Fade in={showUndo && lastCorrection}>
          <Box
            onClick={handleUndo}
            sx={{
              position: 'absolute',
              top: 6,
              left: lastCorrection ? `${Math.min(lastCorrection.position * 8 + 24, 600)}px` : '24px',
              bgcolor: 'rgba(0, 0, 0, 0.7)',
              color: 'white',
              borderRadius: '12px',
              px: 1,
              py: 0.5,
              display: 'flex',
              alignItems: 'center',
              gap: 0.5,
              cursor: 'pointer',
              fontSize: '12px',
              zIndex: 1000,
              boxShadow: 2,
              '&:hover': {
                bgcolor: 'rgba(0, 0, 0, 0.85)',
              },
            }}
          >
            <UndoIcon sx={{ fontSize: 14 }} />
            <Typography variant="caption" sx={{ color: 'white', fontSize: '11px' }}>
              {lastCorrection ? `"${lastCorrection.from}"` : ''}
            </Typography>
          </Box>
        </Fade>

        <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', gap: 1.5, alignItems: 'center' }}>
          <TextField
            ref={textFieldRef}
            fullWidth
            variant="outlined"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask questions or send commands: 'set track 1 volume to -6 dB' or 'how to sidechain in Ableton?'"
            disabled={disabled}
            autoComplete="off"
            inputProps={{
              // Enable native browser spellcheck/autocorrect so users
              // get underlines and OS-level suggestions as a first line
              // of defense, in addition to our DAW-specific autocorrect.
              spellCheck: true,
              autoCorrect: 'on',
              style: { fontSize: '0.9rem' }
            }}
            InputProps={{}}
            sx={{
              '& .MuiOutlinedInput-root': {
                pr: 1 // Reduce right padding to align better with button
              }
            }}
          />
          <IconButton
            type="submit"
            disabled={!input.trim() || disabled}
            size="small"
            sx={{
              color: '#1976d2 !important', // Force blue color
              '&:hover': {
                color: '#1565c0 !important', // Darker blue on hover
                bgcolor: 'rgba(25, 118, 210, 0.04)',
              },
              '&:disabled': {
                color: 'grey.400 !important',
              },
            }}
          >
            <SendIcon sx={{ color: 'inherit' }} />
          </IconButton>
        </Box>
      </Container>
    </Paper>
  );
}
