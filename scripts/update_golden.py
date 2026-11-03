"""Regenerate the golden snapshots (golden inbox, the platform inbox, and the platform inbox with GitHub). Review the diff before committing."""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.build import run_build  # noqa: E402

INBOX = ROOT / "tests" / "fixtures" / "inbox-golden"
OUT = ROOT / "tests" / "fixtures" / "golden" / "2026-W41.json"


PLATFORM_INBOX = ROOT / "tests" / "fixtures" / "inbox-platform"
PLATFORM_OUT = ROOT / "tests" / "fixtures" / "golden" / "platform-2026-W41.json"
GITHUB = ROOT / "tests" / "fixtures" / "github"
GITHUB_OUT = ROOT / "tests" / "fixtures" / "golden" / "github-2026-W41.json"


def write(inbox: Path, out: Path) -> None:
    with TemporaryDirectory() as tmp:
        res = run_build(inbox, "2026-W41", Path(tmp) / "out", Path(tmp) / "state", generated_at=datetime(2026, 10, 8, 9, 0, tzinfo=timezone.utc), template_path=Path(tmp) / "none")
        if not res.built:
            for i in res.check.blockers:
                print(i)
            sys.exit(1)
        data = res.snapshot
    for s in data["sources"]:
        s["asOf"] = "<mtime>"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out} ({len(data['products'])} products, {len(data['metrics'])} metric values)")


def main() -> None:
    write(INBOX, OUT)
    write(PLATFORM_INBOX, PLATFORM_OUT)  # register plus platform files; used by the component tests
    with TemporaryDirectory() as tmp:  # the platform inbox plus the GitHub extract; used by the component tests
        inbox = Path(tmp) / "inbox"
        shutil.copytree(PLATFORM_INBOX, inbox)
        shutil.copytree(GITHUB, inbox / "github")
        write(inbox, GITHUB_OUT)


if __name__ == "__main__":
    main()
