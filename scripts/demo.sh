#!/bin/sh
# Open a saved demo of the dashboard.
#   sh scripts/demo.sh                 demo/index.html: the showcase week 2026-W47 (made up; scripts/make_showcase.py)
#   sh scripts/demo.sh --named         demo/index-named.html: week 2026-W41, the real product and domain names, made-up values
#   add --rebuild to rebuild from the current app first (the named demo from tests/fixtures/inbox-named-demo;
#   regenerate that fixture from a real inbox with: python scripts/make_named_demo.py generate --inbox inbox)
set -e
cd "$(dirname "$0")/.."
named=0; rebuild=0
for a in "$@"; do
  case "$a" in
    --named) named=1 ;;
    --rebuild) rebuild=1 ;;
  esac
done
if [ "$rebuild" = 1 ]; then
  [ -x .venv/bin/dp ] && [ -d app/node_modules ] || { echo "Run sh scripts/setup.sh once before --rebuild." >&2; exit 1; }
  (cd app && npm run build)
  if [ "$named" = 1 ]; then
    .venv/bin/python scripts/make_named_demo.py build
  else
    .venv/bin/python scripts/make_showcase.py build
  fi
fi
if [ "$named" = 1 ]; then f=demo/index-named.html; else f=demo/index.html; fi
if command -v open >/dev/null 2>&1; then open "$f"; else echo "open $f in a browser"; fi
