# Graphify + Hermes: payment-diagnosis pilot

20 October 2026. Local experiment; not published or pushed.

## Finding

**This pilot found no demonstrated speed or accuracy improvement from Graphify.**
Every run diagnosed the same expiry-boundary bug correctly. File-only median
wall time was **35.21s**; explicitly using Graphify was
**35.61s** (1.2% higher).
A difference this small in three runs per condition is not evidence of a reliable
performance difference. This is not proof that Graphify cannot help harder tasks.

| Condition | Runs | Median seconds | Range seconds | Runs using graph | Quality score |
|---|---:|---:|---:|---:|---:|
| baseline | 3 | 35.21 | 34.76–37.51 | 0/3 | 6/6 |
| graph | 3 | 36.10 | 35.85–36.65 | 0/3 | 6/6 |
| graph-required | 3 | 35.61 | 34.25–38.41 | 3/3 | 6/6 |

The original six-run protocol made Graphify optional. None of its three
Graphify-enabled runs used the graph. Those are an availability result, not a
measurement of graph-assisted diagnosis. We preserved them and declared a separate
three-run supplement explicitly requiring graph use. No unsuccessful runs were
silently replaced. All nine runs completed successfully and left source unchanged.

## What was tested

A fixed OTel Demo source snapshot with a deliberately introduced single-character
expiry comparison defect (`>` changed to `>=`). The supplied incident evidence
contained the failed expiry date and successful comparison date, without a stack
line. Each fresh Hermes session identified the condition, explained the failure,
proposed the minimal correction, traced the handler/validation path and proposed
regression tests. No patches, regression-test execution, deployment or live
recovery were part of these diagnosis runs.

GPT-6.1 SOL via the existing Codex subscription, medium reasoning, 20-turn maximum,
normal/default service tier. Hermes v0.22.2; Graphify OSS 0.9.92.
Graphify commit: `86c57be8204673c2a1b9849a3292a7dd3ab373d8`.
OTel source commit: `dedc0178918e260823323b8d95005a8cb924b007`, plus the recorded defect.
No .git history, prior repair reports or new regression suite were in the snapshot.
Fresh sessions used `--ignore-rules`, excluding injected rules/memories; neither
condition could access session history through its allowed tools.

The frozen local graph had 3,959 nodes and 6,883 edges. Its initial code-only build
took **2.585 seconds**, measured separately. No LLM extraction or Graphify cloud was
used. Graph context was sent to Hermes's configured model during investigation.

## Every run

| Run | Condition | Seconds | Graph queries | Tool calls | API calls | Reported total tokens | Score |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 | baseline | 37.51 | 0 | 6 | 5 | 40,792 | 6/6 |
| 2 | graph | 35.85 | 0 | 6 | 5 | 36,652 | 6/6 |
| 3 | graph | 36.65 | 0 | 7 | 5 | 47,778 | 6/6 |
| 4 | baseline | 35.21 | 0 | 6 | 5 | 41,187 | 6/6 |
| 5 | baseline | 34.76 | 0 | 8 | 4 | 30,782 | 6/6 |
| 6 | graph | 36.10 | 0 | 6 | 5 | 36,636 | 6/6 |
| 7 | graph-required | 34.25 | 1 | 6 | 4 | 32,318 | 6/6 |
| 8 | graph-required | 38.41 | 2 | 7 | 5 | 39,167 | 6/6 |
| 9 | graph-required | 35.61 | 1 | 8 | 4 | 32,793 | 6/6 |

`baseline` means file tools. `graph` means file tools plus optional graph access.
`graph-required` is the separately declared explicit-use supplement. Original
run order was B,G,G,B,B,G; supplemental G-required runs followed afterward.
Wall time includes process startup, model requests and tool execution, not graph
indexing. API and token counters are copied from Hermes usage files, not reconstructed
billing. The table uses main-run counters; raw usage retains auxiliary title-generation
usage separately. Tool counts include discovery/wrapper calls. Graph queries count
the actual underlying MCP invocations. Cache read/input/output fields are preserved
separately in metrics.csv; do not infer dollar savings from token totals or the
subscription's zero incremental-cost display.

## Quality review

Manual, unblinded review by the coordinator, with a six-point rubric written before
runs: inclusive boundary identified; current-month explanation; strict-comparison
fix; correct file/line; handler-to-validator path; acceptance and expired-rejection
tests. All nine met all six criteria and did not claim deployed recovery. This
rubric checks a bounded diagnosis task, not general software-engineering ability.
Final responses and observable tool transcripts are retained for independent review.
No private reasoning traces are included.

## Limitations

One simple, deliberately seeded defect; three runs per condition; the incident
message is a strong clue; sequential model calls share uncontrolled cache/load
conditions; no random seed control; unblinded scoring. The supplement changes the
instruction and runs later, so its comparison is exploratory and order-confounded.
Graph construction/index freshness is controlled here; actual production version
mapping and dynamic cross-service relationships are not. No statistical significance,
generalized speedup, token-saving or autonomous-repair claim is justified.

## Reproduction

Use the recorded product commits and model settings. Export the OTel commit with
`git archive` into a clean source directory; apply defect.patch. Build its graph
with `GRAPHIFY_BACKEND=none graphify extract SOURCE --code-only --max-workers 2 --out INDEX`.
Configure local MCP server graphify-benchmark with that graph and the seven graph-query
tools recorded in the setup notes. Adapt SOURCE_ROOT in the included prompt.
Run fresh `hermes --ignore-rules --in SOURCE -t file --usage-file usage.json -z PROMPT`
for baseline; use `-t file,graphify-benchmark` for graph access. Follow the two saved
protocols, retaining failures and usage files. Use the supplemental prompt only for
the separately labelled required-use condition. Compare hashes before/after.
The local runner scripts, frozen source and raw evidence are retained outside the
self-heal repository. The shareable bundle contains sanitized protocols, prompts,
metadata, source hashes, usage, final answers and observable tool transcripts.

## Suggested publication wording

“In a nine-run pilot on one simple payment-expiry defect, Hermes correctly diagnosed
the issue in every run. Median diagnosis time was 35.21s with file tools and
35.61s when Graphify use was required. Optional Graphify access was not used
by the agent in three trials. This small experiment did not demonstrate a speed or
accuracy benefit; a broader multi-service evaluation is needed.”
