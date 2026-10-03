# Tanilo Eval Harness (formerly AgentOracle)

Scripts and results from a May 2026 evaluation of the `/evaluate` endpoint against the AVeriTeC 2024 dev set. Tanilo was AgentOracle until September 2026; file names, script names and the dated records in this repository keep the old name.

## Status, 2026-10-03

- **One result is published here.** 287 of 498 scored claims correct, 57.6% label accuracy, on the AVeriTeC 2024 dev set. It was measured on 28 May 2026 against the live `/evaluate` endpoint. The dev set has 500 claims; the results file has 500 rows, of which 498 were scored. The other two calls returned server errors.
- **That figure describes a pipeline that has since been replaced.** The evaluation pipeline behind `/evaluate` was replaced in September 2026. The benchmark has not been re-run since. The figure says nothing about the service as it runs today.
- **Split.** First 250 claims by dataset order: 144 of 250, 57.6%. Last 250: 143 of 248 scored, 57.7%. The mapping from the service's verdicts to AVeriTeC's four labels was chosen on the first half.
- **No FEVER result is published here, and none should be cited.** The FEVER run this repository planned was deferred and is not in the repository. See the corrections record in [tanilo-receipt-spec](https://github.com/TKCollective/tanilo-receipt-spec#corrections-record).
- **No one outside Tanilo is recorded in this repository as having re-run the evaluation.**

The dated record of the run, including per-label accuracy and its caveats, is in [RESULTS.md](./RESULTS.md). That file is kept as written.

## Can the harness be run today?

**Scoring: yes.** The scoring script re-computes the published figures from the published results file, with no network access:

```bash
git clone https://github.com/TKCollective/tanilo-eval-harness
cd tanilo-eval-harness
python3 scripts/score.py results/2026-05-28-dev/results.jsonl
```

Checked on 2026-10-03: it prints `Overall: 57.6% (287/498)` for the full set and `Overall: 57.7% (143/248)` for the last-250 split.

**A fresh run: not as written.** `scripts/run_dev_eval.py` sends all 500 dev claims to the live `/evaluate` endpoint. The endpoint is now a rate-limited free beta, and its limits are below what a 500-claim run needs. A fresh run would also measure the current pipeline, so it would not reproduce the May figure. No fresh run has been attempted since the pipeline changed.

`scripts/run_full_eval.sh` and the Docker file belong to the larger plan described below and have not been checked against the current service.

## What is in this repository

```
.
├── RESULTS.md                    # dated record of the 28 May 2026 run
├── results/2026-05-28-dev/       # results.jsonl (500 rows) and summary.json
├── results/smoke/                # 4-claim smoke test, not an evaluation
├── scripts/                      # run_dev_eval.py, score.py, download scripts, run_full_eval.sh
├── src/                          # FEVER and AVeriTeC runners, scoring, HTTP clients
├── docker/                       # Dockerfile for the planned full run
└── docs/SPRINT_PLAN.md           # the April 2026 plan
```

## History: the May 2026 plan

This repository was announced on 30 April 2026 and made public on 14 May 2026, with a 14-day plan. The plan is kept in [docs/SPRINT_PLAN.md](./docs/SPRINT_PLAN.md). What it set out to do, and what this repository shows was done:

| Planned | In this repository |
|---|---|
| AVeriTeC 2024 dev run | Done on 28 May 2026 (planned for 11 May). Results above. |
| FEVER 1.0 dev run | Not done. Deferred on 19 May 2026; no results are in the repository. |
| Recall@5 and Recall@10 on evidence retrieval for the full run | Scoring code exists in `src/scoring/`. No full-run figures are published. |
| A no-retrieval baseline to help estimate contamination | Runner code exists (`src/averitec/runner_parametric.py`). No results are published. |
| A published Docker image and a signed receipt for the run | No record of either in this repository. |
| A clean-machine re-run before publication | No record in this repository. |

The earlier README said the harness would make the service's numbers reproducible by third parties. One AVeriTeC result can be re-scored from the published file. The run itself cannot be repeated against the same pipeline, because that pipeline was replaced.

## Datasets

- **AVeriTeC**: Schlichtkrull et al. Dev set from [MichSchli/AVeriTeC](https://github.com/MichSchli/AVeriTeC) (`data/dev.json`). The test set is hidden, so only dev-set results are possible here.
- **FEVER 1.0**: Thorne et al., 2018. Loader code only; no results.

See each dataset's own page for its licence terms.

## Limitations

- The published result is for one run, on one date, on a pipeline that has been replaced.
- 2 of the 500 dev claims returned server errors and were not scored.
- The label mapping was chosen by inspecting the first half of the dev set.
- Language models may have seen benchmark claims in training. The planned no-retrieval baseline that would help estimate this has no published results.

## Questions

Open an issue in this repository, or write to joe@tanilo.io.

---

**License:** MIT (harness code). Dataset licences per their respective owners.

**Cite this harness:**

```
@software{tanilo_eval_2026,
  author  = {Tanilo (TK Collective LLC)},
  title   = {Tanilo Eval Harness (formerly AgentOracle Eval Harness)},
  year    = {2026},
  url     = {https://github.com/TKCollective/tanilo-eval-harness}
}
```
