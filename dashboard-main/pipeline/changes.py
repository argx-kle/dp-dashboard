"""The three-line "what changed" note, from the current snapshot and the last approved one."""

from __future__ import annotations

MAX_LINES = 3


def _names(products: list[dict], urns: list[str], limit: int = 4) -> str:
    by = {p["urn"]: p["name"] for p in products}
    names = [by.get(u, u) for u in urns]
    if len(names) > limit:
        return ", ".join(names[:limit]) + f" and {len(names) - limit} more"
    return ", ".join(names)


def compute_changes(current: dict, previous: dict | None) -> list[str]:
    if previous is None:
        return ["First snapshot: no previous approved week to compare."]
    lines: list[str] = []
    prev_products = {p["urn"]: p for p in previous["products"]}
    cur_products = current["products"]

    newly_certified = [
        p["urn"] for p in cur_products
        if p.get("firstG4Date") and not prev_products.get(p["urn"], {}).get("firstG4Date")
    ]
    if newly_certified:
        lines.append(f"Certified since {previous['weekId']}: {_names(cur_products, newly_certified)}.")

    def flag_set(p: dict) -> set[str]:
        return {f["code"] for f in p.get("flags", [])}

    raised, cleared = [], []
    for p in cur_products:
        before = flag_set(prev_products.get(p["urn"], {}))
        after = flag_set(p)
        for code in sorted(after - before):
            raised.append(f"{p['name']} ({code})")
        for code in sorted(before - after):
            cleared.append(f"{p['name']} ({code})")
    if raised:
        lines.append("New flags: " + ", ".join(raised[:4]) + (f" and {len(raised) - 4} more" if len(raised) > 4 else "") + ".")
    if cleared:
        lines.append("Cleared: " + ", ".join(cleared[:4]) + (f" and {len(cleared) - 4} more" if len(cleared) > 4 else "") + ".")

    def behind(snapshot: dict) -> set[str]:
        return {m["scope"] for m in snapshot["metrics"] if m["id"] == "certified_qtd" and m.get("flag") == "BEHIND"}

    now_behind, was_behind = behind(current), behind(previous)
    if now_behind != was_behind:
        name = {d["id"]: d["name"] for d in current.get("domains", [])}
        names = lambda ids: ", ".join(sorted(name.get(i, i) for i in ids))  # noqa: E731
        parts = []
        if now_behind - was_behind:
            parts.append("now behind: " + names(now_behind - was_behind))
        if was_behind - now_behind:
            parts.append("back on track: " + names(was_behind - now_behind))
        lines.append("Domains " + "; ".join(parts) + ".")

    if not lines:
        lines.append(f"No certifications or flag changes since {previous['weekId']}.")
    return lines[:MAX_LINES]
