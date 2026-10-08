# Data Product Dashboard

Turns a folder of weekly files (the product register, plus optional NextData and validation-tool exports) into a signed-off executive pack: one self-contained `index.html` dashboard and a data-quality report. It follows the argenx Data Product Governance Framework gates, G1 Intake to G6 Retire. Everything runs locally from files; there is no server and no login.

## 1. See it without installing anything

Open `demo/index.html` in a browser (double-click it). It is the full dashboard on a made-up showcase week, 2026-W47: 58 products in Commercial, TechOps, R&D and G&A, every stage, flag and health state. `demo/index-named.html` is week 2026-W41 with the real data product and domain names and made-up values.

## 2. Set up once

You need **Python 3.11 or newer** and **Node.js 20 or newer** (`python3 --version`, `node --version`). Then, from the repository folder (a clone, a fork or an unzipped download):

```bash
sh scripts/setup.sh
```

It creates the Python environment in `.venv` with the `dp` command, installs the app packages, builds the dashboard template (`app/dist/template.html`), and checks that a test dashboard builds. It takes a minute or two and is safe to run again. Add `--tests` to also install the browser the end-to-end tests use.

## 3. Generate a dashboard

Activate the environment once per terminal, then build from the made-up inbox and open the result:

```bash
source .venv/bin/activate
dp build --inbox tests/fixtures/inbox-golden --week 2026-W41
dp preview --week 2026-W41
```

`dp build` writes `out/2026-W41/`: `index.html` (the dashboard, marked draft), `snapshot.json` (the numbers) and `dq-report.html` (the data-quality report). Try `--inbox tests/fixtures/inbox-platform` for a week with NextData and validation files.

## Weekly run with real files

Put the week's files in a folder called `inbox/` in the repository (git ignores it, together with `out/` and `state/`, so real data is never committed):

```
inbox/
  register.xlsx      the product register: sheets Products, GateEvents, Targets, Capacity
                     (or the same four tables as products.csv, gate_events.csv, targets.csv, capacity.csv)
  nextdata/          optional: NextData `dp list` output (.txt), catalog lookup (.csv), domain tree (.csv with a parent column)
  validation/        optional: repo validation tool results (.xlsx summary or .csv)
  crosswalk.csv      optional: the program lead's decisions on which names are one product, what is counted, display names
```

The empty register template for Data Product Owners is `templates/register.xlsx`. Then, with the environment active:

```bash
dp check   --inbox inbox                          # read and validate the files; lists blockers and warnings
dp build   --inbox inbox --week 2026-W43          # draft pack in out/2026-W43/
dp preview --week 2026-W43                        # open the draft in the browser
dp approve --week 2026-W43 --by "Program lead"    # sign off: the footer shows who signed, the snapshot is kept in state/
```

- `dp build` refuses to write a dashboard while any blocker exists. `dq-report.html` lists every problem with file, row and URN.
- `dp approve` refuses if the inbox changed after the draft was built. Approved weeks in `state/` give the next week its "what changed" lines and the plan-slip history, so keep `state/` between runs.
- `dp --help` and `dp <command> --help` list every option.

**First time with platform files.** Write a first crosswalk and register from the NextData and validation exports, review them, then run the week as above:

```bash
python scripts/seed_crosswalk.py --inbox inbox   # writes inbox/crosswalk.csv: review it, set reviewed=yes
python scripts/seed_register.py  --inbox inbox   # writes inbox/register.xlsx, one Products row per counted product
```

How names become products, what is counted and how each product gets its business domain are in `docs/metric-definitions.md` ("Platform sources"). A product's domain comes from the crosswalk's `domain` column, else `registry/product-domains.yaml` (edit it when a product moves), else the name rules in `registry/platform.yaml`, else Unknown.

## Demos

