#!/usr/bin/env bash
set -euo pipefail

APP_HOST="${APP_HOST:-0.0.0.0}"
APP_PORT="${APP_PORT:-8000}"
ROTATE_SECONDS="${ROTATE_SECONDS:-100}"   # 30 seconds default

generate_secret_key() {
  local key=""
  while [[ ${#key} -lt 50 ]]; do
    key="$(head -c 64 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 50 || true)"
  done
  printf "%s" "$key"
}

cleanup() {
  if [[ -n "${SERVER_PID:-}" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
    kill -TERM "$SERVER_PID" 2>/dev/null || true
    for _ in {1..10}; do
      kill -0 "$SERVER_PID" 2>/dev/null || break
      sleep 0.2
    done
    kill -KILL "$SERVER_PID" 2>/dev/null || true
  fi
}

trap cleanup EXIT INT TERM

service postgresql start

sleep 5

# Create DB user if missing
psql -U postgres -tc "SELECT 1 FROM pg_roles WHERE rolname='compfess'" | grep -q 1 || \
  psql -U postgres -c "CREATE USER compfess WITH PASSWORD 'compfess';"

# Create DB if missing
psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname='compfess'" | grep -q 1 || \
  psql -U postgres -c "CREATE DATABASE compfess OWNER compfess;"

python /app/manage.py makemigrations 
python /app/manage.py migrate 
python /app/manage.py ensure_admin 

echo "[*] Starting loop: rotate SECRET_KEY every ${ROTATE_SECONDS}s"
while true; do
  export DJANGO_SECRET_KEY="$(generate_secret_key)"
  echo "[+] $(date -u +'%Y-%m-%dT%H:%M:%SZ') New SECRET_KEY: $DJANGO_SECRET_KEY"

  python /app/manage.py runserver --noreload "${APP_HOST}:${APP_PORT}" &
  SERVER_PID=$!

  sleep "${ROTATE_SECONDS}"

  echo "[!] $(date -u +'%Y-%m-%dT%H:%M:%SZ') Rotating key; stopping server (pid ${SERVER_PID})..."
  kill -TERM "${SERVER_PID}" 2>/dev/null || true
  for _ in {1..10}; do
    if ! kill -0 "${SERVER_PID}" 2>/dev/null; then break; fi
    sleep 0.2
  done
  kill -KILL "${SERVER_PID}" 2>/dev/null || true
  unset SERVER_PID
done
