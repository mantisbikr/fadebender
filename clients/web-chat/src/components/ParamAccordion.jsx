import { useState, useEffect, useRef } from 'react';
import { Box, Accordion, AccordionSummary, AccordionDetails, Typography, Chip, Button, Tooltip } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

export default function ParamAccordion({ capabilities, onParamClick }) {
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [expanded, setExpanded] = useState(false);
  const accordionRef = useRef(null);

  if (!capabilities) return null;
  const groups = capabilities.groups || [];
  const ungrouped = capabilities.ungrouped || [];
  const deviceName = capabilities.device_name;

  // Create group list including ungrouped if present
  const allGroups = [
    ...groups,
    ...(ungrouped.length > 0 ? [{ name: 'Other', params: ungrouped }] : [])
  ];

  // Select first group by default
  const activeGroup = selectedGroup || (allGroups.length > 0 ? allGroups[0].name : null);

  // Close accordion when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (accordionRef.current && !accordionRef.current.contains(event.target)) {
        setExpanded(false);
      }
    };

    if (expanded) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [expanded]);

  const renderParamChip = (p) => {
    const chip = (
      <Chip
        key={`${p.index}-${p.name}`}
        label={p.name}
        onClick={() => onParamClick && onParamClick(p)}
        variant="outlined"
        size="small"
        sx={{ mr: 1, mb: 1, cursor: 'pointer' }}
      />
    );

    // Wrap in tooltip if we have tooltip text
    if (p.tooltip) {
      return (
        <Tooltip
          key={`${p.index}-${p.name}`}
          title={
            <Box sx={{ whiteSpace: 'pre-line', fontSize: '0.875rem' }}>
              {p.tooltip}
            </Box>
          }
          arrow
          placement="top"
        >
          {chip}
        </Tooltip>
      );
    }

    return chip;
  };

  return (
    <Box sx={{ mt: 2 }}>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        Parameters • {deviceName}
      </Typography>

      {/* Group selector buttons */}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
        {allGroups.map((g) => (
          <Button
            key={g.name}
            variant={activeGroup === g.name ? 'contained' : 'outlined'}
            size="small"
            onClick={() => setSelectedGroup(g.name)}
            sx={{ textTransform: 'none' }}
          >
            {g.name}
          </Button>
        ))}
      </Box>

      {/* Accordion for selected group's parameters */}
      {activeGroup && (() => {
        const group = allGroups.find(g => g.name === activeGroup);
        return (
          <Accordion
            ref={accordionRef}
            expanded={expanded}
            onChange={(_, isExpanded) => setExpanded(isExpanded)}
            disableGutters
            sx={{ boxShadow: 'none', border: '1px solid', borderColor: 'divider' }}
          >
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="body2" fontWeight="medium">{activeGroup}</Typography>
            </AccordionSummary>
            <AccordionDetails>
              {/* Group description and sonic focus */}
              {(group?.description || group?.sonic_focus) && (
                <Box sx={{ mb: 2, p: 1.5, bgcolor: 'action.hover', borderRadius: 1 }}>
                  {group.sonic_focus && (
                    <Typography variant="caption" color="primary" fontWeight="medium" display="block" sx={{ mb: 0.5 }}>
                      {group.sonic_focus}
                    </Typography>
                  )}
                  {group.description && (
                    <Typography variant="body2" color="text.secondary">
                      {group.description}
                    </Typography>
                  )}
                </Box>
              )}

              {/* Parameter chips */}
              <Box sx={{ display: 'flex', flexWrap: 'wrap' }}>
                {(group?.params || []).map(renderParamChip)}
              </Box>
            </AccordionDetails>
          </Accordion>
        );
      })()}
    </Box>
  );
}

