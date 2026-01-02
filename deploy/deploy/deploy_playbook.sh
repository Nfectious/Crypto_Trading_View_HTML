#!/usr/bin/env bash
set -euo pipefail

BASE="$HOME/crypto-playbook"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_DIR="${ROOT_DIR}"

echo "Deploying playbook to ${BASE}"
mkdir -p "${BASE}"
mkdir -p "${BASE}/clips" "${BASE}/pdf" "${BASE}/deploy"

if command -v rsync &>/dev/null; then
  rsync -av --delete "${SRC_DIR}/index.html" "${BASE}/"
  rsync -av --delete "${SRC_DIR}/style.css" "${BASE}/"
  rsync -av --delete "${SRC_DIR}/script.js" "${BASE}/"
  rsync -av --delete "${SRC_DIR}/clips/" "${BASE}/clips/"
  rsync -av --delete "${SRC_DIR}/pdf/" "${BASE}/pdf/"
  rsync -av --delete "${SRC_DIR}/deploy/" "${BASE}/deploy/"
else
  cp -v "${SRC_DIR}/index.html" "${BASE}/"
  cp -v "${SRC_DIR}/style.css" "${BASE}/"
  cp -v "${SRC_DIR}/script.js" "${BASE}/"
  cp -rv "${SRC_DIR}/clips"/* "${BASE}/clips/" || true
  cp -rv "${SRC_DIR}/pdf"/* "${BASE}/pdf/" || true
  cp -rv "${SRC_DIR}/deploy"/* "${BASE}/deploy/" || true
fi

echo "Files copied to ${BASE}"

if command -v xdg-open &>/dev/null; then
  xdg-open "${BASE}/index.html" &>/dev/null || true
elif command -v termux-open &>/dev/null; then
  termux-open "${BASE}/index.html" || true
else
  echo "Open ${BASE}/index.html manually in your browser."
fi

