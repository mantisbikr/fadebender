import * as fs from 'fs';
import * as path from 'path';

export interface RagConfig {
  rag: {
    enabled: boolean;
    version: string;
    environment: string;
    firebase_studio: {
      project_id: string;
      region: string;
      data_sources: {
        paths: {
          ableton_live: string;
          audio_fundamentals: string;
          fadebender: string;
          device_catalog: string;
          preset_catalog: string;
        };
        excluded_paths: string[];
      };
      indexing: {
        auto_reindex: boolean;
        watch_paths: string[];
        embedding_model: string;
        chunk_size: number;
        chunk_overlap: number;
      };
    };
    retrieval: {
      top_k: number;
      min_relevance_score: number;
      rerank: boolean;
      max_context_tokens: number;
    };
    conversation: {
      enabled: boolean;
      max_history_turns: number;
      session_timeout_minutes: number;
      cache_project_analysis: boolean;
      cache_ttl_minutes: number;
    };
    context_injection: {
      enabled: boolean;
      max_context_size_kb: number;
      progressive_loading: boolean;
      default_scope: string;
    };
    cost_optimization: {
      cache_rag_results: boolean;
      cache_ttl_seconds: number;
      use_gemini_flash_for_simple_queries: boolean;
      max_tokens_per_query: number;
    };
  };
}

export interface AppConfig {
  debug: {
    auto_capture: boolean;
    firestore: boolean;
    sse: boolean;
  };
  features: {
    display_only_io: boolean;
    simple_device_resolver: boolean;
    sticky_capabilities_card: boolean;
    use_intents_for_chat: boolean;
  };
  models: {
    audio_analysis: string;
    context_analysis: string;
    default: string;
    help_assistant: string;
    intent_parsing: string;
  };
  nlp: any;
  server: any;
}

let cachedRagConfig: RagConfig | null = null;
let cachedAppConfig: AppConfig | null = null;

/**
 * Load RAG configuration from configs/rag_config.json
 */
export function loadRagConfig(): RagConfig {
  if (cachedRagConfig) {
    return cachedRagConfig;
  }

  // In Cloud Functions, config is in parent directory
  const configPath = path.join(__dirname, '../../configs/rag_config.json');

  if (!fs.existsSync(configPath)) {
    throw new Error(`RAG config not found at ${configPath}`);
  }

  const configData = fs.readFileSync(configPath, 'utf-8');
  cachedRagConfig = JSON.parse(configData) as RagConfig;

  return cachedRagConfig;
}

/**
 * Load App configuration from configs/app_config.json
 */
export function loadAppConfig(): AppConfig {
  if (cachedAppConfig) {
    return cachedAppConfig;
  }

  const configPath = path.join(__dirname, '../../configs/app_config.json');

  if (!fs.existsSync(configPath)) {
    throw new Error(`App config not found at ${configPath}`);
  }

  const configData = fs.readFileSync(configPath, 'utf-8');
  cachedAppConfig = JSON.parse(configData) as AppConfig;

  return cachedAppConfig;
}

/**
 * Get environment-specific config value
 */
export function getConfigValue<T>(path: string, defaultValue?: T): T {
  const config = loadRagConfig();
  const keys = path.split('.');

  let value: any = config;
  for (const key of keys) {
    if (value && typeof value === 'object' && key in value) {
      value = value[key];
    } else {
      if (defaultValue !== undefined) {
        return defaultValue;
      }
      throw new Error(`Config path not found: ${path}`);
    }
  }

  return value as T;
}

/**
 * Check if RAG is enabled
 */
export function isRagEnabled(): boolean {
  try {
    return getConfigValue('rag.enabled', false);
  } catch {
    return false;
  }
}

/**
 * Get model name for a specific purpose from app_config.json
 * @param purpose - 'help_assistant' | 'intent_parsing' | 'audio_analysis' | 'context_analysis' | 'default'
 */
export function getModelName(purpose: keyof AppConfig['models'] = 'default'): string {
  try {
    const appConfig = loadAppConfig();
    return appConfig.models[purpose] || appConfig.models.default;
  } catch (error) {
    // Fallback to sensible default
    console.warn(`Failed to load model config, using fallback: ${error}`);
    return 'gemini-1.5-flash';
  }
}
