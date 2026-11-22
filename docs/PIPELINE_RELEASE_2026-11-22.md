# Pipeline release provenance

This release publishes the agreed historical base, hybrid sensitivity and observed-only comparison, with the complete producer and the supplied completed results. It promotes the reviewed temporary integration work into the project publication. It does not rerun Joohee's experiments, overwrite frozen observations or edit Google Docs.

## Reviewed upstream sources

- Main starting point: `64fe8cd9fa5aa5beac6b1a4a66339bd3acda08ed`.
- Hong Jin [PR #1](https://github.com/carloida/DBA5103_finalproject/pull/1), reviewed head `244dda807805acbd28b33c56292e6eecb1de936a`: four Python source files were imported and reconciled. Its earlier generated own-hour demand, duplicate nested demand and old pilot results are excluded from the current release. They remain in upstream history, not current report inputs.
- Fu Yan [PR #2](https://github.com/carloida/DBA5103_finalproject/pull/2), reviewed head `169043a843d4f67cf9ca3381d0d37be5a633c822`: all four source files imported. Local refinements standardize CSV line endings and score paired finite validation support; verified main-case numerical outputs are unchanged.
- Joohee's [Drive handoff and checks](JOOHEE_HANDOFF_2026-11-22.md): all 13 supplied files preserved byte-for-byte, with the original source/output SHA-256 in the handoff manifest.

The upstream heads are recorded as merge parents after their reviewed content has already been integrated. The integration tree is retained to preserve local fixes and exclude superseded generated artifacts. This is a reviewed source integration, not acceptance of PR #1's old demand outputs as the base case.

## Current execution paths

- `run_project_pipeline.py`: the report scenario, with verification-only default and explicit rebuild flags. Three policy cases, no implicit experiment reruns, no overwriting the published output tree.
- The Hong Jin model/policy/multiday CLI defaults now point to the published historical CSV.gz. The old own-hour producer is retained only as labelled legacy source.
- Joohee's source is unchanged; its original standalone model CLI retains the old example path. Use the project wrapper or an explicit `--demand` argument. Her experiment runner already accepts its demand file explicitly.
- `run_integrated_pipeline.py`: separate updated-cost extension. Its outcomes must remain labelled apart from the report's supplied numbers.

## Release checks

The default project verification passed: all 13 supplied hashes, demand schemas and finite values, 14-day keys, demand totals, accounting, recorded solver/replay diagnostics and the report cost constants. The new case-orchestration check passed with subprocesses mocked: historical/hybrid/observed arguments, 31-column observed comparison and protected output destinations. It did not execute solver runs. Existing demand and integration-invariant tests had passed during the temporary integration.

The [report reconciliation](REPORT_RECONCILIATION_2026-11-22.md) is part of this release. Publishing runnable code and supplied results does not certify the draft's stronger routing, diversion or profit claims. The five additional city/time packages remain observed-data preparation, not completed policy tests.
