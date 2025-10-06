# Fadebender GCP Deployment Architecture

**Generated:** 2025-10-05
**Status:** Draft - Ready for Implementation
**Owner:** Architecture Team

---

## **FILLED JSON CONTEXT**

```json
{
  "project_name": "Fadebender",
  "languages": ["python==3.11", "node==18"],
  "package_managers": ["pip", "npm"],
  "entrypoints": [
    {
      "name": "main-server",
      "path": "server/app.py",
      "framework": "FastAPI",
      "handler": "server.app:app",
      "port_env": "SERVER_PORT (8722 local, 8080 cloud)"
    },
    {
      "name": "nlp-service",
      "path": "nlp-service/main.py",
      "framework": "FastAPI",
      "handler": "main:app",
      "port_env": "PORT (8000 local, 8080 cloud)"
    },
    {
      "name": "web-chat-ui",
      "path": "clients/web-chat",
      "framework": "React (Vite)",
      "handler": "static build",
      "port_env": "3000 (dev only, CDN in prod)"
    },
    {
      "name": "preset-enricher-worker",
      "path": "cloud-workers/preset-enricher/main.py",
      "framework": "Flask (Pub/Sub handler)",
      "handler": "main:app",
      "port_env": "PORT (8080)"
    }
  ],
  "background_work": [
    {
      "name": "preset_metadata_enrichment",
      "est_runtime_sec": 20,
      "peak_mem_mb": 512,
      "concurrency": "low-medium",
      "trigger": "pubsub",
      "idempotent": true
    }
  ],
  "batch_jobs": [],
  "native_deps": ["none (pure Python/JS)"],
  "python_deps": [
    "fastapi",
    "uvicorn",
    "pydantic",
    "google-cloud-aiplatform",
    "google-cloud-firestore",
    "google-cloud-pubsub",
    "google-cloud-storage",
    "google-generativeai",
    "Flask (worker)",
    "gunicorn"
  ],
  "assets_files": {
    "max_upload_mb": 10,
    "avg_upload_mb": 3,
    "daily_volume_gb": 1
  },
  "data_stores": [
    {
      "use_case": "presets_metadata",
      "type": "Firestore",
      "tx_rate_rps": 5,
      "multiregion_needed": false
    },
    {
      "use_case": "learned_device_mappings",
      "type": "Firestore",
      "tx_rate_rps": 2,
      "multiregion_needed": false
    },
    {
      "use_case": "knowledge_base_files",
      "type": "Cloud Storage",
      "tx_rate_rps": 1,
      "multiregion_needed": false
    }
  ],
  "caches": [
    {
      "type": "in-memory",
      "location": "in-service (Python dicts)"
    }
  ],
  "auth_model": {
    "users": "internal/desktop-app-users",
    "auth": "none-yet (TODO: Identity Platform for multi-user)",
    "roles": []
  },
  "external_apis": [
    {
      "name": "Vertex AI Gemini / Generative AI",
      "egress_per_request_mb": 0.05
    }
  ],
  "slo_sli": {
    "latency_ms_p50_p95": [100, 400],
    "availability": "99.5%",
    "cold_start_tolerance": "ok"
  },
  "traffic_profile": {
    "regions_users": ["us-heavy"],
    "baseline_rps": 1,
    "p95_rps_peaks": 10,
    "daily_active_users": 50
  },
  "security": {
    "secrets": [
      "VERTEX_PROJECT",
      "GOOGLE_APPLICATION_CREDENTIALS_JSON",
      "LLM_API_KEY (fallback)",
      "PUBSUB_TOPIC"
    ],
    "pii": false,
    "compliance": "none"
  },
  "networking": {
    "needs_vpc": false,
    "egress_to": ["Vertex AI", "Generative AI API", "GitHub (CI/CD)"],
    "private_sql": false
  },
  "ci_cd": "Cloud Build",
  "observability": {
    "log_verbosity": "info",
    "tracing": true,
    "error_reporting": true
  },
  "budget_caps": {
    "target_monthly_usd": 50,
    "hard_ceiling_usd": 150
  }
}
```

---

## **1) SUMMARY**

