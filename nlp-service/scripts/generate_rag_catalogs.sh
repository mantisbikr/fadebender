#!/bin/bash
# Generate both device and preset catalogs for RAG indexing

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║           RAG Catalog Generation                               ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Ensure we're in the project root
cd "$(dirname "$0")/../.."

# Generate device catalog
echo "🔧 Generating device catalog..."
python3 nlp-service/scripts/generate_device_catalog.py

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Generate preset catalog
echo "📦 Generating preset catalog..."
python3 nlp-service/scripts/generate_preset_catalog.py

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║           ✅ RAG Catalogs Generated Successfully               ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Generated files:"
echo "  📄 knowledge/fadebender/device-catalog.md"
echo "  📄 knowledge/fadebender/preset-catalog.md"
echo ""
echo "Next steps:"
echo "  1. Review the generated catalogs"
echo "  2. Index them into Vertex AI Search"
echo "  3. Test RAG queries"
echo ""
