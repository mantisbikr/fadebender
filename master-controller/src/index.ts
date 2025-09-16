import { createServer } from 'http';
import { readFileSync } from 'fs';
import { join } from 'path';

const PORT = 8721;

// Load mapping configuration
const mappingPath = join(process.cwd(), '../configs/mapping.json');
const mapping = JSON.parse(readFileSync(mappingPath, 'utf8'));

// Track current state (for relative changes)
const currentState = new Map<string, number>();

// Parameter name mapping to standardize AI output to our mappings
function normalizeParameterName(plugin: string | null, parameter: string, operation?: any): string {
  if (!plugin) {
    const p = (parameter || '').toLowerCase();
    if (p === 'vol' || p === 'volume' || p === 'level') return 'volume';
    if (p === 'pan' || p === 'panning') return 'pan';
    return parameter; // Direct track parameters (volume, pan)
  }

  // Handle EQ parameter variations
  if (plugin.toLowerCase().includes('eq') || plugin === 'Channel EQ') {
    if (parameter === 'gain' || parameter === 'high_gain') return 'high';
    if (parameter === 'mid_gain') return 'mid';
    if (parameter === 'low_gain') return 'low';

    // Handle frequency-based EQ operations
    if (parameter === 'cut' || parameter === 'boost' || parameter === 'gain') {
      // Use frequency to determine which band to target
      const frequency = operation?.frequency;
      if (frequency) {
        if (frequency < 200) return 'low';
        if (frequency < 2000) return 'mid'; // 200Hz-2kHz
        return 'high'; // Above 2kHz
      }
      return 'mid'; // Default to mid if no frequency specified
    }
  }

  // Handle compressor parameter variations
  if (plugin.toLowerCase().includes('compressor')) {
    if (parameter === 'ratio') return 'ratio';
    if (parameter === 'threshold') return 'threshold';
    if (parameter === 'attack') return 'attack';
    if (parameter === 'release') return 'release';
  }

  // Handle reverb parameter variations
  if (plugin.toLowerCase().includes('reverb') || plugin === 'ChromaVerb') {
    if (parameter === 'wet' || parameter === 'wet_level') return 'wet';
    if (parameter === 'dry' || parameter === 'dry_level') return 'dry';
  }

  return parameter;
}

function normalizePluginName(plugin: string | null): string | null {
  if (!plugin) return null;

  // Normalize plugin names
  if (plugin.toLowerCase().includes('eq') || plugin === 'Channel EQ') return 'eq';
  if (plugin.toLowerCase().includes('compressor')) return 'compressor';
  if (plugin.toLowerCase().includes('reverb') || plugin === 'ChromaVerb') return 'reverb';

  return plugin.toLowerCase();
}

function processIntent(intent: any) {
  console.log('Processing intent:', intent.intent);

  if (!intent.targets || intent.targets.length === 0) {
    throw new Error('No targets specified in intent');
  }

  const target = intent.targets[0];
  const operation = intent.operation;

  console.log('Target:', target);
  console.log('Operation:', operation);

  if (!operation) {
    throw new Error('No operation specified in intent');
  }

  // Handle and normalize track field
  if (!target.track) {
    throw new Error('Track not specified - please specify which track to modify');
  }
  // Accept numeric or digit-string and normalize to "Track N"
  if (typeof target.track === 'number' || (/^\d+$/.test(String(target.track)))) {
    target.track = `Track ${Number(target.track)}`;
  } else if (typeof target.track === 'string') {
    const m = String(target.track).match(/^\s*track\s+(\d+)\s*$/i);
    if (m) {
      target.track = `Track ${Number(m[1])}`;
    }
  }

  // Normalize plugin and parameter names
  const normalizedPlugin = normalizePluginName(target.plugin);
  const normalizedParameter = normalizeParameterName(target.plugin, target.parameter, operation);

  // Find mapping for this target
  let trackParam: string;
  if (normalizedPlugin) {
    trackParam = `track${target.track.replace('Track ', '')}.${normalizedPlugin}.${normalizedParameter}`;
  } else {
    trackParam = `track${target.track.replace('Track ', '')}.${normalizedParameter}`;
  }

  console.log('Looking for mapping:', trackParam);

  const mappingEntry = mapping.mappings.find((m: any) => m.alias === trackParam);

  if (!mappingEntry) {
    const aliases: string[] = mapping.mappings.map((m: any) => m.alias);
    console.log('Available mappings:', aliases);
    const trackPrefix = trackParam.split('.').slice(0, 1)[0];
    const suggestions = aliases.filter(a => a.startsWith(trackPrefix + '.'));
    const hint = suggestions.length ? ` Available for this track: ${suggestions.join(', ')}` : '';
    throw new Error(`No mapping found for ${trackParam}.${hint}`);
  }

  console.log('Found mapping:', mappingEntry);

  let finalValue: number;

  if (operation.type === 'relative') {
    // Create unique key for state tracking
    const currentKey = target.plugin ?
      `${target.track}-${target.plugin}-${target.parameter}` :
      `${target.track}-${target.parameter}`;

    // Get current value or use appropriate default based on parameter type
    let defaultValue: number;
    if (operation.unit === '%') {
      defaultValue = 0; // Default to 0% for percentage parameters like reverb
    } else {
      defaultValue = -20; // Default to -20dB for dB parameters
    }

    const currentValue = currentState.get(currentKey) || defaultValue;
    finalValue = currentValue + operation.value;

    // Store new value
    currentState.set(currentKey, finalValue);

    console.log(`Relative change: ${currentValue}${operation.unit} + ${operation.value}${operation.unit} = ${finalValue}${operation.unit}`);
  } else {
    // Absolute value
    finalValue = operation.value;
    const currentKey = target.plugin ?
      `${target.track}-${target.plugin}-${target.parameter}` :
      `${target.track}-${target.parameter}`;
    currentState.set(currentKey, finalValue);
  }

  // Convert dB to MIDI CC value (0-127)
  const { in_min, in_max, out_min, out_max } = mappingEntry.scale;
  const normalizedValue = Math.max(in_min, Math.min(in_max, finalValue));
  const midiValue = Math.round(
    ((normalizedValue - in_min) / (in_max - in_min)) * (out_max - out_min) + out_min
  );

  const targetDescription = target.plugin ?
    `${target.track} ${target.plugin} ${target.parameter}` :
    `${target.track} ${target.parameter}`;

  return {
    op: "emit_cc",
    payload: [{
      cc: mappingEntry.midi.cc,
      channel: mappingEntry.midi.channel,
      value: midiValue,
      target: targetDescription,
      final_value: finalValue,
      unit: operation.unit || 'dB'
    }]
  };
}

const server = createServer((req, res) => {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }

  if (req.method === 'POST' && req.url === '/execute-intent') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const intent = JSON.parse(body);
        console.log('Received intent:', intent);

        // Process intent and generate appropriate bridge message
        const bridgeMessage = processIntent(intent);

        console.log('Generated bridge message:', bridgeMessage);

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: true, bridgeMessage }));
      } catch (error) {
        console.error('Intent processing error:', error);
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: error instanceof Error ? error.message : 'Unknown error' }));
      }
    });
  } else {
    res.writeHead(404);
    res.end('Not Found');
  }
});

server.listen(PORT, () => {
  console.log(`🎛️  Master Controller running on http://localhost:${PORT}`);
  console.log(`📡 Ready to receive intents at POST /execute-intent`);
});

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n🛑 Shutting down Master Controller...');
  server.close(() => process.exit(0));
});
