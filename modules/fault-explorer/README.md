# Random code-fault explorer — exploration

21 October 2026. Design only; no faults injected, services changed or software installed.

Build a separate experiment controller: clicking **Start random incident** selects one reviewed source-code mutation, creates a disposable payment-service snapshot, reproduces its symptom and lets a repair agent investigate. Randomness chooses a known, validated defect; it does not invent arbitrary edits. Keep this project separate from the main demo and the existing payment repair lab until a new target is explicitly selected.

## What existing tools cover

| Capability | What changes | Relevance |
| --- | --- | --- |
| Chaos Mesh Pod/Network experiments | Runtime infrastructure, availability or connectivity | Useful for resilience drills; does not supply an application source defect to repair. [Official PodChaos documentation](https://chaos-mesh.org/docs/simulate-pod-chaos-on-kubernetes/). |
| OTel Demo feature flags | Existing application branches, such as percentage payment failures | Convenient scenario activation; turning a flag off is different from repairing code. [Official flag documentation](https://opentelemetry.io/docs/demo/feature-flags/). |
| Stryker mutation testing | Small code mutations evaluated against tests | Useful model for mutation operators and catalog qualification. Its purpose is measuring tests, rather than orchestrating deployed agent-repair incidents. [Official introduction](https://stryker-mutator.io/docs/). |
| Proposed explorer | A concrete source snapshot, then its built runtime | Adds incident lifecycle, agent separation, verified repair and reset. |

The local OTel checkout already documents a **Scheduler** tab with random flags, variants, durations, concurrency and reproducible seeds in `${PROJECTS_DIR}/opentelemetry-demo/src/flagd-ui/README.md`; its implementation is `lib/flagd_ui/scheduler.ex`. This is local source evidence, not verification that the deployed image exposes the tab. The fetched public [Flagd-UI documentation](https://opentelemetry.io/docs/demo/services/flagd-ui/) describes flag editing; do not promise source mutation or a deployed scheduler from that page.

## First scope

Use one Node payment service, one active experiment, a frozen healthy base, three reviewed mutations and deterministic gRPC traffic. Candidate families are expiry-boundary comparison, expiry-month arithmetic and supported-card eligibility. These remain proposals: each must build and produce a specific observable defect before entering the catalog. Reserve the previously demonstrated `>` to `>=` expiry case for a smoke test and label its familiarity; it is a weak blind benchmark.

Exclude syntax errors, dependency edits, resource exhaustion and simultaneous faults from the first catalog. Introduce checkout totals/aliasing later: silent wrong totals require a business-invariant detector, since successful RPCs and low error rates can coexist with incorrect behavior.

Qualify each entry before use: healthy snapshot passes independent acceptance tests; mutated snapshot builds, stays runnable and fails its intended business checks; controlled traffic reliably exposes the fault; applying the known reference repair restores behavior. Record unsuccessful qualification rather than silently replacing cases. Stryker's [mutant states](https://stryker-mutator.io/docs/mutation-testing-elements/mutant-states-and-metrics/) distinguish invalid, timed-out and surviving mutations; those outcomes should not be counted as successful repair experiments.

## Small modules

- **Catalog:** versioned mutation ID, base source hash, allowed files, patch hash, exact preconditions, traffic recipe, expected symptom, hidden acceptance suite and reference repair. An existing mutation tool could later generate candidates offline; first use explicit patches.
- **Runner:** single-job state machine: ready → preparing → baseline verified → fault reproduced → agent running → evaluating → recovered/failed → resetting → ready. Failed builds or missing symptoms are setup failures. Persist each transition and make duplicate clicks idempotent.
- **Agent adapter:** provide the faulty working tree, normal development tests and incident telemetry; collect edits and a report. Keep the interface independent of Hermes or Graphify so comparisons need no runner changes.
- **Evaluator:** apply the candidate to a fresh faulty snapshot, run withheld behavior checks and existing tests, then verify built-source identity and live gRPC behavior. Telemetry recovery is an additional gate for the end-to-end track.
- **UI:** start, status, elapsed time, telemetry links, stop/reset and completed-run results. Reveal selected defect and reference patch only after the agent finishes. Disable start while busy. A small local controller is sufficient; no separate workflow platform is needed initially.

Persist the seed **and** catalog version, sorted eligible IDs, selection algorithm/version, chosen ID, patch/base/image hashes, traffic fixture, clock/timezone, agent configuration and event timestamps. A seed alone cannot replay a changed catalog or reproduce model output and live timing. Pin or control the clock for expiry tests.

## Boundaries, reset and evaluation

The controller owns the catalog, healthy snapshot and answer key. Give the agent only a per-run faulty source copy: no `.git`, mutation patch, prior report, catalog or hidden tests. Keep controller/evaluator files outside the agent's filesystem and tool access, with separate telemetry access scoped to its experiment. Hide identifying seed/catalog metadata from the agent until evaluation. Merely placing files in another host directory is not a read boundary.

Use a dedicated lab identity/container or VM and a fixed deployment helper. The agent can edit its service source and request evaluation; it should not receive the host Docker socket or arbitrary deployment targets. Docker's [official security documentation](https://docs.docker.com/engine/security/) explains the authority exposed by daemon control. Separate Compose names or a prompt allowlist alone do not isolate a host user with Docker access.

Set a maximum duration, traffic cap and an independent cleanup watchdog. **Reset** restores the immutable known-healthy source/image and per-run state, then checks baseline behavior. **Rollout rollback** restores the preceding deployed image if a candidate fails; that preceding image may still contain the injected bug. Never label rollback as recovered without functional checks. Retain experiment artifacts before disposing of the runtime; report reset failure and block the next run.

Report fault qualification, alert detection, diagnosis, withheld-test repair, live recovery and cleanup separately. Track time to detection/repair/recovery, tool calls, tokens/cost where available and all failures/timeouts. Include healthy control runs to measure false alarms and unnecessary edits. Count evaluator rejection, agent failure and infrastructure failure explicitly; retain every run. Show per-mutation outcomes before aggregate rates. Repeated results on a small known catalog do not establish performance on unseen incidents.

## Fit with the current work

The earlier [payment code-repair trial](../hermes/code-repair-trial.md) demonstrated an injected expiry bug, repair and subsequent recovery, but Git history exposed the introduced change. The [checkout benchmark protocol](../graphify/benchmarks/2026-10-21/protocol.md) already uses withheld tests and source copies without Git; its boundaries were prompt-enforced and it did not measure live alerts or deployment. Reuse those lessons and artifact formats, while preserving their different claims. The [existing deployment helper](../hermes/automatic-lab-deployment.md) provides a useful rollout pattern, but its current authorization targets the existing payment lab; it does not authorize deploying a new explorer target.

Before implementation, decide: is the first milestone a visible end-to-end demo or a blind repair benchmark; should the target be a fresh standalone service or a new clone of the OTel payment service; and should the agent deploy through the fixed helper or submit a patch for the evaluator to deploy? Suggested defaults: fresh OTel payment clone, evaluator-controlled rollout, three fault entries plus healthy controls, then add live SigNoz detection once repeatable repair/reset works.