```bash
sh scripts/demo.sh                    # open demo/index.html
sh scripts/demo.sh --named            # open demo/index-named.html
sh scripts/demo.sh --rebuild          # rebuild demo/index.html from the current app first (add --named for the named demo)
python scripts/make_showcase.py generate   # rewrite the showcase inbox (tests/fixtures/inbox-showcase/) from the script's table
```

The named demo is built from `tests/fixtures/inbox-named-demo/`: weeks 39 and 40 are built and signed off first, so "what changed" and Slipping are real pipeline results. `python scripts/make_named_demo.py generate --inbox inbox` refreshes that fixture from a real inbox, copying only product names and domains. The version approved on 2026-10-07 is the git tag `demo-2026-10-07`; in a clone, `git checkout demo-2026-10-07 -- demo/index.html` brings it back.

## Changing the dashboard

| To change | Edit | Then |
| --- | --- | --- |
| A rule, metric or flag | `registry/*.yaml`, the function in `pipeline/`, `docs/metric-definitions.md` | Add or adjust a test in `tests/acceptance/`; `python scripts/update_golden.py` and review the diff |
| The look or a view | `app/src/` (React + TypeScript; colours, type sizes and fonts are the tokens in `app/src/styles/tokens.css`) | `cd app && npm run dev` previews the showcase week (open `/template.html`); `npm run build` refreshes the template that `dp build` uses |
| The snapshot contract | `schema/snapshot.schema.json` and `pipeline/contracts.py` | `cd app && npm run gen:types` |
| The register template | `pipeline/readers/register.py` | `python scripts/make_register.py --template --out templates/register.xlsx` |

Adding a KPI is a registry entry, a function and a test.

## Tests

```bash
python -m pytest              # acceptance tests, plus end-to-end tests on the built dashboard
cd app && npm test            # component and selector tests
```

The end-to-end tests need the template and the test browser (`sh scripts/setup.sh --tests`); they are skipped when the template is missing. They run against `app/dist/template.html`, so rebuild it (`npm run build` in `app/`) after changing the app.

## Repository layout

| Path | What |
| --- | --- |
| `dp/` | The `dp` command (check, build, preview, approve). |
| `pipeline/` | Readers, lifecycle, data-quality checks, metric and flag functions, snapshot assembly, the data-quality report. |
| `registry/` | Metrics, flags, comment screening, domains, the product-to-domain map and the platform rules, as YAML. |
| `schema/` | The snapshot contract between the pipeline and the app. |
| `app/` | The one-file dashboard: React, TypeScript and Vite, built into `app/dist/template.html`. |
| `templates/` | The register workbook template for Data Product Owners. |
| `scripts/` | Setup, demos, register and crosswalk seeding, golden snapshots. |
| `tests/` | Acceptance tests (one per rule in the definitions), end-to-end tests, and the made-up inboxes and golden snapshots in `tests/fixtures/`. |
| `demo/` | The two saved demo dashboards. |
| `docs/` | `metric-definitions.md` (every rule), `adr/` (architecture decisions), `archive/` (the original plans). |

## Guardrails

- Real register values never enter the repository: `inbox/`, `state/` and `out/` are ignored by git. Real product and domain names appear only in `registry/product-domains.yaml`, `tests/fixtures/inbox-named-demo/` and `demo/index-named.html`, which is acceptable because the repository is private.
- No credentials for SharePoint, NextData or Snowflake exist in this release.
- Third-party material in the app: the argenx wordmark, the brand fonts (SIL OFL, licences next to them in `app/src/assets/fonts/`) and the vendored react-bits components (MIT + Commons Clause: use in this app is fine, redistributing the components themselves is not; see `app/src/components/reactbits/README.md`).

## On Windows

`scripts/setup.sh` is for macOS and Linux. On Windows the same steps in PowerShell are below (not tested here):

```powershell
py -3 -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
cd app; npm ci; npm run build; cd ..
.venv\Scripts\dp build --inbox tests\fixtures\inbox-golden --week 2026-W41
```
