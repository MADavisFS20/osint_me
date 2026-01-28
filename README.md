# Termux-OSINT Manager — Original Edition (Deployable Single-Command)

Overview
- Original OSINT & investigation manager implemented in Python for Termux (Android).
- Pure-Python investigative modules: TCP scanner, WHOIS, HTTP enumeration, subdomain brute-forcing, username discovery, image tools.
- Investigation & evidence management, scheduled jobs, and PDF export with a simple chain-of-custody SHA256 file.
- GUI: web-based (Bootstrap) designed to open in Termux:X11.

Single-command deploy
1. Ensure Termux is installed (F-Droid recommended) and optionally Termux:X11 for GUI.
2. Place all files from this release into a directory in Termux.
3. Make deploy script executable and run:
   - chmod +x deploy.sh
   - bash deploy.sh

First run
- A default admin user is created (admin / admin). Change this password immediately via the GUI by registering a new admin account or modifying the DB.

Security & Legal
- Use this tool only for lawful OSINT and authorized security testing.
- Record permission/scope in the investigation 'Scope note' field before collecting data.
- The system includes timeouts & concurrency caps to limit accidental misuse.

Extending
- Add more wordlists in data/subs.txt.
- Add new modules in backend/modules_core.py.
- Add PGP signing by installing GPG on the device and modifying pdf_report.py to call gpg for signing.
- Schedule exports or recurring scans using APScheduler (already included).

Support & next steps I can add
- PGP-signed PDF reports and timestamping with a trusted timestamping service.
- More advanced original modules: polite crawler, metadata extraction for files, public email harvesters, map visualizations for geotagged evidence.
- Hardened auth (refresh tokens, HTTPS, session revocation), multi-user role management, and encrypted DB.

If you want, I will:
- Add PGP signing integration (requires gpg installed in Termux).
- Add scheduled exports and vault-encrypted API key storage.
- Flesh out advanced original modules (polite crawler, metadata extraction).

Thank you — tell me which next item to implement and I’ll produce the changes and a follow-up single-commit patch you can paste into your Termux directory.