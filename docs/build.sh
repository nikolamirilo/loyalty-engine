#!/usr/bin/env bash
# Rebuilds the user docs and publishes them to the client app, which serves them at /docs.
#
#   ./docs/build.sh            build, then copy to client/public/docs/index.html
#   ./docs/build.sh --check    also run the browser checks (needs Playwright + Chromium)
set -euo pipefail

cd "$(dirname "$0")"
python3 make_shots.py
python3 tooling/scripts/build.py .

mkdir -p ../client/public/docs
cp dist/preview.html ../client/public/docs/index.html
echo "Published to client/public/docs/index.html (served at /docs)"

if [[ "${1:-}" == "--check" ]]; then
  node tooling/scripts/check.js .
  python3 tooling/scripts/check_labels.py . ../client ../api
fi
