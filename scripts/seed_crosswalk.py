"""Write a first crosswalk.csv from the platform files in the inbox, for the program lead to review.

Every NextData name and validation keyid gets one row: the product it belongs to, whether it is counted, why,
and the rule that decided. `domain` is left empty (the product-to-domain map decides; `domain_by_rule` shows the
result); fill it only to override one product. Edit `product`, `include`, `domain` or `display_name`, then set
`reviewed` to yes. The pipeline applies the file on every run; names it has not seen yet are decided by rule and reported.

Usage
  python scripts/seed_crosswalk.py --inbox inbox            # writes inbox/crosswalk.csv (or crosswalk.proposed.csv if one exists)
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.platform import CROSSWALK, CROSSWALK_COLUMNS, crosswalk_rows, load_platform, resolve  # noqa: E402
from pipeline.registry import load_platform_config  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inbox", type=Path, default=Path("inbox"))
    ap.add_argument("--out", type=Path, help="default: <inbox>/crosswalk.csv, or crosswalk.proposed.csv when one exists")
    args = ap.parse_args()

    src = load_platform(args.inbox)
    if not src.present:
        sys.exit(f"No platform files under {args.inbox}/nextdata or {args.inbox}/validation")
    res = resolve(src, load_platform_config())
    out = args.out or (args.inbox / (CROSSWALK if src.crosswalk is None else "crosswalk.proposed.csv"))
    rows = crosswalk_rows(res)
    with open(out, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CROSSWALK_COLUMNS)
        w.writeheader()
        w.writerows(rows)
    counted = res.included
    print(f"wrote {out}: {len(rows)} names -> {len(counted)} products counted, {len(res.excluded)} not counted")
    for domain, n in Counter(p.domain for p in counted).most_common():
        print(f"  {domain:16s} {n}")
    for reason, n in Counter(p.reason for p in res.excluded).most_common():
        print(f"  not counted: {reason} ({n})")


if __name__ == "__main__":
    main()
