Made-up `dp fetch-github` output for the GitHub tests (`tests/acceptance/test_github.py`), matched to the products
of `tests/fixtures/inbox-platform`. Tests copy it into a copy of that inbox as `github/`. As of 2026-10-09:

| Repository | Matches | Case |
| --- | --- | --- |
| edp-ops-dp-crmsys | nxd:dp-ops-crmsys (Live) | prod successes in and before the window, a superseded (inactive) success, a failure, a re-run that ends in success, a pending deployment, one after the as-of date |
| edp-hcp-dp-hcp_master | nxd:dp-hcp-hcp-master (Live) | no prod deployment (GH_STATUS), an error |
| edp-patient-dp-journey_insights | nxd:dp-patient-journey-insights | one dev success |
| edp-claims-dp-rx_claims | nxd:dp-claims-rx-claims | no deployments |
| edp-ops-dp-legacy_cube | urn:dp:com:legacy-cube | prod success outside the window |
| edp-patient-dp-pj_app | nxd:hubservice-nxd | matched by its data_product_urn |
| edp-patient-dp-crmsys | nxd:dp-ops-crmsys | second repository for one product (GH_DUPLICATE) |
| edp-ops-dp-orphan_feed | nothing | GH_NOT_IN_REGISTER |
| edp-nxd-dp-template, edp-hcp-dp-survey_test | not counted | tooling team, test name |
