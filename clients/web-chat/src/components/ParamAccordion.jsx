import { useState, useEffect, useRef } from 'react';
import { Box, Accordion, AccordionSummary, AccordionDetails, Typography, Chip, Button, Tooltip } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import SingleMixerParamEditor from './SingleMixerParamEditor';
import SingleDeviceParamEditor from './SingleDeviceParamEditor';

export default function ParamAccordion({ capabilities, onParamClick, initialGroup = null, initialParam = null }) {
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [expanded, setExpanded] = useState(false);
  const [editingParam, setEditingParam] = useState(null); // {param, group}
  const accordionRef = useRef(null);

  // Detect if this is device or mixer capabilities
  const isDevice = typeof capabilities?.device_index === 'number';
  const isMixer = typeof capabilities?.entity_type === 'string';

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

  // Apply initial group/param focus when provided
  useEffect(() => {
    if (!capabilities) return;
    let applied = false;
    if (initialGroup) {
      const ig = String(initialGroup).toLowerCase();
      let g = allGroups.find(g => String(g.name || '').toLowerCase() === ig);
      if (!g) {
        g = allGroups.find(g => String(g.name || '').toLowerCase().includes(ig));
      }
      if (g) {
        setSelectedGroup(g.name);
        setExpanded(true);
        applied = true;
      }
    }
    if (initialParam) {
      try {
        const ip = String(initialParam).toLowerCase();
        // Find param across groups if needed
        let g = null;
        let p = null;
        const preferredGroup = applied ? String(initialGroup) : (selectedGroup || (allGroups[0] && allGroups[0].name));
        if (preferredGroup) {
          g = allGroups.find(x => x.name === preferredGroup) || null;
          p = (g && g.params || []).find(p => String(p.name || '').toLowerCase() === ip) || null;
        }
        if (!p) {
          for (const gg of allGroups) {
            const cand = (gg.params || []).find(pp => String(pp.name || '').toLowerCase() === ip);
            if (cand) { g = gg; p = cand; break; }
          }
        }
        if (g && p && g.name) {
          setSelectedGroup(g.name);
          setEditingParam(p);
          setExpanded(true);
          return;
        }
      } catch {}
    }
  }, [capabilities, initialGroup, initialParam]);

  // Reset local UI state when capabilities context changes (prevent stale group/expanded state)
  useEffect(() => {
    setSelectedGroup(null);
    setExpanded(false);
    setEditingParam(null);
  }, [capabilities?.device_index, capabilities?.entity_type]);

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

  const handleParamClick = (p) => {
    // Show inline editor
    console.log('[ParamAccordion] Parameter clicked:', {
      param_name: p.name,
      previous_editing: editingParam?.name
    });
    setEditingParam(p);
  };

  const renderParamChip = (p) => {
    const chip = (
      <Chip
        key={`${p.index}-${p.name}`}
        label={p.name}
        onClick={() => handleParamClick(p)}
        variant={editingParam?.name === p.name ? 'filled' : 'outlined'}
        color={editingParam?.name === p.name ? 'primary' : 'default'}
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
            onClick={() => {
              setSelectedGroup(g.name);
              setEditingParam(null); // Clear editor when switching groups
            }}
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
            onChange={(_, isExpanded) => {
              setExpanded(isExpanded);
              if (!isExpanded) {
                setEditingParam(null); // Clear editor when accordion closes
              }
            }}
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

              {/* Inline editor for selected parameter */}
              {editingParam && (() => {
                console.log('[ParamAccordion] Rendering inline editor for:', editingParam.name);

                // For mixer parameters
                if (isMixer) {
                  const values = capabilities.values || {};
                  const currentValue = values[editingParam.name] || {};

                  const editorProps = {
                    entity_type: capabilities.entity_type,
                    index_ref: capabilities.entity_type === 'track'
                      ? capabilities.track_index
                      : (capabilities.entity_type === 'return'
                        ? String.fromCharCode('A'.charCodeAt(0) + (capabilities.return_index || 0))
                        : null),
                    title: editingParam.name,
                    param: {
                      ...editingParam,
                      current_value: currentValue.value,
                      current_display: currentValue.display_value,
                    },
                    send_ref: editingParam.send_letter || null,
                  };

                  console.log('[ParamAccordion] Creating SingleMixerParamEditor with key:', editingParam.name);

                  return (
                    <Box sx={{ mt: 2, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
                      <SingleMixerParamEditor key={editingParam.name} editor={editorProps} />
                    </Box>
                  );
                }

                // For device parameters
                if (isDevice) {
                  const currentValues = capabilities.current_values || {};

                  const editorProps = {
                    return_index: capabilities.return_index,
                    device_index: capabilities.device_index,
                    title: `${editingParam.name} • ${capabilities.device_name || 'Device'}`,
                    param: editingParam,
                    current_values: currentValues,
                  };

                  console.log('[ParamAccordion] Creating SingleDeviceParamEditor with key:', editingParam.name);

                  return (
                    <Box sx={{ mt: 2, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
                      <SingleDeviceParamEditor key={editingParam.name} editor={editorProps} />
                    </Box>
                  );
                }

                return null;
              })()}
            </AccordionDetails>
          </Accordion>
        );
      })()}
    </Box>
  );
}
