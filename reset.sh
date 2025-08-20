#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./reset.sh             # cleanup + build + up
#   ./reset.sh --seed      # idem e poi inserisce dati demo
#   ./reset.sh --no-build  # salta la build (riusa le ultime immagini)
#   ./reset.sh --clean-all # fa anche prune di immagini/volumi orfani

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

SEED=false
BUILD=true
CLEAN_ALL=false

for arg in "$@"; do
  case "$arg" in
    --seed) SEED=true ;;
    --no-build) BUILD=false ;;
    --clean-all) CLEAN_ALL=true ;;
    *) echo "Unknown option: $arg" && exit 1 ;;
  esac
done

echo "👉 Stopping & removing containers + volumes..."
docker compose down -v --remove-orphans

if [ "$CLEAN_ALL" = true ]; then
  echo "🧹 Pruning dangling images/volumes/networks..."
  docker system prune -f
fi

if [ "$BUILD" = true ]; then
  echo "🔨 Building images..."
  docker compose build
fi

echo "🚀 Starting services..."
docker compose up -d

echo "⏳ Waiting a moment for Postgres health..."
# semplice attesa (evita coupling con nomi container)
sleep 8

if [ "$SEED" = true ]; then
  echo "🌱 Seeding demo data..."
  # Se la tua immagine non ha bash, usa 'sh -lc'
  if docker compose exec priceforge bash -lc "python app/seed.py"; then
    echo "✅ Seed completato."
  else
    echo "⚠️  Seed fallito. Controlla i log:  docker compose logs --no-color priceforge"
  fi
fi

echo "✅ Done. Endpoints:"
echo "   API     → http://localhost:8000"
echo "   Docs    → http://localhost:8000/docs"
echo "   pgAdmin → http://localhost:8080"