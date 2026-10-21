# Graphify + Hermes: checkout correctness pilot

21 October 2026 · Three paired runs · Publication draft, not published

**On this one seeded incident, instructed Graphify use reduced median investigation time by 8.7% and median reported token volume by 37.1%. Both conditions produced correct repairs in all three runs.** This is encouraging exploratory evidence for this workflow, not a general speedup or accuracy claim.

## The new incident

A new-to-these-trials checkout defect reused a mutable Money object across prepared order items. Individually correct product and currency responses became order-sensitive totals: A at 10.25 ×2 and B at 4.75 ×3 plus 1.50 shipping should total 36.25, but A→B produced 25.25 and B→A produced 52.75. Single-item baskets remained correct. The source path runs through catalog lookup, currency conversion, item preparation, shared money arithmetic and the payment request. The graph helped navigate relationships; it did not execute the application or itself prove the defect.

This is harder than the previous explicit payment rejection: there is no exception pinpointing a line, and the symptom is a silent wrong total with an ordering dependency. It is still one compact Go aliasing bug with informative fixture observations, not a complex production incident. Prior model pretraining knowledge cannot be excluded.

The coordinator independently invoked real checkout preparation code and money helpers using deterministic local Go catalog/currency doubles. Original source passed all eight new acceptance cases; the faulty snapshot failed five. **No live SigNoz incident, payment, deployment or recovery was measured in this study.** The prior automated payment recovery drill is a separate result.

## Design

Fresh Hermes profiles with no prior conversations, rule/memory injection disabled, identical frozen source and incident evidence. No Git history, prior report, or acceptance-test file was present in the model-visible tree. Source boundaries were prompt-enforced; audited observable file calls remained inside that tree. Model: GPT-6.1 SOL, medium reasoning, provider default tier. Twenty turns and 300 seconds per run. No runs failed or were rerun.

Six sequential investigations were arranged as three seeded randomized pairs: source/graph, graph/source, source/graph. Both conditions had file tools. The graph condition also had seven Graphify tools and an explicit requirement for a symbol query and a relationship lookup. This compares an **instructed Graphify workflow** with source-only investigation; it does not isolate mere tool availability or show that an agent would elect to use Graphify unaided. All graph runs used it successfully (3, 2 and 2 calls) and checked source.

Each run proposed exact source replacements without editing files. After completion, the evaluator applied the proposed edits to a separate clean copy and ran the withheld acceptance tests plus existing checkout/money tests: **70 leaf test cases per candidate**. All six candidates restored the correct original implementation and passed all 70. Coordinator manual rubric: 6/6 for every answer, unblinded; executable correctness is reported separately.

## Every run

| Run | Condition | Wall seconds | Graph calls | Reported total tokens | Tests |
|---|---|---:|---:|---:|---:|
| 1 | source | 67.49 | 0 | 91,071 | 70/70 |
| 2 | graphify | 62.97 | 3 | 83,787 | 70/70 |
| 3 | graphify | 53.34 | 2 | 60,151 | 70/70 |
| 4 | source | 68.94 | 0 | 144,442 | 70/70 |
| 5 | source | 77.05 | 0 | 131,770 | 70/70 |
| 6 | graphify | 67.43 | 2 | 82,933 | 70/70 |

| Measure | Source only | Graphify |
|---|---:|---:|
| Successful repairs | 3/3 | 3/3 |
| Median complete-output time | 68.94s | 62.97s |
| Median reported total tokens | 131,770 | 82,933 |
| Median uncached input tokens | 31,278 | 23,513 |
| Median file reads | 9 | 7 |
| Median source searches | 9 | 5 |

Graphify was faster in each pair by 4.53s, 15.60s and 9.63s. The 8.7% result is the reduction in condition medians, not an average paired percentage. No significance test or population confidence claim is made from three pairs of one defect.

Reported total tokens include cache-read tokens and exclude separately recorded auxiliary title-generation usage. They are not unique code tokens, dollar cost or subscription usage limits. Provider-reported uncached input, output, cache reads, auxiliary usage and API calls are retained separately. Responses also differ in length. The included Codex subscription does not establish a zero infrastructure cost.

Graphify indexing took 2.56s, with 3,959 nodes and 6,883 edges. A fresh output directory was used, but OS filesystem caches were warm. Indexing is **excluded** from run timing and must be included/amortized for real use. Wall time includes agent startup, MCP/tool work and model response; separate candidate validation is excluded. A shared server and provider caches/latency were not controlled. Small evaluator jobs overlapped some later inference runs.

## Redaction artifact and limits

All six runs saw Hermes's secret-redaction layer mask the valid source constant `+999999999` as `+999****9999` in tool output. Runs 1 and 3 consequently mentioned an apparent unrelated compile blocker. The real source was unchanged and compiled successfully for every validation. We retained the runs and this artifact instead of altering the tool configuration mid-experiment. It may affect search/time; it is not a second seeded defect. Correct diagnosis does not mean every ancillary assertion was correct.

The fixture directly exercises item preparation and money arithmetic with stubbed downstream clients; it does not run a whole distributed checkout or capture actual payment requests. Non-USD cases check currency preservation with deterministic values, not real exchange-rate behavior. Passing these tests is not exhaustive correctness. Graph traversal results were sometimes truncated by tool output budgets. Manual grading is unblinded. More defects, services, repetitions and tighter controls are needed before generalizing to complex applications.

## Reproducibility and publication

The archive contains the frozen protocol, prompts, seeded order, versions/hashes, injection patch, hidden test source, per-run proposed repairs, observable tool transcripts, raw token reports, executable validation logs, metrics, audit and scoring. Private reasoning and authentication files are excluded. Paths in the public copy are anonymized. Nothing was posted or pushed.

Raw private evidence: `${PROJECTS_DIR}/self-heal-benchmarks/2026-10-21-checkout-alias/`.

Original repository: https://github.com/open-telemetry/opentelemetry-demo
Exact commit: `dedc0178918e260823323b8d95005a8cb924b007`. Apply seed-defect.patch to an archive of that commit to reproduce the frozen source, and verify source-hashes.json. The snapshot was taken from upstream tracked source; active deployment overrides were excluded. Model profiles and tools are recorded by the scripts; edit anonymized installation paths before re-running. Use an authenticated Hermes installation; never distribute auth.json.

A suitable publication claim: “In a three-pair pilot on a seeded checkout pricing bug, required Graphify use reduced median investigation time by 8.7% and reported token volume by 37.1%; both conditions produced repairs passing 70 tests. Results are exploratory, from one incident.”
