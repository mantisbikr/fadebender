// Minimal MCP server skeleton for Fadebender (TypeScript)
//
// Exposes a single help tool backed by the Cloud Functions
// Studio help endpoint, plus a placeholder for adding more
// tools (intent/parse, snapshot/query, capabilities, etc.).
//
// NOTE: This is a sketch; you will need to:
// - Install the MCP SDK for Node (e.g. @modelcontextprotocol/sdk)
// - Wire this file as the entrypoint for your MCP server binary
// - Configure environment variables for URLs and auth

import fetch from 'node-fetch';

// Adjust imports to match the MCP SDK you use.
// Example (if using @modelcontextprotocol/sdk):
// import { Server } from '@modelcontextprotocol/sdk/server';
// import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio';

type HelpStudioInput = {
  query: string;
  userId?: string;
};

type HelpStudioOutput = {
  response: string;
  model_used: string;
  sources?: Array<{ title: string; snippet: string }>;
  mode: 'rag' | 'fallback';
};

type MixAdviceInput = {
  query: string;
  userId?: string;
};

type MixAdviceOutput = {
  analysis: string;
  recommendations: Array<{
    description: string;
    intent_suggestion?: string;
  }>;
};

type PresetRecommendationsInput = {
  device_type: string;
  goal: string;
  userId?: string;
};

type PresetRecommendationsOutput = {
  recommendations: Array<{
    preset_id: string;
    name: string;
    why: string;
    suggested_commands: string[];
  }>;
};

type DeviceExplainerInput = {
  device_type: string;
  experience_level?: 'beginner' | 'advanced';
};

type DeviceExplainerOutput = {
  summary: string;
  controls: Array<{
    name: string;
    role: string;
    tips?: string;
  }>;
};

type UserProfile = {
  preferred_units?: 'db' | 'percent';
  default_vocal_track?: number;
  default_bass_track?: number;
  safe_max_gain_db?: number;
  genres?: string[];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  [key: string]: any;
};

type GetUserProfileInput = {
  userId: string;
};

type GetUserProfileOutput = {
  userId: string;
  profile: UserProfile;
};

type UpdateUserProfileInput = {
  userId: string;
  profile: UserProfile;
};

type UpdateUserProfileOutput = {
  ok: boolean;
  userId: string;
};

type HealthOutput = {
  server_ok: boolean;
  snapshot_ok: boolean;
  live_connected: boolean | null;
  mode: 'full' | 'explain_only';
};

// Helper to call the Cloud Functions /help endpoint
async function callStudioHelp(input: HelpStudioInput): Promise<HelpStudioOutput> {
  const baseUrl =
    process.env.FADEBENDER_STUDIO_HELP_URL ||
    process.env.FADEBENDER_FUNCTIONS_BASE_URL ||
    'http://localhost:5001/fake-project/us-central1';

  // Expect baseUrl like: https://<region>-<project>.cloudfunctions.net or emulator base
  const endpoint = `${baseUrl.replace(/\/+$/, '')}/help`;

  const res = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query: input.query,
      userId: input.userId,
    }),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(
      `Studio help HTTP ${res.status} ${res.statusText} at ${endpoint}: ${text}`,
    );
  }

  const data = (await res.json()) as any;

  // Map loosely to our output type; Cloud Functions already uses this shape.
  return {
    response: String(data.response ?? data.answer ?? ''),
    model_used: String(data.model_used ?? 'unknown'),
    sources: Array.isArray(data.sources) ? data.sources : [],
    mode: data.mode === 'rag' ? 'rag' : 'fallback',
  };
}

async function callMixAdvice(input: MixAdviceInput): Promise<MixAdviceOutput> {
  const baseUrl =
    process.env.FADEBENDER_FUNCTIONS_BASE_URL ||
    process.env.FADEBENDER_STUDIO_HELP_URL ||
    'http://localhost:5001/fake-project/us-central1';
  const endpoint = `${baseUrl.replace(/\/+$/, '')}/mixAdvice`;

  const res = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`mixAdvice HTTP ${res.status} ${res.statusText}: ${text}`);
  }
  return (await res.json()) as MixAdviceOutput;
}

async function callPresetRecommendations(
  input: PresetRecommendationsInput,
): Promise<PresetRecommendationsOutput> {
  const baseUrl =
    process.env.FADEBENDER_FUNCTIONS_BASE_URL ||
    process.env.FADEBENDER_STUDIO_HELP_URL ||
    'http://localhost:5001/fake-project/us-central1';
  const endpoint = `${baseUrl.replace(/\/+$/, '')}/presetRecommendations`;

  const res = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`presetRecommendations HTTP ${res.status} ${res.statusText}: ${text}`);
  }
  return (await res.json()) as PresetRecommendationsOutput;
}

