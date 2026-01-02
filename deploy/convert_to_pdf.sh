#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_PDF="${ROOT_DIR}/pdf/pullback-playbook-sol-ltc.pdf"
HTML="${ROOT_DIR}/pdf/pullback-playbook-sol-ltc.html"

echo "Exporting PDF to ${OUT_PDF}"

if command -v wkhtmltopdf &>/dev/null; then
  wkhtmltopdf --enable-local-file-access "${HTML}" "${OUT_PDF}"
  echo "PDF created with wkhtmltopdf"
elif command -v chrome &>/dev/null || command -v google-chrome &>/dev/null || command -v chromium &>/dev/null; then
  CHROME_BIN=$(command -v chrome || command -v google-chrome || command -v chromium)
  "${CHROME_BIN}" --headless --disable-gpu --print-to-pdf="${OUT_PDF}" "file://${HTML}"
  echo "PDF created with Chrome headless"
else
  echo "No PDF renderer found. Install wkhtmltopdf or Chrome/Chromium."
  exit 2
fi
