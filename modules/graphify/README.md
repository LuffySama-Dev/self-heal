# Local Graphify OSS for Hermes

> Historical integration notes, with operator paths and instance IDs anonymized. Use [SETUP.md](../../SETUP.md) for current portable setup. Private runtime archives referenced below are not part of this repository.

Installed 20 October 2026. Graphify source, environment and graph artifacts are
outside self-heal. No sudo or hosted Graphify account was needed.

- Source: `${PROJECTS_DIR}/graphify`, version 0.9.92, commit
  `86c57be8204673c2a1b9849a3292a7dd3ab373d8`.
- Runtime: `${PROJECTS_DIR}/graphify/.venv/bin/python` (Python 3.14.7).
  Installed the official source package with `mcp` and `sql` extras using the
  already available uv executable. Dependency snapshot:
  `${PROJECTS_DIR}/graphify-data/installed-requirements.txt`.
- Indexed checkout: `${PROJECTS_DIR}/otel-demo-repair-lab`.
- Graph: `${PROJECTS_DIR}/graphify-data/otel-demo-repair-lab/graphify-out/graph.json`.
- Refresh: `${PROJECTS_DIR}/graphify-data/refresh.sh`.

Extraction uses `--code-only`, two workers and `GRAPHIFY_BACKEND=none`.
Code parsing is local, with no LLM extraction or Graphify cloud connection.
Documents/images are excluded. The graph contains 3,980 nodes and 6,900 edges.
These are extracted graph entities/relationships, not proof of runtime calls.

## Hermes connection

`~/.hermes/config.yaml` defines stdio MCP server `graphify`, launching the runtime
above with `-m graphify.serve` and the absolute graph path. No HTTP port or API key
is used. Seven local graph-query tools are enabled: query_graph, get_node,
get_neighbors, get_community, god_nodes, graph_stats and shortest_path. The three
GitHub PR tools are not enabled because repository management is separate.

The authenticated SigNoz webhook route includes `mcp-graphify`, alongside its
existing SigNoz, terminal and file tools. Its instructions use telemetry to
identify the service, then graph queries to locate source and inspect relationships.
Source editing and deployment-review boundaries remain unchanged.

`hermes mcp test graphify` verified connection and discovery of ten server tools.
For a one-shot CLI check use `-t graphify` (the CLI expects the configured server
name); the webhook route uses the dynamically registered `mcp-graphify` toolset.
The previous configuration is backed up at
`${HOME}/.hermes/config.before-graphify.yaml`, mode 0600.

## Coverage and freshness

This graph describes the repair checkout, not necessarily the running deployment.
Refresh after source changes and confirm the deployment revision during incidents.
No background index watcher was installed. Hermes graph queries may send returned
source context to its configured model provider, just like its file-reading tools.
Local indexing does not mean the entire Hermes investigation stays on the host.

Some files are unsupported or have no extracted symbols. Initial extraction
reported a syntax limitation in `src/ad/build.gradle`; SQL support was then added.
Environment files were excluded by Graphify. An absent node/edge does not prove
that no dependency exists. Graph paths supplement traces, logs and source inspection.

The payment lab has since completed automatic repair/deployment/recovery. Graphify measurement reports are saved in benchmarks/2026-10-20 and benchmarks/2026-10-21. The later checkout pilot found a modest timing/token reduction with equal repair success; see its limitations before generalizing.

## Official references

- https://graphify.com/mcp
- https://github.com/Graphify-Labs/graphify
- https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp/

Live Hermes verification completed: graph_stats and query_graph located
chargeServiceHandler at src/payment/index.js:12, its import of charge.js,
and charge at src/payment/charge.js:27. The run used only graph tools.
Evidence: ${PROJECTS_DIR}/graphify-data/hermes-verification.md.