async function callDeviceExplainer(
  input: DeviceExplainerInput,
): Promise<DeviceExplainerOutput> {
  const baseUrl =
    process.env.FADEBENDER_FUNCTIONS_BASE_URL ||
    process.env.FADEBENDER_STUDIO_HELP_URL ||
    'http://localhost:5001/fake-project/us-central1';
  const endpoint = `${baseUrl.replace(/\/+$/, '')}/deviceExplainer`;

  const res = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`deviceExplainer HTTP ${res.status} ${res.statusText}: ${text}`);
  }
  return (await res.json()) as DeviceExplainerOutput;
}

async function callGetUserProfile(
  input: GetUserProfileInput,
): Promise<GetUserProfileOutput> {
  const baseUrl =
    process.env.FADEBENDER_FUNCTIONS_BASE_URL ||
    process.env.FADEBENDER_STUDIO_HELP_URL ||
    'http://localhost:5001/fake-project/us-central1';
  const endpoint = `${baseUrl.replace(/\/+$/, '')}/getUserProfile`;

  const res = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`getUserProfile HTTP ${res.status} ${res.statusText}: ${text}`);
  }
  return (await res.json()) as GetUserProfileOutput;
}

async function callUpdateUserProfile(
  input: UpdateUserProfileInput,
): Promise<UpdateUserProfileOutput> {
  const baseUrl =
    process.env.FADEBENDER_FUNCTIONS_BASE_URL ||
    process.env.FADEBENDER_STUDIO_HELP_URL ||
    'http://localhost:5001/fake-project/us-central1';
  const endpoint = `${baseUrl.replace(/\/+$/, '')}/updateUserProfile`;

  const res = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`updateUserProfile HTTP ${res.status} ${res.statusText}: ${text}`);
  }
  return (await res.json()) as UpdateUserProfileOutput;
}

async function callHealth(): Promise<HealthOutput> {
  const baseUrl =
    process.env.FADEBENDER_FUNCTIONS_BASE_URL ||
    process.env.FADEBENDER_STUDIO_HELP_URL ||
    'http://localhost:5001/fake-project/us-central1';
  const endpoint = `${baseUrl.replace(/\/+$/, '')}/health`;

  const res = await fetch(endpoint, {
    method: 'GET',
  });

  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`health HTTP ${res.status} ${res.statusText}: ${text}`);
  }
  return (await res.json()) as HealthOutput;
}
// Skeleton registration for MCP tool (pseudo-code; adapt to your MCP SDK)
//
// Example if using an SDK with a "Server" abstraction:
//
// const server = new Server(
//   { name: 'fadebender', version: '0.1.0' },
//   { capabilities: { tools: {} } },
// );
//
// server.tool(
//   'fadebender.help_studio',
//   {
//     description: 'Get audio / Ableton / Fadebender help via Firebase Studio RAG.',
//     inputSchema: {
//       type: 'object',
//       properties: {
//         query: { type: 'string' },
//         userId: { type: 'string', nullable: true },
//       },
//       required: ['query'],
//     },
//     outputSchema: {
//       type: 'object',
//       properties: {
//         response: { type: 'string' },
//         model_used: { type: 'string' },
//         mode: { type: 'string', enum: ['rag', 'fallback'] },
//         sources: {
//           type: 'array',
//           items: {
//             type: 'object',
//             properties: {
//               title: { type: 'string' },
//               snippet: { type: 'string' },
//             },
//             required: ['title', 'snippet'],
//           },
//         },
//       },
//       required: ['response', 'model_used', 'mode'],
//     },
//   },
//   async (args: HelpStudioInput): Promise<HelpStudioOutput> => {
//     return await callStudioHelp(args);
//   },
// );
//
// const transport = new StdioServerTransport();
// server.connect(transport);

export {
  callStudioHelp,
  callMixAdvice,
  callPresetRecommendations,
  callDeviceExplainer,
  callGetUserProfile,
  callUpdateUserProfile,
  callHealth,
  HelpStudioInput,
  HelpStudioOutput,
  MixAdviceInput,
  MixAdviceOutput,
  PresetRecommendationsInput,
  PresetRecommendationsOutput,
  DeviceExplainerInput,
  DeviceExplainerOutput,
  GetUserProfileInput,
  GetUserProfileOutput,
  UpdateUserProfileInput,
  UpdateUserProfileOutput,
  HealthOutput,
};
