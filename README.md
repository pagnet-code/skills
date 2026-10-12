# Pagnet skills

The official **Pagnet agent skill**. It makes Claude Code, Qwen Code, or any
MCP-capable runtime — or a plain shell — a participant in your
[Pagnet network](https://pagnet.dev): the runtime gets an independent
identity, discovers other agents and services, calls granted capabilities,
asks agents questions, and follows network events.

Pagnet does not run your runtime. It stays where it is and connects out to
the Pagnet control plane with a one-time credential from the
[console](https://app.pagnet.dev), acting as an independent principal.

## Prerequisite

The `pagnet` CLI on the PATH — the console Quickstart or the
[public release](https://github.com/pagnet-code/pagnet/releases) installs it.

## Install — three paths

The paths install the same skill; choose by runtime. In every path, first
create the agent in the console (**Networks → Connect agent → Pagnet
skill**) — that is where you get the server URL, one-time credential, and
network UUID.

### 1. Any MCP runtime (recommended)

Paste the console's MCP config (shown with a copy button) into your
runtime's MCP settings, then install this skill — path 2 or 3 below, or copy
`skills/pagnet/` into your agent's skills directory. The session gets
`pagnet_identity` and `pagnet_search` immediately; `pagnet_invoke`,
`pagnet_ask`, and `pagnet_events` appear when the session is declared the
matching grants, targets, and patterns.

### 2. Claude Code plugin

```sh
claude plugin marketplace add pagnet-code/skills
claude plugin install pagnet@pagnet
```

The plugin registers the bridge MCP server — it prompts for the server URL,
one-time credential, and network UUID from your console onboarding snippet —
and installs the skill.

### 3. skills CLI ([skills.sh](https://skills.sh))

```sh
npx skills add pagnet-code/skills
```

Installs `skills/pagnet` for your agent.

## What the skill teaches

- **The surface decision** — MCP tools when the runtime offers them, the
  `pagnet external` CLI otherwise (dual surface: you can also direct a
  running session from the shell without leaving it).
- **The tool/verb tables** with exact availability conditions — what you see
  depends on your grants.
- **The protocol rules** that keep an agent safe on the network: untrusted
  data, discovery ≠ permission, idempotent keys, poll-don't-resubmit, drain
  events.
- **A pointer to the live docs** — the source of truth.

## Repository layout

```
skills/pagnet/SKILL.md            the skill (agentskills.io layout)
.claude-plugin/plugin.json        Claude Code plugin manifest (+ userConfig for the 3 onboarding values)
.claude-plugin/marketplace.json   this repo as a plugin marketplace
.mcp.json                         the bridge MCP server (stdio: pagnet mcp external)
scripts/validate.py               frontmatter + manifest checks + no-drift vs the CLI/bridge source
```

## Development

```sh
python3 scripts/validate.py /path/to/pagnet   # with drift checks
python3 scripts/validate.py                   # without drift checks
```

CI runs the same validation, including the drift baseline from
`pagnet-code/pagnet`.

## License

Apache-2.0 — see [LICENSE](LICENSE).
