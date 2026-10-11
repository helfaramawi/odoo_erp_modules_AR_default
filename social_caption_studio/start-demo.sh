#!/usr/bin/env bash
# Social Caption Generator - start the demo (macOS / Linux): ./start-demo.sh
cd "$(dirname "$0")"
if ! docker info >/dev/null 2>&1; then
  echo "Docker is not running. Start Docker Desktop (or the docker service) and try again."
  exit 1
fi
echo "Starting Odoo... the first time downloads about 1 GB and takes a few minutes."
docker compose up -d || exit 1
echo "Waiting for Odoo to be ready..."
until curl -s -o /dev/null http://localhost:8069/web/login; do sleep 3; done
echo
echo "Ready: http://localhost:8069   login: admin   password: admin"
(open http://localhost:8069 || xdg-open http://localhost:8069) >/dev/null 2>&1 || true
