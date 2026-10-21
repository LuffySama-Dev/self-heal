# Simulithic testing integration — preparation

> Historical integration notes, with operator paths and instance IDs anonymized. Use [SETUP.md](../../SETUP.md) for current portable setup. Private runtime archives referenced below are not part of this repository.

Installed official Simulithic CLI 0.4.8 on 20 October 2026 using its documented
installer, which validates the downloaded package SHA-256 against the official
manifest. Installer saved at `${PROJECTS_DIR}/simulithic/install.sh`.
CLI: `${HOME}/.simulithic/cli/simulithic`. Existing Node 26.7.0 is available
at `${HOME}/.hermes/tools/node-26.7.0-linux-x64/bin/node`.
Verified CLI help; no sudo, account creation, login, uploads, tunnels or paid runs.

This is the vendor's local client for a hosted testing service, not an established
self-hosted OSS testing backend. Official docs require an account/invite. The local
web explorer is fetched after authentication. Remote simulations against localhost
require a temporary public tunnel. Account access, workspace and run budget remain
unconfirmed. Do not start a tunnel or paid simulation without settling those steps.

Proposed first flow: add a product to the cart, check out using a dummy valid card,
and assert the order confirmation. Add explicit current-month-expiry and expired-card
cases; generic successful checkout alone would not cover our demonstrated defect.
The paused payment-only lab has no frontend; browser tests need an approved web
staging target wired to the intended payment revision. The main demo must not be
silently repointed to the repair lab.

Keep the existing unit/regression tests. Simulithic adds end-to-end user-flow testing;
it does not replace validation of code boundaries or SigNoz recovery evidence.
No GitHub App installation, CI workflow, PR comments or production monitors are
configured. Repository management remains a separate authorized step.

The CLI's login implementation writes its local JSON configuration with mode 0600
and directory mode 0700. This is not encrypted-keyring storage. Before authentication,
choose a credential approach consistent with the project's encrypted-keyring practice;
the CLI supports SIMULITHIC_TOKEN for runtime token injection.

Official references:
- https://www.simulithic.com/docs/cli
- https://www.simulithic.com/docs/agent-setup
- https://www.simulithic.com/docs/faq
