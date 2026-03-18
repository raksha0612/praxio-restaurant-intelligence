#!/usr/bin/env bash
set -e

COMMAND="${1:-}"
ROOT="$(cd "$(dirname "$0")" && pwd)"

case "$COMMAND" in
  install)
    echo "→ Installing all dependencies with uv..."
    uv sync
    echo "✓ Done — run ./do app to start the dashboard"
    ;;

  app)
    echo "→ Starting Restaurant Intelligence dashboard..."
    uv run streamlit run app/app.py
    ;;

  lint)
    echo "→ Running ruff linter..."
    uv run ruff check app/ --fix
    echo "✓ Lint complete"
    ;;

  test)
    echo "→ Running tests..."
    uv run pytest tests/ -v
    ;;

  clean)
    echo "→ Cleaning cache and temp files..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name ".DS_Store" -delete 2>/dev/null || true
    echo "✓ Clean complete"
    ;;

  *)
    echo "Usage: ./do <command>"
    echo ""
    echo "  install   Install all dependencies via uv"
    echo "  app       Start the Streamlit dashboard"
    echo "  lint      Run ruff linter with auto-fix"
    echo "  test      Run pytest tests"
    echo "  clean     Remove __pycache__ and temp files"
    echo ""
    echo "  First time? Run:  ./do install && ./do app"
    exit 1
    ;;
esac
