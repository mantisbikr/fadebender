# Environment Configuration Guide

## Environment Files

Fadebender uses environment-specific configuration files for better security and deployment management:

```
.env.development  # Local development (your current setup)
.env.production   # Production deployment (never commit)
.env.test         # Testing environment
.env.staging      # Staging environment
```

## Usage

### Development (Default)
```bash
# Automatically loads .env.development
python app.py
```

### Production
```bash
ENV=production python app.py
```

### Other Environments
```bash
ENV=staging python app.py
ENV=test python app.py
```

## Security Features

✅ **All .env.* files are gitignored** - secrets never get committed
✅ **Environment-specific configurations** - different keys for dev/prod
✅ **Fallback to default .env** - backwards compatible
✅ **Clear logging** - shows which config file was loaded

## File Structure

```
nlp-service/
├── .env.example          # Template (safe to commit)
├── .env.development      # Your dev config (gitignored)
├── .env.production       # Production config (gitignored)
└── app.py               # Automatically loads correct config
```

## Setup New Environment

1. Copy template: `cp .env.example .env.production`
2. Edit with production API key
3. Deploy with: `ENV=production python app.py`

**Never commit any .env.* files except .env.example!**