- **Fadebender** is an AI-powered Ableton Live controller with natural language processing for audio mixing operations.
- **Current architecture**: Local dev with 3 Python FastAPI services (main server, NLP service, preset enricher worker), 1 React UI, UDP bridge to Ableton Live.
- **Key dependencies**: Google Cloud (Vertex AI Gemini, Firestore, Pub/Sub, Cloud Storage), FastAPI, React with MUI.
- **Data flow**: User commands → NLP service (LLM intent parsing) → Server → Ableton UDP bridge; Preset capture → Pub/Sub → Cloud worker → Firestore + LLM metadata generation.
- **Current cloud usage**: Already using Firestore (presets, mappings), Cloud Storage (knowledge base), Pub/Sub (preset enrichment queue), Vertex AI (LLM).
- **Production gap**: All services run locally; need Cloud Run deployment, CDN for static assets, proper secrets management, observability, CI/CD.
- **Traffic**: Low volume (single-user desktop app currently, ~1-10 RPS), high latency tolerance (interactive audio mixing UI), no strict SLAs.
- **Cost drivers**: Vertex AI API calls (main), Cloud Run compute (minimal at low traffic), Firestore reads/writes (low).
- **Security**: Service-account based auth already in use; no end-user auth yet (desktop app model); secrets stored in local `.env` files.
- **Observability**: Console logging only; need structured logs, error reporting, metrics, traces.

---

## **2) GCP ARCHITECTURE (Cloud Run–first)**

### **ASCII Diagram**

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         FADEBENDER GCP ARCHITECTURE                        │
└───────────────────────────────────────────────────────────────────────────┘

┌──────────────┐
│  Desktop App │  (Ableton Live + local UDP bridge – stays local)
│  (local)     │
└──────┬───────┘
       │ HTTPS API calls
       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        Cloud CDN + Load Balancer                          │
