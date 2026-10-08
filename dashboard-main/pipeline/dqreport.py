"""dq-report.html: the data-quality report the program team sends to DPOs."""

from __future__ import annotations

from html import escape

from pipeline.contracts import DQItem, SourceStatus
from pipeline.registry import load_platform_config

CSS = """
body{font-family:Arial,Helvetica,sans-serif;margin:0;color:#002834;background:#fff}
header{background:#002834;color:#fff;padding:16px 24px}
header h1{margin:0;font-size:20px;font-weight:600}
header p{margin:4px 0 0;opacity:.85;font-size:13px}
main{padding:16px 24px 40px;max-width:1100px}
h2{font-size:15px;color:#18687F;margin:24px 0 8px;text-transform:uppercase;letter-spacing:.04em}
table{border-collapse:collapse;width:100%;font-size:13px}
th{text-align:left;background:#D2F1FA;color:#002834;padding:6px 8px;border-bottom:1px solid #9FA5AD}
td{padding:6px 8px;border-bottom:1px solid #e5e7eb;vertical-align:top}
.sev{display:inline-block;padding:1px 8px;border-radius:999px;font-weight:600;font-size:12px}
.blocker{background:#E55E5E;color:#fff}.warning{background:#FFE224;color:#002834}
.ok{color:#2e7d32}.empty{color:#6b7280;font-style:italic}
code{background:#f3f4f6;padding:0 4px;border-radius:3px}
"""


def _platform_section(resolution) -> str:
    """Which platform names became which product, and what is not counted and why."""
    if resolution is None:
        return ""
    teams = load_platform_config().teams
    counted = sorted(resolution.included, key=lambda p: ((p.team or "~"), p.key))
    merged = "".join(
        f"<tr><td><code>{escape(p.key)}</code></td><td>{escape(p.display_name)}</td><td>{escape(teams.get(p.team, p.team) if p.team else '–')}</td>"
        f"<td>{escape(', '.join(p.names[1:]) or '–')}</td><td>{escape(', '.join(p.keyids) or '–')}</td></tr>"
        for p in counted
    )
    excluded = "".join(
        f"<tr><td><code>{escape(p.key)}</code></td><td>{escape(', '.join(p.names[1:]) or '–')}</td><td>{escape(p.reason)}</td></tr>"
        for p in sorted(resolution.excluded, key=lambda p: p.key)
    )
    return (
        f"<h2>Products on the platform</h2><p>{len(counted)} products counted from the NextData and validation files; "
        f"{len(resolution.excluded)} not counted. Decisions come from the rules in registry/platform.yaml and the inbox crosswalk.csv.</p>"
        "<table><thead><tr><th>Product</th><th>Shown as</th><th>Team</th><th>Other NextData names</th><th>Validation keyids</th></tr></thead>"
        f"<tbody>{merged}</tbody></table>"
        + (
            "<h2>Not counted</h2><table><thead><tr><th>Name</th><th>Other names</th><th>Reason</th></tr></thead>"
            f"<tbody>{excluded}</tbody></table>"
            if excluded
            else ""
        )
    )


def render(week_id: str, as_of: str, sources: list[SourceStatus], issues: list[DQItem], built: bool, resolution=None) -> str:
    blockers = [i for i in issues if i.severity == "blocker"]
    warnings = [i for i in issues if i.severity == "warning"]
    status = "Draft pack built" if built else f"Pack not built: {len(blockers)} blocker(s)"
    rows = "".join(
        f"<tr><td><span class='sev {escape(i.severity)}'>{escape(i.severity)}</span></td>"
        f"<td><code>{escape(i.rule)}</code></td><td>{escape(i.urn or '')}</td>"
        f"<td>{escape(i.file or '')}{(' · row ' + str(i.row)) if i.row else ''}</td><td>{escape(i.message)}</td></tr>"
        for i in [*blockers, *warnings]
    )
    src = "".join(
        f"<tr><td>{escape(s.name)}</td><td>{escape(s.file)}</td><td>{escape(s.as_of)}</td><td class='{ 'ok' if s.status == 'ok' else ''}'>{escape(s.status)}</td><td>{s.rows}</td></tr>"
        for s in sources
    )
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Data quality · {escape(week_id)}</title>
<meta name="viewport" content="width=device-width,initial-scale=1"><style>{CSS}</style></head><body>
<header><h1>Data Product Delivery · data-quality report · {escape(week_id)}</h1><p>As of {escape(as_of)} · {escape(status)} · {len(blockers)} blockers · {len(warnings)} warnings</p></header>
<main>
<h2>Sources</h2><table><thead><tr><th>Table</th><th>File</th><th>Last modified</th><th>Status</th><th>Rows</th></tr></thead><tbody>{src}</tbody></table>
<h2>Findings</h2>
{('<table><thead><tr><th>Severity</th><th>Rule</th><th>URN</th><th>Where</th><th>Message</th></tr></thead><tbody>' + rows + '</tbody></table>') if rows else "<p class='empty'>No findings.</p>"}
{_platform_section(resolution)}
</main></body></html>"""
