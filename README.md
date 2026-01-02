
# Crypto Chart Playbook

This repository contains a small, self-contained static HTML playbook for structured, pullback-only crypto trade decision-making. It is designed to be run locally across devices (laptop, phone, Termux) without a server.

**Crypto Chart Playbook**

Overview
 - A compact, offline-first static playbook for disciplined crypto trade execution. The UI is intentionally simple: `index.html`, `style.css`, and `script.js` form the single-page playbook. Media assets live in `clips/` and reference material lives in `pdf/`.

Repository layout
 - `index.html` — main playbook UI (includes Daily Bias form and log)
 - `style.css` — site styles
 - `script.js` — UI behavior; includes Daily Bias logging (localStorage), export, and clear
 - `clips/` — example video clips (optional)
 - `pdf/` — printable HTML + stylesheet and generated PDF
 - `deploy/` — helper scripts for deployment and PDF export
 - `LICENSE`, `.gitignore`, `CONTRIBUTING.md` — repo metadata

Quick start (preview)
 - Open `index.html` in any modern browser to preview the playbook locally.

Deploy locally (one-command)
 - Linux / macOS / Termux:

```bash
./deploy_playbook.sh
```

 - Windows (cmd / double-click):

```bat
deploy_playbook_windows.bat
```

What these scripts do
 - Create `crypto-playbook` in your home folder (`$HOME` or `%USERPROFILE%`).
 - Copy `index.html`, assets (`clips/`, `pdf/`) and helper scripts into that folder.
 - Attempt to open `index.html` in your default browser.

Daily Bias logging
 - The playbook includes a `Daily Bias` form. Saved entries persist per-browser using `localStorage`.
 - Features: save timestamped entries, view a scrollable Bias Log, `Export CSV`, and `Clear Log`.
 - Files involved: `index.html` (UI), `script.js` (storage + export logic).

Formatted PDF (printable)
 - A polished printable source is included at `pdf/pullback-playbook-sol-ltc.html` and uses `pdf/print.css` for layout.
 - Automated export helpers:
    - `deploy/convert_to_pdf.sh` — Linux/macOS script (uses `wkhtmltopdf` or headless Chrome)
    - `deploy/convert_to_pdf_windows.bat` — Windows batch (tries `wkhtmltopdf` or Chrome/Edge)

Generate the PDF
 - Recommended: install `wkhtmltopdf` for best results, or ensure `chrome`/`msedge`/`chromium` is in your PATH to use headless print-to-PDF.

Linux / macOS / Termux
```bash
./deploy/convert_to_pdf.sh
```

Windows (cmd)
```bat
deploy\convert_to_pdf_windows.bat
```

If you don't have those tools, open `pdf/pullback-playbook-sol-ltc.html` in a browser and choose Print → Save as PDF.

Editing the playbook
 - To change copy or modules: edit `index.html`. The layout is simple and uses semantic sections — add modules by copying the SOL or LTC sections.
 - To add media: drop files into `clips/` and update the `<video>` source in `index.html`.
 - To update print/PDF layout: edit `pdf/pullback-playbook-sol-ltc.html` and `pdf/print.css`.

Versioning and contribution
 - This repo uses the MIT license (`LICENSE`).
 - Keep changes small and focused. See `CONTRIBUTING.md` for guidance.

Troubleshooting
 - If `deploy` scripts fail to open the page, open `crypto-playbook/index.html` manually.
 - If PDF export fails: install `wkhtmltopdf` or Chrome/Edge and re-run the export script.
 - If Daily Bias entries aren't visible, ensure your browser allows `localStorage` for local files (or use a simple local server: `python -m http.server`).

Next steps I can help with
 - Run the PDF export here if you install `wkhtmltopdf` or make Chrome/Edge available in PATH.
 - Add a logo, tweak fonts, or create a one-page summary card for quick printing.

Contact
 - If you want a copy exported or packaged, tell me which format and I will produce it.

Enjoy — this is meant to be your offline, cross-device trading execution tool.

Exporting the formatted PDF

1. The formatted printable source is at `pdf/pullback-playbook-sol-ltc.html` and uses `pdf/print.css` for layout.
2. To generate a PDF automatically, run the included helper:

Linux / macOS / Termux:
```bash
./deploy/convert_to_pdf.sh
```

Windows (cmd):
```bat
deploy\convert_to_pdf_windows.bat
```

These scripts will try `wkhtmltopdf` first, then headless Chrome/Chromium. If you don't have either, open `pdf/pullback-playbook-sol-ltc.html` in a browser and use Print → Save as PDF for best results.
