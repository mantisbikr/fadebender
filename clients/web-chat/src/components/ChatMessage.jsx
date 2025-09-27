/**
 * ChatMessage Component
 * Displays individual chat messages with different types
 */

import {
  Box,
  Paper,
  Typography,
  Avatar,
  Alert,
  Button,
  Chip
} from '@mui/material';
import {
  Person as PersonIcon,
  SmartToy as BotIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  HelpOutline as QuestionIcon,
  LiveHelp as HelpIcon
} from '@mui/icons-material';
import ClickAwayAccordion from './ClickAwayAccordion.jsx';

export default function ChatMessage({ message, onSuggestedIntent }) {
  const renderHelpResponse = (data) => {
    const answer = data.answer || data.intent?.answer || data.summary || data.content;
    const suggestedIntents = data.suggested_intents || data.intent?.suggested_intents || [];

    return (
      <Box>
        <Typography variant="body1" fontWeight="medium" sx={{ mb: 2 }}>
          {answer}
        </Typography>

        {suggestedIntents.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Try these commands:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {suggestedIntents.map((intent, index) => (
                <Chip
                  key={index}
                  label={intent}
                  onClick={() => onSuggestedIntent?.(intent)}
                  color="primary"
                  variant="outlined"
                  size="small"
                  sx={{
                    cursor: 'pointer',
                    '&:hover': {
                      bgcolor: 'primary.light',
                      color: 'primary.contrastText'
                    }
                  }}
                />
              ))}
            </Box>
          </Box>
        )}
      </Box>
    );
  };

  const getMessageProps = () => {
    switch (message.type) {
      case 'user':
        return {
          ml: 'auto',
          maxWidth: 'sm'
        };
      case 'intent':
        return {
          mr: 'auto',
          maxWidth: 'lg'
        };
      case 'success':
        return {
          mr: 'auto',
          maxWidth: 'lg'
        };
      case 'error':
        return {
          mr: 'auto',
          maxWidth: 'lg'
        };
      case 'info':
        return {
          mr: 'auto',
          maxWidth: 'lg'
        };
      case 'question':
        return {
          mr: 'auto',
          maxWidth: 'lg'
        };
      default:
        return {
          maxWidth: 'lg'
        };
    }
  };

  const getIcon = () => {
    switch (message.type) {
      case 'user':
        return <PersonIcon />;
      case 'intent':
        return <InfoIcon />;
      case 'success':
        return <SuccessIcon />;
      case 'error':
        return <ErrorIcon />;
      case 'info':
        // Help responses route through 'info' with data.answer
        if (message.data && (message.data.answer || message.data.suggested_intents)) {
          return <HelpIcon />;
        }
        return <BotIcon />;
      case 'question':
        return <QuestionIcon />;
      default:
        return <InfoIcon />;
    }
  };

  const getAvatarColor = () => {
    switch (message.type) {
      case 'user':
        return 'primary';
      case 'intent':
        return 'info';
      case 'success':
        return 'success';
      case 'error':
        return 'error';
      case 'info':
        return 'info';
      case 'question':
        return 'secondary';
      default:
        return 'default';
    }
  };

  const formatContent = () => {
    // Canonical intent card
    if (message.type === 'intent' && message.data) {
      const intent = message.data;
      const trackRef = intent?.target?.track;
      const trackLabel = trackRef ? (trackRef.by === 'name' ? String(trackRef.value) : `Track ${trackRef.value}`) : 'Track ?';
      let human = null;
      try {
        if (intent.op === 'set_mixer') {
          const val = intent.value;
          const valStr = val?.type === 'relative'
            ? `${val.amount > 0 ? '+' : ''}${val.amount} ${val.unit || ''}`.trim()
            : `${val.amount} ${val.unit || ''}`.trim();
          human = `${intent.field} • ${trackLabel} • ${val?.type} ${valStr}`;
        } else if (intent.op === 'get_track_status') {
          human = `Get status • ${trackLabel}`;
        } else if (intent.op === 'get_overview') {
          human = 'Get overview';
        }
      } catch {}

      return (
        <Box>
          <Typography variant="body1" fontWeight="medium" gutterBottom>
            {human || 'Canonical Intent'}
          </Typography>
          <ClickAwayAccordion title="View Intent JSON">
            <Box component="pre" sx={{
              fontSize: '0.75rem',
              overflow: 'auto',
              bgcolor: 'action.hover',
              color: 'text.primary',
              p: 1,
              borderRadius: 1,
              fontFamily: 'monospace',
              border: '1px solid',
              borderColor: 'divider'
            }}>
              {JSON.stringify(intent, null, 2)}
            </Box>
            {message.raw && (
              <>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  Raw LLM intent
                </Typography>
                <Box component="pre" sx={{
                  fontSize: '0.75rem',
                  overflow: 'auto',
                  bgcolor: 'action.hover',
                  color: 'text.primary',
                  p: 1,
                  borderRadius: 1,
                  fontFamily: 'monospace',
                  border: '1px solid',
                  borderColor: 'divider'
                }}>
                  {JSON.stringify(message.raw, null, 2)}
                </Box>
              </>
            )}
          </ClickAwayAccordion>
        </Box>
      );
    }

    // Debug: log message structure for help questions
    if (message.content && message.content.toLowerCase().includes('vocal')) {
      console.log('Help question message:', message);
    }

    // Handle success type messages (from /chat endpoint) — show clean summary only
    if (message.type === 'success' && message.data) {
      return (
        <Box>
          <Typography variant="body1" fontWeight="medium" gutterBottom>
            {message.content}
          </Typography>
          {message.data && (
            <ClickAwayAccordion title="View Details">
              <Box component="pre" sx={{
                fontSize: '0.75rem',
                overflow: 'auto',
                bgcolor: 'action.hover',
                color: 'text.primary',
                p: 1,
                borderRadius: 1,
                fontFamily: 'monospace',
                border: '1px solid',
                borderColor: 'divider'
              }}>
                {JSON.stringify(message.data, null, 2)}
              </Box>
            </ClickAwayAccordion>
          )}
        </Box>
      );
    }

    if (message.type === 'question') {
      return (
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <QuestionIcon color="secondary" sx={{ mr: 1 }} />
            <Typography variant="body1" fontWeight="medium" color="secondary.main">
              Clarification Needed
            </Typography>
          </Box>
          <Typography variant="body2" sx={{ mb: 2 }}>
            {message.content}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Please respond with your clarification to continue...
          </Typography>
        </Box>
      );
    }

    // Handle info type messages (from /help endpoint or other sources)
    if (message.type === 'info' && message.data) {
      // Render help responses if present
      if (message.data.answer || message.data.suggested_intents) {
        return renderHelpResponse(message.data);
      }

      // Skip noisy unsupported previews without a clear summary
      if (message.data.reason === 'unsupported_intent_for_auto_execute' && !message.data.summary) {
        return null;
      }

      // Check for fallback indicators
      const isFallback = message.data.meta?.fallback;
      const fallbackReason = message.data.meta?.fallback_reason;
      const confidence = message.data.meta?.confidence;
      return (
        <Box>
          <Box>
            <Typography variant="body1" fontWeight="medium" gutterBottom>
              {message.content}
            </Typography>
            {message.data.summary && (
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {message.data.summary}
              </Typography>
            )}
          </Box>

          {isFallback && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              <Typography variant="body2" fontWeight="medium">
                Fallback Mode
              </Typography>
              <Typography variant="caption">
                {fallbackReason || "AI unavailable - using basic parsing"}
              </Typography>
              {confidence && (
                <Typography variant="caption" display="block">
                  Confidence: {Math.round(confidence * 100)}%
                </Typography>
              )}
            </Alert>
          )}

          <ClickAwayAccordion title="View Details">
            <Box component="pre" sx={{
              fontSize: '0.75rem',
              overflow: 'auto',
              bgcolor: 'action.hover',
              color: 'text.primary',
              p: 1,
              borderRadius: 1,
              fontFamily: 'monospace',
              border: '1px solid',
              borderColor: 'divider'
            }}>
              {JSON.stringify(message.data, null, 2)}
            </Box>
          </ClickAwayAccordion>
        </Box>
      );
    }

    // Handle messages without data or other types (like help questions that come through differently)
    if (message.content) {
      return (
        <Typography variant="body1" fontWeight="medium">
          {message.content}
        </Typography>
      );
    }

    // Fallback for messages with data but no content
    if (message.data && message.data.summary) {
      return (
        <Typography variant="body1" fontWeight="medium">
          {message.data.summary}
        </Typography>
      );
    }

    // Last resort fallback
    return (
      <Typography variant="body2" color="text.secondary">
        No content available
      </Typography>
    );
  };

  const messageProps = getMessageProps();
  const content = formatContent();

  // Don't render anything if content is null (hidden message)
  if (content === null) {
    return null;
  }

  return (
    <Paper
      variant="outlined"
      sx={{
        p: 2,
        mb: 2,
        borderRadius: 2,
        ...messageProps
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
        <Avatar sx={{ bgcolor: `${getAvatarColor()}.main`, width: 32, height: 32 }}>
          {getIcon()}
        </Avatar>
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Box>
            {content}
          </Box>
        </Box>
        <Typography variant="caption" color="text.secondary" sx={{ flexShrink: 0 }}>
          {new Date(message.timestamp).toLocaleTimeString()}
        </Typography>
      </Box>
    </Paper>
  );
}
