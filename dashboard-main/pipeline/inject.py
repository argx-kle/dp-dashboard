"""Inject the snapshot JSON into the one-file app template."""

from __future__ import annotations

import re
from pathlib import Path

PLACEHOLDER_RE = re.compile(r'<script type="application/json" id="snapshot">.*?</script>', re.DOTALL)


def escape_for_script(json_text: str) -> str:
    """Make JSON safe inside a <script> block: no `</`, no U+2028/2029 line breaks."""
    return json_text.replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def inject(template_html: str, json_text: str) -> str:
    if not PLACEHOLDER_RE.search(template_html):
        raise ValueError('Template has no <script type="application/json" id="snapshot"> placeholder')
    replacement = f'<script type="application/json" id="snapshot">{escape_for_script(json_text)}</script>'
    return PLACEHOLDER_RE.sub(lambda _m: replacement, template_html, count=1)


def inject_file(template_path: Path, json_text: str, out_path: Path) -> None:
    html = template_path.read_text(encoding="utf-8")
    out_path.write_text(inject(html, json_text), encoding="utf-8")