│                         (Static assets + API routing)                     │
└──────────────┬────────────────────────────────┬───────────────────────────┘
               │                                │
      /api/*   │                                │  / (static)
               ▼                                ▼
    ┌─────────────────────┐          ┌─────────────────────┐
    │   Cloud Run Service │          │   Cloud Storage     │
    │   "fadebender-api"  │          │   Bucket (static)   │
    │   (server/app.py)   │          │   + lifecycle rules │
    └─────────┬───────────┘          └─────────────────────┘
              │
              ├───────► ┌──────────────────────┐
              │         │  Cloud Run Service   │
              │         │  "nlp-service"       │
              │         │  (NLP intent parser) │
              │         └──────────────────────┘
              │
              ├───────► ┌──────────────────────────────────┐
              │         │       Firestore (Native)         │
              │         │  Collections: presets, mappings  │
              │         └──────────────────────────────────┘
              │
              ├───────► ┌──────────────────────────────────┐
              │         │     Cloud Storage (GCS)          │
              │         │  Bucket: fadebender-kb (docs)    │
              │         └──────────────────────────────────┘
              │
              └───────► ┌──────────────────────────────────┐
                        │       Pub/Sub Topic              │
                        │    "preset-enrich"               │
                        └────────────┬─────────────────────┘
                                     │ push subscription
                                     ▼
                        ┌──────────────────────────────────┐
                        │    Cloud Run Service             │
                        │  "preset-enricher-worker"        │
                        │  (async metadata generation)     │
                        └────────────┬─────────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    ▼                ▼                ▼
            ┌───────────────┐ ┌────────────┐ ┌────────────────┐
            │  Vertex AI    │ │ Firestore  │ │ Cloud Storage  │
            │  Gemini API   │ │  (update)  │ │   (read KB)    │
            └───────────────┘ └────────────┘ └────────────────┘

                    ┌──────────────────────────────────┐
                    │      Secret Manager              │
                    │  Secrets: VERTEX_PROJECT,        │
                    │  SERVICE_ACCOUNT_KEY, API_KEYS   │
                    └──────────────────────────────────┘

                    ┌──────────────────────────────────┐
                    │   Cloud Logging + Monitoring     │
                    │   Error Reporting + Trace        │
                    └──────────────────────────────────┘

                    ┌──────────────────────────────────┐
                    │       Cloud Build (CI/CD)        │
                    │  Triggers on main branch push    │
                    └──────────────────────────────────┘
```

### **Service Selection Rationale**

| **Component** | **Chosen Service** | **Why (vs alternatives)** |
|---------------|-------------------|---------------------------|
| **Main API** | Cloud Run (`fadebender-api`) | FastAPI already containerized; low traffic fits pay-per-request; autoscale 0→N; vs App Engine (less control), GKE (overkill for <10 RPS) |
| **NLP Service** | Cloud Run (`nlp-service`) | Same as main API; service-to-service calls via internal URLs; stateless LLM intent parsing |
| **Frontend** | Cloud Storage + Cloud CDN | React SPA (static build); CDN for global latency; vs Cloud Run (unnecessary compute for static files), Firebase Hosting (vendor lock-in) |
| **Async Worker** | Cloud Run (Pub/Sub push) | Already exists as Flask app; <30s runtime fits Cloud Run; vs Cloud Functions (no benefit), Cloud Run Jobs (not event-driven) |
| **Database** | Firestore (Native mode) | Already in use; JSON documents (presets, mappings); low write volume; vs Cloud SQL (no relational needs, higher cost at low scale) |
| **File Storage** | Cloud Storage | Knowledge base markdown files; presigned URLs for uploads; lifecycle rules for cleanup |
| **Queue** | Pub/Sub | Async preset enrichment; at-least-once delivery; push to Cloud Run worker |
| **LLM** | Vertex AI Gemini (primary), Generative AI API (fallback) | Already integrated; keep existing logic |
| **Secrets** | Secret Manager | Service account keys, API keys; mounted as env vars in Cloud Run |
| **CDN/LB** | Cloud CDN + External HTTPS LB | Single entry point; static assets cached; API requests proxied to Cloud Run |
| **Auth** | None initially; Identity Platform (future) | Desktop app today; add for multi-user web version |

### **Regions & Latency Plan**

- **Start**: `us-central1` (Iowa) – low cost, good US latency, Vertex AI availability
- **Multi-region path**:
  - Phase 1: Single region (`us-central1`)
  - Phase 2: Add Cloud CDN (global edge caching for static assets)
  - Phase 3: Deploy Cloud Run services to `us-east1`, `europe-west1` if user base grows; use Traffic Manager
  - Firestore: Start single-region (`us-central1`), upgrade to multi-region (`nam5`) if needed
- **CDN coverage**: Automatic global edge locations via Cloud CDN

### **Scaling Knobs**

| **Service** | **Concurrency** | **Min Instances** | **Max Instances** | **CPU** | **RAM** | **Timeout** |
|-------------|----------------|-------------------|-------------------|---------|---------|-------------|
| `fadebender-api` | 40 | 0 | 10 | 1 vCPU | 512 MB | 300s |
| `nlp-service` | 20 | 0 | 5 | 1 vCPU | 512 MB | 60s |
| `preset-enricher-worker` | 1 | 0 | 10 | 1 vCPU | 1 GB | 540s |
| Static assets (CDN) | N/A | N/A | N/A | N/A | N/A | N/A |

**Rationale**:
- **Low min instances (0)**: Pay only for actual usage; cold starts acceptable for desktop app use case
- **Low max instances**: Traffic cap prevents runaway costs
- **Concurrency**: Higher for API (stateless), lower for NLP (LLM calls), 1 for worker (long-running tasks)
- **Memory**: 512 MB for lightweight FastAPI services; 1 GB for worker (LLM context)
- **Timeout**: 5 min for API (safe), 1 min for NLP (LLM latency), 9 min for worker (metadata generation)

---

## **3) DEPLOYABLE ARTIFACTS**

### **A) Dockerfiles**

#### **`server/Dockerfile` (main API)**

```dockerfile
FROM python:3.11-slim

# Non-root user for security
RUN useradd -m -u 1000 appuser
WORKDIR /app

# Copy dependencies first (layer caching)
COPY server/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY server ./server
COPY shared ./shared

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=3)"

# Switch to non-root
USER appuser

# Cloud Run expects PORT env var
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Use uvicorn for FastAPI (ASGI)
CMD exec uvicorn server.app:app --host 0.0.0.0 --port $PORT --workers 1 --log-level info
```

#### **`nlp-service/Dockerfile`**

```dockerfile
FROM python:3.11-slim

RUN useradd -m -u 1000 appuser
WORKDIR /app

COPY nlp-service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY nlp-service ./nlp-service
COPY shared ./shared

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=3)"

USER appuser

ENV PORT=8080
ENV PYTHONUNBUFFERED=1

CMD exec uvicorn nlp-service.main:app --host 0.0.0.0 --port $PORT --workers 1 --log-level info
```

#### **`cloud-workers/preset-enricher/Dockerfile`** (already exists, enhance)

```dockerfile
FROM python:3.11-slim

RUN useradd -m -u 1000 appuser
WORKDIR /app

COPY cloud-workers/preset-enricher/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY cloud-workers/preset-enricher/main.py ./main.py
COPY cloud-workers/preset-enricher/shared ./shared

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=3)" || true

USER appuser

ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Flask with gunicorn (Pub/Sub handler)
CMD exec gunicorn --bind :$PORT --workers 1 --threads 4 --timeout 540 main:app
```

---

### **B) `cloudbuild.yaml` (CI/CD)**

```yaml
steps:
  # Build main API
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'gcr.io/$PROJECT_ID/fadebender-api:$COMMIT_SHA'
      - '-t'
      - 'gcr.io/$PROJECT_ID/fadebender-api:latest'
      - '-f'
      - 'server/Dockerfile'
      - '.'

  # Build NLP service
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'gcr.io/$PROJECT_ID/nlp-service:$COMMIT_SHA'
      - '-t'
      - 'gcr.io/$PROJECT_ID/nlp-service:latest'
      - '-f'
      - 'nlp-service/Dockerfile'
      - '.'

  # Build preset enricher worker
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'gcr.io/$PROJECT_ID/preset-enricher-worker:$COMMIT_SHA'
      - '-t'
      - 'gcr.io/$PROJECT_ID/preset-enricher-worker:latest'
      - '-f'
      - 'cloud-workers/preset-enricher/Dockerfile'
      - '.'

  # Push images
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/fadebender-api:$COMMIT_SHA']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/fadebender-api:latest']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/nlp-service:$COMMIT_SHA']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/nlp-service:latest']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/preset-enricher-worker:$COMMIT_SHA']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/preset-enricher-worker:latest']

  # Deploy main API to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'fadebender-api'
      - '--image=gcr.io/$PROJECT_ID/fadebender-api:$COMMIT_SHA'
      - '--region=us-central1'
      - '--platform=managed'
      - '--allow-unauthenticated'
      - '--concurrency=40'
      - '--cpu=1'
      - '--memory=512Mi'
      - '--timeout=300'
      - '--min-instances=0'
      - '--max-instances=10'
      - '--set-env-vars=VERTEX_PROJECT=$PROJECT_ID,VERTEX_LOCATION=us-central1,FIRESTORE_PROJECT_ID=$PROJECT_ID,PUBSUB_TOPIC=preset-enrich'
      - '--set-secrets=GOOGLE_APPLICATION_CREDENTIALS=fadebender-sa-key:latest,LLM_API_KEY=llm-api-key:latest'

  # Deploy NLP service
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'nlp-service'
      - '--image=gcr.io/$PROJECT_ID/nlp-service:$COMMIT_SHA'
      - '--region=us-central1'
      - '--platform=managed'
      - '--no-allow-unauthenticated'
      - '--concurrency=20'
      - '--cpu=1'
      - '--memory=512Mi'
      - '--timeout=60'
      - '--min-instances=0'
      - '--max-instances=5'
      - '--set-env-vars=VERTEX_PROJECT=$PROJECT_ID,VERTEX_LOCATION=us-central1'
      - '--set-secrets=GOOGLE_APPLICATION_CREDENTIALS=fadebender-sa-key:latest,LLM_API_KEY=llm-api-key:latest'

  # Deploy preset enricher worker
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'preset-enricher-worker'
      - '--image=gcr.io/$PROJECT_ID/preset-enricher-worker:$COMMIT_SHA'
      - '--region=us-central1'
      - '--platform=managed'
      - '--no-allow-unauthenticated'
      - '--concurrency=1'
      - '--cpu=1'
      - '--memory=1Gi'
      - '--timeout=540'
      - '--min-instances=0'
      - '--max-instances=10'
      - '--set-env-vars=VERTEX_PROJECT=$PROJECT_ID,VERTEX_LOCATION=us-central1,FIRESTORE_PROJECT_ID=$PROJECT_ID,KB_BUCKET=fadebender-kb'
      - '--set-secrets=GOOGLE_APPLICATION_CREDENTIALS=fadebender-sa-key:latest,LLM_API_KEY=llm-api-key:latest'

  # Build and deploy static frontend
  - name: 'node:18'
    dir: 'clients/web-chat'
    entrypoint: 'sh'
    args:
      - '-c'
      - |
        npm install
        npm run build
        gsutil -m rsync -r -d dist gs://fadebender-static/

timeout: 1200s
options:
  machineType: 'N1_HIGHCPU_8'
```

---

### **C) Terraform Skeleton**

#### **`terraform/main.tf`**

```hcl
terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  backend "gcs" {
    bucket = "fadebender-terraform-state"
    prefix = "prod/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "firestore.googleapis.com",
    "pubsub.googleapis.com",
    "storage.googleapis.com",
    "aiplatform.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "cloudtrace.googleapis.com",
    "compute.googleapis.com"
  ])
  service            = each.value
  disable_on_destroy = false
}

# Firestore (Native mode)
resource "google_firestore_database" "default" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
}

# Cloud Storage buckets
resource "google_storage_bucket" "static_assets" {
  name          = "${var.project_id}-static"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  website {
    main_page_suffix = "index.html"
    not_found_page   = "index.html"
  }

  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD"]
    response_header = ["*"]
    max_age_seconds = 3600
  }
}

resource "google_storage_bucket" "knowledge_base" {
  name          = "${var.project_id}-kb"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type = "Delete"
    }
  }
}

# Make static bucket public
resource "google_storage_bucket_iam_member" "public_read" {
  bucket = google_storage_bucket.static_assets.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}

# Pub/Sub topic for preset enrichment
resource "google_pubsub_topic" "preset_enrich" {
  name = "preset-enrich"
}

# Service account for Cloud Run services
resource "google_service_account" "cloud_run" {
  account_id   = "fadebender-run-sa"
  display_name = "Fadebender Cloud Run Service Account"
}

# IAM roles for service account
resource "google_project_iam_member" "sa_roles" {
  for_each = toset([
    "roles/firestore.user",
    "roles/storage.objectViewer",
    "roles/storage.objectCreator",
    "roles/pubsub.publisher",
    "roles/aiplatform.user",
    "roles/secretmanager.secretAccessor",
    "roles/logging.logWriter",
    "roles/cloudtrace.agent"
  ])
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

# Secrets
resource "google_secret_manager_secret" "sa_key" {
  secret_id = "fadebender-sa-key"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "llm_api_key" {
  secret_id = "llm-api-key"

  replication {
    auto {}
  }
}

# Grant Cloud Run SA access to secrets
resource "google_secret_manager_secret_iam_member" "sa_key_access" {
  secret_id = google_secret_manager_secret.sa_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run.email}"
}

resource "google_secret_manager_secret_iam_member" "llm_key_access" {
  secret_id = google_secret_manager_secret.llm_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run.email}"
}

# Cloud Run services (placeholder - managed via cloudbuild.yaml)
# Actual deployments via `gcloud run deploy` in CI/CD

# Cloud Build trigger
resource "google_cloudbuild_trigger" "main_branch" {
  name        = "deploy-main"
  description = "Deploy on main branch push"

  github {
    owner = var.github_owner
    name  = var.github_repo
    push {
      branch = "^main$"
    }
  }

  filename = "cloudbuild.yaml"

  service_account = google_service_account.cloud_build.id
}

resource "google_service_account" "cloud_build" {
  account_id   = "fadebender-build-sa"
  display_name = "Fadebender Cloud Build Service Account"
}

resource "google_project_iam_member" "build_sa_roles" {
  for_each = toset([
    "roles/run.admin",
    "roles/storage.admin",
    "roles/iam.serviceAccountUser"
  ])
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.cloud_build.email}"
}

# Monitoring: Budget alert
resource "google_billing_budget" "monthly_budget" {
  billing_account = var.billing_account_id
  display_name    = "Fadebender Monthly Budget"

  amount {
    specified_amount {
      currency_code = "USD"
      units         = var.monthly_budget_usd
    }
  }

  threshold_rules {
    threshold_percent = 0.7
  }

  threshold_rules {
    threshold_percent = 0.9
  }

  threshold_rules {
    threshold_percent = 1.0
  }

  all_updates_rule {
    pubsub_topic = google_pubsub_topic.budget_alerts.id
  }
}

resource "google_pubsub_topic" "budget_alerts" {
  name = "budget-alerts"
}

# Alert policy for high latency
resource "google_monitoring_alert_policy" "high_latency" {
  display_name = "Cloud Run High Latency (p95 > 1s)"
  combiner     = "OR"

  conditions {
    display_name = "High request latency"

    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND metric.type = \"run.googleapis.com/request_latencies\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 1000

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_DELTA"
        cross_series_reducer = "REDUCE_PERCENTILE_95"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.id]
}

resource "google_monitoring_notification_channel" "email" {
  display_name = "Email Alerts"
  type         = "email"

  labels = {
    email_address = var.alert_email
  }
}

# Output URLs
output "api_url" {
  value       = "https://fadebender-api-<hash>-uc.a.run.app"
  description = "Main API URL (replace <hash> after deploy)"
}

output "static_bucket" {
  value       = google_storage_bucket.static_assets.url
  description = "Static assets bucket"
}
```

#### **`terraform/variables.tf`**

```hcl
variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "fadebender"
}

variable "region" {
  description = "Primary GCP region"
  type        = string
  default     = "us-central1"
}

variable "github_owner" {
  description = "GitHub repository owner"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
  default     = "fadebender"
}

variable "billing_account_id" {
  description = "GCP Billing Account ID"
  type        = string
}

variable "monthly_budget_usd" {
  description = "Monthly budget in USD"
  type        = number
  default     = 50
}

variable "alert_email" {
  description = "Email for alerts"
  type        = string
}
```

---

### **D) gcloud One-Liners**

```bash
# Set project
gcloud config set project fadebender

# Enable APIs
gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
  firestore.googleapis.com pubsub.googleapis.com storage.googleapis.com \
  aiplatform.googleapis.com secretmanager.googleapis.com

# Create Firestore database
gcloud firestore databases create --region=us-central1

# Create Pub/Sub topic
gcloud pubsub topics create preset-enrich

# Create Cloud Storage buckets
gsutil mb -l us-central1 gs://fadebender-static
gsutil mb -l us-central1 gs://fadebender-kb

# Build & deploy main API (manual)
gcloud builds submit --tag gcr.io/fadebender/fadebender-api:latest -f server/Dockerfile .
gcloud run deploy fadebender-api \
  --image gcr.io/fadebender/fadebender-api:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --concurrency 40 \
  --cpu 1 \
  --memory 512Mi \
  --timeout 300 \
  --min-instances 0 \
  --max-instances 10 \
  --set-env-vars VERTEX_PROJECT=fadebender,VERTEX_LOCATION=us-central1 \
  --set-secrets GOOGLE_APPLICATION_CREDENTIALS=fadebender-sa-key:latest

# Deploy NLP service
gcloud builds submit --tag gcr.io/fadebender/nlp-service:latest -f nlp-service/Dockerfile .
gcloud run deploy nlp-service \
  --image gcr.io/fadebender/nlp-service:latest \
  --region us-central1 \
  --platform managed \
  --no-allow-unauthenticated \
  --concurrency 20 \
  --cpu 1 \
  --memory 512Mi \
  --timeout 60 \
  --min-instances 0 \
  --max-instances 5

# Deploy preset enricher worker
gcloud builds submit --tag gcr.io/fadebender/preset-enricher-worker:latest -f cloud-workers/preset-enricher/Dockerfile .
gcloud run deploy preset-enricher-worker \
  --image gcr.io/fadebender/preset-enricher-worker:latest \
  --region us-central1 \
  --platform managed \
  --no-allow-unauthenticated \
  --concurrency 1 \
  --cpu 1 \
  --memory 1Gi \
  --timeout 540

# Create Pub/Sub push subscription to worker
gcloud pubsub subscriptions create preset-enrich-sub \
  --topic preset-enrich \
  --push-endpoint https://preset-enricher-worker-<hash>-uc.a.run.app \
  --push-auth-service-account fadebender-run-sa@fadebender.iam.gserviceaccount.com

# Build & deploy static frontend
cd clients/web-chat && npm install && npm run build
gsutil -m rsync -r -d dist gs://fadebender-static/

# Make bucket public
gsutil iam ch allUsers:objectViewer gs://fadebender-static
```

---

### **E) Secret Manager Setup**

```bash
# Create secrets (one-time)
echo -n '{"type":"service_account",...}' | \
  gcloud secrets create fadebender-sa-key --data-file=-

echo -n 'YOUR_LLM_API_KEY' | \
  gcloud secrets create llm-api-key --data-file=-

# Grant Cloud Run SA access
gcloud secrets add-iam-policy-binding fadebender-sa-key \
  --member serviceAccount:fadebender-run-sa@fadebender.iam.gserviceaccount.com \
  --role roles/secretmanager.secretAccessor

gcloud secrets add-iam-policy-binding llm-api-key \
  --member serviceAccount:fadebender-run-sa@fadebender.iam.gserviceaccount.com \
  --role roles/secretmanager.secretAccessor
```

---

## **4) SECURITY & IAM**

### **Service Accounts**

| **Service Account** | **Purpose** | **IAM Roles** |
|---------------------|-------------|---------------|
| `fadebender-run-sa` | Runtime for Cloud Run services | `roles/firestore.user`, `roles/storage.objectViewer`, `roles/storage.objectCreator`, `roles/pubsub.publisher`, `roles/aiplatform.user`, `roles/secretmanager.secretAccessor`, `roles/logging.logWriter`, `roles/cloudtrace.agent` |
| `fadebender-build-sa` | Cloud Build deployments | `roles/run.admin`, `roles/storage.admin`, `roles/iam.serviceAccountUser` |
| `<user>@fadebender.iam.gserviceaccount.com` | Local dev (existing) | Owner (dev only, revoke in prod) |

### **Least-Privilege IAM**

- **Cloud Run services**: Run as `fadebender-run-sa` with minimal roles
- **Firestore**: Read/write only to `presets` and `mappings` collections
- **Cloud Storage**: Read from `fadebender-kb`, write to `fadebender-static` (frontend build)
- **Pub/Sub**: Publish to `preset-enrich` topic; worker authenticated via push subscription with service account
- **Secret Manager**: Read-only access to secrets at runtime (no write)
- **Vertex AI**: User role for API calls (no training/tuning)

### **Ingress/Egress Controls**

- **Main API (`fadebender-api`)**: `--allow-unauthenticated` (public, HTTPS only)
- **NLP service**: `--no-allow-unauthenticated` (internal only, called via service-to-service auth)
- **Worker**: `--no-allow-unauthenticated` (Pub/Sub push only)
- **Egress**: No VPC needed; default internet egress for Vertex AI, Generative AI API

### **Service-to-Service Auth**

```python
# In fadebender-api calling nlp-service
import google.auth.transport.requests
import google.oauth2.id_token

def call_nlp_service(prompt: str):
    nlp_url = os.getenv("NLP_SERVICE_URL")  # Internal Cloud Run URL
    auth_req = google.auth.transport.requests.Request()
    id_token = google.oauth2.id_token.fetch_id_token(auth_req, nlp_url)

    headers = {"Authorization": f"Bearer {id_token}"}
    response = requests.post(f"{nlp_url}/parse", json={"prompt": prompt}, headers=headers)
    return response.json()
```

### **Secrets Handling (12-Factor)**

- All secrets in Secret Manager, mounted as env vars: `--set-secrets KEY=secret-name:latest`
- No secrets in Docker images, source code, or logs
- Rotate secrets annually; use versioning in Secret Manager

---

## **5) OBSERVABILITY & OPS**

### **Logging (Structured JSON)**

```python
# Add to FastAPI apps
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": self.formatTime(record),
            "severity": record.levelname,
            "message": record.getMessage(),
            "service": os.getenv("K_SERVICE", "local"),
            "trace": getattr(record, "trace", None),
        }
        return json.dumps(log_obj)

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.root.addHandler(handler)
logging.root.setLevel(logging.INFO)
```

### **Metrics & Tracing**

- **Built-in Cloud Run metrics**: Request count, latency (p50/p95/p99), CPU/memory usage, instance count
- **Custom metrics**: Use OpenTelemetry SDK to export to Cloud Monitoring
- **Tracing**: Enable Cloud Trace via `google-cloud-trace` library; automatic for HTTP requests

### **Error Reporting**

```python
# Add to FastAPI exception handlers
from google.cloud import error_reporting

error_client = error_reporting.Client()

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    error_client.report_exception()
    logging.exception("Unhandled exception")
    return JSONResponse(status_code=500, content={"error": "Internal server error"})
```

### **SLO & Alert Policies**

| **SLI** | **SLO** | **Alert Threshold** | **Policy** |
|---------|---------|---------------------|------------|
| Availability | 99.5% uptime | <99% over 1h | Alert if error rate >1% for 5 min |
| Latency (p95) | <600ms | >1s for 5 min | Alert if p95 latency >1s sustained |
| Error rate | <1% | >5% for 5 min | Immediate page |
| Budget burn | <$50/month | >70% of budget | Email at 70%, 90%, 100% |

### **Rollout Strategy**

- **Canary deployments**: Use Cloud Run traffic splitting
  ```bash
  # Deploy new revision without traffic
  gcloud run deploy fadebender-api --image ... --no-traffic --tag canary

  # Split 10% traffic to canary
  gcloud run services update-traffic fadebender-api --to-revisions canary=10,LATEST=90

  # Promote if healthy
  gcloud run services update-traffic fadebender-api --to-latest
  ```
- **Blue-green**: Deploy to new revision, switch 100% traffic atomically
- **Rollback**: `gcloud run services update-traffic fadebender-api --to-revisions PREVIOUS=100`

### **Backup & Retention**

- **Firestore**: Automatic daily backups (managed by Google); export to GCS monthly via Cloud Scheduler + Cloud Functions
- **Cloud Storage**: Versioning enabled; lifecycle rules to delete old versions after 90 days
- **Logs**: Retained 30 days by default; export to BigQuery for long-term analysis

---

## **6) COST MODEL (Rough Monthly Estimate)**

Assumptions:
- **Traffic**: 50 DAU, 1-10 RPS baseline, 5,000 requests/day
- **Preset enrichments**: 10/day = 300/month
- **Knowledge base**: 100 MB, 1,000 reads/month
- **LLM calls**: 5,000 prompts/month (main API + NLP), avg 500 input tokens, 200 output tokens

| **Component** | **Usage** | **Unit Cost** | **Monthly Cost** |
|---------------|-----------|---------------|------------------|
| **Cloud Run (API)** | 5,000 req × 100ms × 512MB | $0.00002/vCPU-sec, $0.0000025/GB-sec | ~$1 |
| **Cloud Run (NLP)** | 5,000 req × 200ms × 512MB | Same | ~$2 |
| **Cloud Run (Worker)** | 300 req × 20s × 1GB | Same | ~$3 |
| **Firestore** | 10,000 reads, 1,000 writes, 1 GB | $0.06/100k reads, $0.18/100k writes, $0.18/GB | ~$2 |
| **Cloud Storage** | 100 MB, 1,000 reads, 100 writes | $0.02/GB, $0.004/10k Class A ops | <$1 |
| **Pub/Sub** | 300 messages/month | $40/TB (negligible) | <$1 |
| **Vertex AI Gemini** | 5,000 prompts × 700 tokens avg | $0.075/1M input tokens (Flash) | ~$3 |
| **Cloud CDN** | 10 GB egress, 50,000 requests | $0.08/GB (US), $0.0075/10k requests | ~$1 |
| **Cloud Build** | 5 builds/month × 10 min | 120 min free/day | $0 |
| **Logging** | 5 GB/month | 50 GB free | $0 |
| **Monitoring** | <25 metrics | Free tier | $0 |
| **Secret Manager** | 2 secrets, 10,000 accesses | $0.06/secret/month, $0.03/10k accesses | <$1 |
| **Network egress** | 2 GB (API responses) | $0.12/GB (Americas) | <$1 |
| **TOTAL** | | | **~$15-20/month** |

### **Cost Reduction Levers**

1. **Minimize cold starts**: Set `min-instances=1` for API during peak hours (adds ~$5/month)
2. **Batch LLM calls**: Reduce Vertex AI usage by caching/deduplicating prompts
3. **Optimize images**: Use distroless Python base images to reduce startup time
4. **Use committed use discounts**: 37% off Cloud Run if traffic grows
5. **Enable Cloud CDN caching**: Reduce Cloud Run hits for static assets (already in plan)

---

## **7) OPEN QUESTIONS / TODOs**

### **Blocking Deployment**

1. **GitHub repository owner/name**: Required for Cloud Build trigger (fill in `terraform/variables.tf`)
2. **Billing account ID**: Required for budget alerts (`terraform/variables.tf`)
3. **Alert email**: Required for monitoring notifications (`terraform/variables.tf`)
4. **Service account key**: Need to generate and upload to Secret Manager (see Section 3E)
5. **LLM API key (fallback)**: If using Generative AI API fallback, upload to Secret Manager

### **Non-Blocking (Can Deploy Without)**

1. **Multi-user auth**: Desktop app doesn't need it yet; add Identity Platform when building web multi-user version
2. **Custom domain**: Use Cloud Run default URLs (`*.run.app`) initially; map custom domain via Cloud Load Balancer later
3. **Health check endpoints**: Add `/health` endpoints to all services (currently missing; returns 200 OK)
4. **Graceful shutdown**: FastAPI/Flask handle SIGTERM gracefully by default; verify in testing
5. **Database migrations**: Firestore is schemaless; no migrations needed (add if switching to Cloud SQL)
6. **Rate limiting**: Not critical at low traffic; add Cloud Armor rules if opening to public
7. **DDoS protection**: Cloud Run has built-in; upgrade to Cloud Armor for advanced rules

### **Post-Launch Improvements**

1. **CI/CD staging environment**: Deploy to `fadebender-staging` project for pre-prod testing
2. **End-to-end tests**: Run integration tests in Cloud Build before deploying
3. **Load testing**: Use Locust or k6 to validate autoscaling behavior
4. **Cost optimization**: Review Cloud Billing reports after 1 month; optimize based on actual usage
5. **Multi-region**: Add `europe-west1` deployment when EU users appear
6. **Backup automation**: Schedule Firestore exports via Cloud Scheduler + Cloud Functions
7. **Incident response playbook**: Document rollback procedures, emergency contacts

---

## **NEXT STEPS**

1. Fill in TODOs in `terraform/variables.tf`
2. Run `terraform init && terraform plan` to preview infrastructure
3. Run `terraform apply` to create GCP resources
4. Upload secrets to Secret Manager (Section 3E)
5. Push code to GitHub main branch to trigger Cloud Build
6. Verify deployments in Cloud Console
7. Test API endpoints and monitor logs/metrics
8. Set up budget alerts and SLO dashboards

---

**Document Version:** 1.0
**Last Updated:** 2025-10-05
**Review Date:** 2025-11-05
