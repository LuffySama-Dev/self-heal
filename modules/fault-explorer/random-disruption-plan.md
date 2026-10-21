# Random source-disruption program — proposal

Planning only, 21 October 2026. No implementation, installation, source mutation or deployment authorized by this plan. This extends the earlier exploration: generate mutations from actual source locations, instead of selecting only a handful of hand-authored bug patches.

## Goal and unresolved wording

A button or CLI command selects a service, source location and code transformation randomly, builds a faulty candidate and deploys it into an isolated demo environment. The generator introduces faults; Hermes remains a separate consumer of genuine alerts. Clarify whether “not fixed” means faults must not be predetermined, or whether automatic repair should be disabled during this experiment. Do not change Hermes behavior until clarified.

Random selection does not guarantee runtime disruption: edits can be invalid, unreachable, equivalent or silently incorrect. Report each outcome. A mode that retries until traffic demonstrably fails is conditional sampling and must preserve rejected attempts; do not call it unbiased random fault generation. Random bytes are possible but primarily exercise parse/build failures rather than running-service diagnosis. Use source-aware mutation operators as the initial proposal.

## Installed inventory verified on server

23 running containers with Compose project label `opentelemetry-demo`, excluding SigNoz and the two payment repair lab containers.

14 application components: accounting, ad, cart, checkout, currency, email, fraud-detection, frontend, image-provider, payment, product-catalog, quote, recommendation, shipping.

9 supporting components: astronomy-db, flagd, flagd-ui, frontend-proxy, kafka, load-generator, otel-collector, telemetry-docs, valkey-cart.

This categorization is for targeting this project, not an official universal microservice count. The installed inventory is authoritative; upstream documentation can describe a different version. Initial application targeting excludes observability, fault controller, flag service, databases and message storage. Adding targets requires a supported language/build/deployment adapter.

## Proposed modules

1. Inventory and selector: declare eligible services/source roots/languages/build commands; select service uniformly first, then a compatible source node and operator. This prevents larger services dominating purely through file count. Support a fresh seed per run and explicit seed for replay.
2. Mutation engine: parse source with a language-aware parser; discover candidate sites; mutate comparisons, booleans, arithmetic, returns or collection handling. Operators are predefined transformation rules, not fixed bug locations or solutions. Language-specific adapters are required; one generic text-replacement script cannot reliably cover the demo's languages. Start with JavaScript/TypeScript, then expand target coverage explicitly.
3. Candidate runner: create a disposable source copy and image; record pristine hashes; apply exactly one mutation; build and probe under bounded time/resources. Build rejection, healthy/no observed effect, business-behavior failure and operational disruption are separate outcomes. Reject uncompilable candidates from the runtime-disruption mode without deleting their records. Optionally support build-failure experiments as a separate future mode.
4. Experiment controller: deploy only to the selected isolated target, sustain deterministic traffic, observe errors/latency/crash/functional checks, record start/stop and provide reset to an immutable healthy baseline. One active fault initially; random scheduling and simultaneous faults can follow. Recovery by reset must be distinguished from agent repair. Keep the controller and telemetry functioning during target disruption.
5. Evidence adapter: persist seed, selection algorithm version, eligible candidates, base revision, exact patch, build/image hashes, timestamps, rejected attempts, symptoms and cleanup result. Export experiment lifecycle to SigNoz. Keep the injected patch/answer separate from the repair agent's access if measuring diagnostic ability; a different directory alone is not access isolation.

## User flow

Start random disruption → choose target/location/operator → build isolated candidate → deploy → run traffic → report observed outcome → either leave incident for the independent repair agent or hold fault for observation, according to selected mode → reset on request or experiment timeout.

A seed plus recorded source/operator versions and exact patch makes the injection reproducible; it does not guarantee identical runtime timing or identical AI behavior. Syntax-preserving mutations can still violate type/build checks, so validation remains necessary.

## Proposed first milestone

Separate small CLI program; browser button comes after the execution path works. Cover supported JS/TS application services discovered in the installed checkout, with per-service adapters, one fault per run, explicit runtime-disruption mode and bounded candidate attempts. Do not claim coverage of all 14 application components at launch. No hardcoded payment-only defect, no hidden repeated injection after Hermes repairs it.

Existing payment-only alert, dashboard adapter and deployment helper are not generic multi-service integrations. Before end-to-end runs on another service, add its detector, source mapping, traffic fixture and authorized isolated deployment path. Silent wrong totals need business-invariant checks; error-rate alerts alone cannot detect them. Multi-service experiment dashboard events should retain both selected target and affected downstream services.

## Task list

- [x] Verify installed service inventory and distinguish application from supporting components.
- [x] Draft generated-mutation architecture and honest outcome classifications.
- [ ] Clarify random/not-predetermined faults versus disabling automatic repair.
- [ ] Agree eligible services, isolated environment and first language adapters.
- [ ] Agree single-click versus scheduled mode, candidate retry limit and reset timeout.
- [ ] Implement only after explicit implementation instruction.
- [ ] Validate replay, invalid/no-effect candidates, successful disruption and reset.
- [ ] Extend alert/dashboard/deployment mappings before multi-service Hermes drills.

## Official references

- [OTel Demo architecture](https://opentelemetry.io/docs/demo/architecture/): application topology and dependencies.
- [OTel Demo feature flags](https://opentelemetry.io/docs/demo/feature-flags/): built-in scenarios are preconfigured faults, distinct from generating source edits.
- [Stryker supported mutators](https://stryker-mutator.io/docs/mutation-testing-elements/supported-mutators/): examples of source-level transformation families. Stryker is a mutation-testing tool, not a ready-made deployed incident controller; its language support does not cover the entire demo.

## Implementation decision — 21 October 2026

User approved a practical generator without redesigning Hermes access. Injector code and operator records are not sent to Hermes; sudo-only installation is a guardrail, not a strict blindness claim. Working first adapter targets the existing payment lab with four source mutations, syntax/runtime qualification and bounded full-flow observation. This narrows the earlier multi-service first milestone to finish an operational path before additional adapters. See `../fault-injector/README.md`. Configuration faults, latency/memory mutations and other services are not implemented in this first adapter.
