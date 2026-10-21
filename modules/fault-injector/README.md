# Random source-fault injector

See [setup](../../SETUP.md) before running. The default chooses uniformly among Payment, Recommendation and Quote, then picks a compatible mutation for that service. A seed reproduces both choices. This is a bounded set of transformations, not arbitrary bug generation.

| Service | Mutations |
|---|---|
| Payment | Four card-validation/expiry condition changes. |
| Recommendation | Sampling overflow, catalog-method mismatch, blocking delay. |
| Quote | Response-method mismatch, blocking delay. |

Candidates must compile/parse, start, and fail independent runtime checks before reaching a live lab. No feature flag is enabled. Unknown/ambiguous source anchors, startup failures and no-effect mutations are rejected. Run only against the fixed isolated labs; original demo and production are outside scope.

```bash
python3 modules/fault-injector/injector.py check --development --service quote --seed 0
python3 modules/fault-injector/injector.py run --development
```

`check` does not inject. `run` injects, generates traffic and waits for observed Hermes deployment plus firing/recovery session completion and healthy post-deployment calls. Timeout or interruption attempts baseline restoration. The default timeout is 25 minutes, configurable from 5–30. A shared injector lock and per-service deployment locks coordinate runs. Operator records are private runtime data, not Git files.

Configuration comes from `selfheal_config.py`, `.local/config.json` (or `SELF_HEAL_CONFIG`) and `.local/rules.json`. The latter contains the real symptom alert IDs. Templates in `alert-rules.example.json` contain no deployment IDs and are created disabled. See `scripts/configure_alerts.py`.

## Optional root-only operator installation

Development mode is user-accessible. For a root-only installed copy, first run `python3 scripts/render_units.py`; this also writes `.local/operator-config.json` with resolved absolute paths and an installed rule-file path. Review those settings. From the repository root, the machine owner may then run:

```bash
sudo install -d -o root -g root -m 0700 /opt/self-heal-injector /opt/self-heal-injector/.local /var/lib/self-heal-injector
sudo install -o root -g root -m 0600 modules/fault-injector/injector.py modules/fault-injector/lab_runtime.py selfheal_config.py /opt/self-heal-injector/
sudo install -o root -g root -m 0600 .local/operator-config.json /opt/self-heal-injector/.local/config.json
sudo install -o root -g root -m 0600 .local/rules.json /opt/self-heal-injector/.local/rules.json
sudo install -o root -g root -m 0700 modules/fault-injector/launcher /usr/local/sbin/self-heal-injector
```

The default installation prefix is `/opt/self-heal-injector`; `SELF_HEAL_INSTALL_DIR` can override the launcher's import path. If using a different prefix, adjust the rendered operator config's `rules_file` and the installation commands consistently. Do not pass untrusted environment/configuration into a root command.

Existing installations need the shared configuration module as well as the injector/runtime files after this portability update. No installed copy is modified by editing this repository. Keep shared coordination locks accessible to the configured operator and Hermes service user; do not recursively change ownership of application source. Hermes retains only its existing service-user permissions, although broad Docker authority means root-only file modes are not a strict security boundary. Development source and prior repair history may remain visible; do not call these blind benchmarks.

Live results: [payment](validation-2026-10-21.md), [multi-service](validation-multiservice-2026-10-21.md). These are sanitized historical summaries; raw operator records are intentionally not distributed.
