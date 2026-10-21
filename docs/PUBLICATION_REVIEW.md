# Public sharing review

## Included

Original integration scripts, configurable paths/endpoints, credential-free examples, six disabled lab alert templates, Incident Live dashboard, regression fixtures, setup instructions and anonymized experiment summaries. The dedicated Hermes walkthrough covers authentication, encrypted credential lookup, MCP, webhook delivery and the permitted lab helpers.

Original integration code uses MIT. The payment test fixture retains its upstream Apache-2.0 notice; see THIRD_PARTY_NOTICES.md. Upstream product repositories remain separate and keep their own licenses. SETUP.md pins the OTel Demo source and images used by the lab.

## Excluded

Local configuration and live alert IDs, generated service units, credentials, keyrings, raw agent databases, telemetry archives, container data and upstream checkouts. Original private operational material is retained outside this repository. Historical reports have anonymized paths, operator identifiers and instance/session IDs; their private raw archives are not distributed.

## Checks performed

- 30 unit tests passed without credentials or live infrastructure.
- A clean temporary copy at a path containing spaces passed the same tests, both alert previews and service-unit rendering/verification.
- Recommendation and Quote candidate checks each passed three functional checks in disposable containers; these checks did not replace the deployed labs.
- Publication pattern checks reviewed the proposed public file set, reachable Git blobs and remote URLs. The existing committed history contained only the initial README blob.
- Documentation/configuration reviewed for machine paths and live instance data; examples use local overrides and placeholders.

The scanner reports locations and categories without printing matched secret values. Pattern scanning and manual review cannot prove that every possible secret or identifying detail has been found. Review newly added files and evidence before each release.

## Remaining release work

A complete fresh installation on another host has not been tested. External account setup, keyring unlocking, upstream deployment and network wiring remain operator steps. Simulithic is marked coming soon and excluded from the setup workflow. The lab is not a general production remediation system.

After the initial preparation, the integration was committed and pushed at the owner’s request. The owner subsequently made the repository public. Further review covers reachable Git history as well as current files; no history rewrite is needed unless a real exposure is found.
