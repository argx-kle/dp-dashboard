"""dp: fetch-github, check, build, preview, approve."""

from __future__ import annotations

import sys
import webbrowser
from datetime import date
from pathlib import Path

import click

from pipeline import TEMPLATE_PATH
from pipeline.build import Registries, resolve_as_of, run_approve, run_build, run_check
from pipeline.contracts import DQItem
from pipeline.dates import parse_week, week_of


def _print_issues(issues: list[DQItem]) -> None:
    for i in issues:
        where = " · ".join(x for x in [i.file, f"row {i.row}" if i.row else None, i.urn] if x)
        click.echo(f"  {i.severity.upper():7} {i.rule:16} {where + ' · ' if where else ''}{i.message}")


def _summary(blockers: int, warnings: int) -> str:
    return f"{blockers} blocker(s), {warnings} warning(s)"


@click.group()
def main() -> None:
    """Data Product Dashboard: turn the inbox folder into a signed-off executive pack."""


@main.command()
@click.option("--inbox", type=click.Path(path_type=Path), default=Path("inbox"), show_default=True)
@click.option("--week", default=None, help="ISO week, e.g. 2026-W43 (default: this week)")
@click.option("--as-of", type=click.DateTime(formats=["%Y-%m-%d"]), default=None, help="Override the as-of date")
def check(inbox: Path, week: str | None, as_of) -> None:
    """Read and validate the inbox files; print the data-quality report."""
    week = week or week_of(date.today())
    parse_week(week)
    as_of_date = resolve_as_of(week, as_of.date() if as_of else None)
    result, _ = run_check(inbox, as_of_date)
    click.echo(f"dp check · inbox {inbox} · week {week} · as of {as_of_date}")
    for s in result.inbox.sources:
        click.echo(f"  {s.status.upper():8} {s.name:11} {s.file} ({s.rows} rows)")
    _print_issues(result.issues)
    click.echo(_summary(len(result.blockers), len(result.warnings)))
    sys.exit(1 if result.blockers else 0)


@main.command()
@click.option("--inbox", type=click.Path(path_type=Path), default=Path("inbox"), show_default=True)
@click.option("--week", required=True, help="ISO week, e.g. 2026-W43")
@click.option("--as-of", type=click.DateTime(formats=["%Y-%m-%d"]), default=None, help="Override the as-of date (default: Friday of the week)")
@click.option("--out", type=click.Path(path_type=Path), default=Path("out"), show_default=True)
@click.option("--state", type=click.Path(path_type=Path), default=Path("state"), show_default=True)
@click.option("--template", type=click.Path(path_type=Path), default=TEMPLATE_PATH, help="App template HTML")
def build(inbox: Path, week: str, as_of, out: Path, state: Path, template: Path) -> None:
    """Build the draft snapshot, index.html (marked draft) and dq-report.html."""
    parse_week(week)
    result = run_build(inbox, week, out, state, as_of.date() if as_of else None, template_path=template)
    chk = result.check
    click.echo(f"dp build · inbox {inbox} · week {week} · as of {chk.as_of}")
    _print_issues(chk.issues)
    click.echo(_summary(len(chk.blockers), len(chk.warnings)))
    if not result.built:
        click.echo(f"Pack NOT built. See {result.out_dir / 'dq-report.html'}")
        sys.exit(1)
    for f in result.files:
        click.echo(f"  wrote {f}")
    click.echo("Draft pack built. Review index.html, then `dp approve`.")


@main.command()
@click.option("--week", required=True)
@click.option("--by", "approved_by", required=True, help='Who signs off, e.g. "Program lead"')
@click.option("--inbox", type=click.Path(path_type=Path), default=Path("inbox"), show_default=True)
@click.option("--out", type=click.Path(path_type=Path), default=Path("out"), show_default=True)
@click.option("--state", type=click.Path(path_type=Path), default=Path("state"), show_default=True)
@click.option("--template", type=click.Path(path_type=Path), default=TEMPLATE_PATH)
def approve(week: str, approved_by: str, inbox: Path, out: Path, state: Path, template: Path) -> None:
    """Stamp the sign-off, copy the snapshot to state/, rebuild index.html as signed off."""
    parse_week(week)
    try:
        saved = run_approve(week, approved_by, out, state, inbox, template_path=template)
    except (FileNotFoundError, RuntimeError) as exc:
        click.echo(f"Not approved: {exc}")
        sys.exit(1)
    click.echo(f"Approved {week} by {approved_by}. Snapshot stored at {saved}.")


@main.command("fetch-github")
@click.option("--inbox", type=click.Path(path_type=Path), default=Path("inbox"), show_default=True)
@click.option("--check", "check_only", is_flag=True, help="Only test the connection")
@click.option("--repos", multiple=True, help="Limit to this repository (repeat the option for more)")
@click.option("--workers", type=int, default=4, show_default=True)
def fetch_github(inbox: Path, check_only: bool, repos: tuple[str, ...], workers: int) -> None:
    """Read the data product repositories from GitHub into <inbox>/github/ (read-only)."""
    from pipeline.github_fetch import FetchError, GitHub, github_token, write_tables
    from pipeline.registry import load_platform_config

    cfg = load_platform_config()
    try:
        token, source = github_token()
        gh = GitHub(token, cfg.github_org)
        conn = gh.check_connection()
        click.echo(
            f"Connected as {conn['login']} (token from {source}); {cfg.github_org} membership: {conn['state']}/{conn['role']}; "
            f"REST rate limit {conn['remaining']}/{conn['limit']}"
        )
        if conn["state"] != "active":
            click.echo(f"  warning: not an active member of {cfg.github_org}; private repositories will be missing")
        if check_only:
            return
        click.echo("Reading repositories and deployments", nl=False)
        result = gh.fetch(cfg.github_repo_pattern, only=list(repos) or None, workers=workers, login=conn["login"], progress=lambda: click.echo(".", nl=False))
    except FetchError as exc:
        click.echo(f"\nNot fetched: {exc}")
        sys.exit(1)
    folder = inbox / "github"
    write_tables(result.tables, folder)
    click.echo(f"\nDone in {result.seconds:.0f}s -> {folder} (REST rate limit left {result.rate_remaining})")
    for t in ("repositories", "deployments", "deployment_statuses"):
        click.echo(f"  {t:<22}{len(result.tables[t]):>6} rows")
    if result.issues:
        click.echo(f"{len(result.issues)} requests were unavailable; see {folder / 'issues.csv'} (affected values are blank)")


@main.command()
@click.option("--week", required=True)
@click.option("--out", type=click.Path(path_type=Path), default=Path("out"), show_default=True)
def preview(week: str, out: Path) -> None:
    """Open index.html for the week in the default browser."""
    parse_week(week)
    path = (out / week / "index.html").resolve()
    if not path.exists():
        click.echo(f"No dashboard at {path}; run `dp build --week {week}` first")
        sys.exit(1)
    webbrowser.open(path.as_uri())
    click.echo(f"Opened {path}")


if __name__ == "__main__":
    main()
