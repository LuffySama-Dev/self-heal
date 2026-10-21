# Preregistered pilot protocol

Six sequential fresh Hermes one-shot runs, same prompt and frozen source.
Order: baseline, graph, graph, baseline, baseline, graph (three paired trials).
Baseline toolsets: file. Graph condition: file plus graphify-benchmark.
Model: existing configured GPT-6.1 SOL, medium reasoning, normal speed.
Use --ignore-rules to exclude injected rules/memories and fresh sessions (no resume).
No live telemetry queries: identical recorded incident evidence for all runs.
No source .git directory, prior repair report, regression test or answer key.
Graph built from the exact same faulty snapshot, using code-only local extraction.
Indexing cost recorded separately from per-run end-to-end wall time.
Wall time includes startup, model inference and tool execution. Record Hermes
usage-file counters, observable tool calls, final response and source hashes.
Timeout: 240 seconds per run; report timeouts, errors and incomplete runs, no silent reruns.

Score 0–6, one point each: identifies inclusive >= expiry boundary; explains
current-month rejection; proposes strict > without weakening expired rejection;
correctly cites charge.js and condition; traces index.js handler to charge.js;
proposes current-month acceptance and past-month rejection regression tests.
Scoring is manual by the coordinator, unblinded; preserve answers for independent review.
A wrong core diagnosis fails regardless of score. No deployment/recovery claim allowed.

Report every run, medians and paired differences. Do not make significance or
general speedup claims from three pairs of one deliberately simple incident.
Graph warm-up/order, server/model latency and visible clues in the fixed evidence
limit generalization. This is a diagnosis pilot, not a production repair benchmark.
