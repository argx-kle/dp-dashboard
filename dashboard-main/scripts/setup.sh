#!/bin/sh
# One-time setup after cloning, forking or unzipping the repository (macOS or Linux).
#   sh scripts/setup.sh           Python environment with the dp command, app packages, the dashboard
#                                 template, and a test build on the made-up inbox
#   sh scripts/setup.sh --tests   the same, plus the browser the end-to-end tests use
# Safe to run again: it repairs a .venv copied from another folder and reinstalls the app packages.
set -e
cd "$(dirname "$0")/.."

fail() {
  printf 'Setup stopped: %s\n' "$1" >&2
  exit 1
}

# Python 3.11 or newer
PY=""
for c in python3.13 python3.12 python3.11 python3; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(sys.version_info < (3, 11))' 2>/dev/null; then
    PY=$c
    break
  fi
done
[ -n "$PY" ] || fail "Python 3.11 or newer is needed (https://www.python.org/downloads/)."

# Node.js 20 or newer, to build the dashboard template
command -v node >/dev/null 2>&1 || fail "Node.js 20 or newer is needed (https://nodejs.org/)."
node -e 'process.exit(Number(process.versions.node.split(".")[0]) >= 20 ? 0 : 1)' || fail "Node.js 20 or newer is needed; this machine has $(node --version)."

echo "1/4 Python environment in .venv, with the dp command"
# A .venv copied from another folder still points there; start it fresh.
if [ -d .venv ] && [ "$(.venv/bin/python -c 'import sys; print(sys.prefix)' 2>/dev/null)" != "$(pwd -P)/.venv" ]; then
  rm -rf .venv
fi
[ -d .venv ] || "$PY" -m venv .venv
.venv/bin/python -m pip install --quiet --disable-pip-version-check -e ".[dev]"

echo "2/4 App packages in app/node_modules"
(cd app && npm ci --no-audit --no-fund --loglevel=error)

echo "3/4 Dashboard template app/dist/template.html"
(cd app && npm run build --silent >/dev/null)

echo "4/4 Test build on the made-up inbox"
tmp=$(mktemp -d)
.venv/bin/dp build --inbox tests/fixtures/inbox-golden --week 2026-W41 --out "$tmp/out" --state "$tmp/state" >/dev/null ||
  fail "the test build did not finish; run it by hand to see why: .venv/bin/dp build --inbox tests/fixtures/inbox-golden --week 2026-W41"
[ -f "$tmp/out/2026-W41/index.html" ] || fail "the test build wrote no index.html."
rm -rf "$tmp"

if [ "$1" = "--tests" ]; then
  echo "Browser for the end-to-end tests"
  .venv/bin/playwright install chromium
fi

cat <<'EOF'

Ready.
  Open the demo:         sh scripts/demo.sh
  Build a dashboard:     .venv/bin/dp build --inbox tests/fixtures/inbox-golden --week 2026-W41
                         then open out/2026-W41/index.html
  Your own inbox:        see "Weekly run" in README.md
EOF
