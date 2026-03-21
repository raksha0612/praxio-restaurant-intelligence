#!/bin/bash
# ============================================================
# deploy.sh — Deploy / update the restaurant app on Hetzner
# Run from LOCAL machine: bash deploy/deploy.sh
# Requires: PRAXIO_SERVER_IP env var set
# ============================================================
set -e

SERVER_IP="${PRAXIO_SERVER_IP:-YOUR_SERVER_IP}"
REMOTE_DIR="/opt/praxiotech/restaurant-intelligence"
KEY="$HOME/.ssh/id_ed25519_praxio"

echo "==> Deploying Restaurant Intelligence to $SERVER_IP..."

echo "==> Syncing files..."
rsync -avz -e "ssh -i $KEY" \
  --exclude '.git' --exclude '.venv' --exclude '__pycache__' \
  --exclude 'scripts/data' --exclude 'app/output' \
  --exclude '.env' --exclude '*.pyc' \
  ./ root@$SERVER_IP:$REMOTE_DIR/

echo "==> Syncing .env file..."
scp -i $KEY .env root@$SERVER_IP:$REMOTE_DIR/.env

echo "==> Building and starting container..."
ssh -i $KEY root@$SERVER_IP "cd $REMOTE_DIR && docker compose up -d --build"

echo "==> Waiting for health check..."
sleep 10
ssh -i $KEY root@$SERVER_IP "cd $REMOTE_DIR && docker compose ps"

echo ""
echo "==> App running at http://$SERVER_IP:8502"
echo "==> With domain:  https://restaurant.praxiotech.de"
