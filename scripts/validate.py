#!/usr/bin/env python3
"""Validate this repo: skill frontmatter (agentskills.io), plugin/marketplace
manifests, and no-drift against the Pagnet CLI/bridge source.

Usage:
  python3 scripts/validate.py [path-to-pagnet-repo]

The pagnet repo argument enables the drift checks (MCP tool names, CLI verb
names, SDK env var names, MCP config shape). CI passes a shallow clone;
locally, pass a pagnet checkout, or omit the argument to skip drift.
"""

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
errors = []

EXPECTED_TOOLS = {
    "pagnet_identity",
    "pagnet_search",
    "pagnet_invoke",
    "pagnet_invocation_get",
    "pagnet_ask",
    "pagnet_ask_get",
    "pagnet_events",
}


def err(msg):
    errors.append(msg)


def check_skill():
    """agentskills.io frontmatter rules for skills/pagnet/SKILL.md."""
    path = ROOT / "skills" / "pagnet" / "SKILL.md"
    if not path.is_file():
        err("skills/pagnet/SKILL.md: missing")
        return ""
    text = path.read_text()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        err("SKILL.md: missing YAML frontmatter block")
        return text
    fm = m.group(1)
    name = re.search(r"^name: (.+)$", fm, re.M)
    desc = re.search(r"^description: (.+)$", fm, re.M)
    if not name:
        err("SKILL.md frontmatter: missing `name`")
    else:
        n = name.group(1).strip()
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", n):
            err(f"SKILL.md frontmatter: name {n!r} must be lowercase alnum/hyphens, no leading/trailing/consecutive hyphens")
        if not 1 <= len(n) <= 64:
            err("SKILL.md frontmatter: name must be 1-64 characters")
        if n != "pagnet":
            err(f"SKILL.md frontmatter: name {n!r} must match its directory name")
    if not desc:
        err("SKILL.md frontmatter: missing `description`")
    else:
        d = desc.group(1).strip()
        if not 1 <= len(d) <= 1024:
            err(f"SKILL.md frontmatter: description is {len(d)} chars (must be 1-1024)")
    body_lines = len(text[m.end():].splitlines())
    if body_lines > 500:
        err(f"SKILL.md body is {body_lines} lines (max 500)")
    return text


def check_json(rel):
    try:
        return json.loads((ROOT / rel).read_text())
    except FileNotFoundError:
        err(f"{rel}: missing")
        return None
    except json.JSONDecodeError as e:
        err(f"{rel}: invalid JSON ({e})")
        return None


def check_manifests(mcp, plugin, market):
    if mcp is not None:
        srv = (mcp.get("mcpServers") or {}).get("pagnet")
        if not isinstance(srv, dict):
            err(".mcp.json: missing mcpServers.pagnet")
            return
        if srv.get("command") != "pagnet":
            err(".mcp.json: pagnet.command must be the `pagnet` binary")
        args = srv.get("args") or []
        if args[:3] != ["mcp", "external", "--network"]:
            err(f".mcp.json: pagnet.args must start with mcp external --network (got {args[:3]})")
        for k in ("PAGNET_SERVER", "PAGNET_CREDENTIAL"):
            if k not in (srv.get("env") or {}):
                err(f".mcp.json: pagnet.env missing {k}")
    if plugin is not None:
        if plugin.get("name") != "pagnet":
            err("plugin.json: name must be `pagnet`")
        for k in ("server", "credential", "network"):
            if k not in (plugin.get("userConfig") or {}):
                err(f"plugin.json: userConfig missing `{k}`")
    if market is not None:
        if not market.get("name"):
            err("marketplace.json: missing `name`")
        if "name" not in (market.get("owner") or {}):
            err("marketplace.json: owner.name is required")
        plugs = market.get("plugins") or []
        if not plugs or plugs[0].get("name") != "pagnet":
            err("marketplace.json: first plugin entry must be named `pagnet`")
        elif plugs[0].get("source") not in (".", "./"):
            err("marketplace.json: plugin source must be the marketplace root (`.`)")


def check_drift(skill_text, repo):
    """Fail if the skill drifts from the CLI/bridge source, or the source
    loses a surface the skill documents."""
    bridge = repo / "internal" / "externalbridge"
    if not bridge.is_dir():
        err(f"drift: {bridge} not found — is the pagnet repo path correct?")
        return
    tools = set()
    for f in bridge.glob("*.go"):
        tools |= set(re.findall(r'mcp\.NewTool\("(pagnet_[a-z_]+)"', f.read_text()))
    for t in sorted(EXPECTED_TOOLS - tools):
        err(f"drift: bridge source no longer defines {t} — update or remove it from the skill")
    for t in sorted(tools):
        if t not in skill_text:
            err(f"drift: tool {t} is not documented in SKILL.md")
    ext = repo / "cmd" / "pagnet" / "external_cli.go"
    if ext.is_file():
        verbs = set()
        for u in re.findall(r'^\s*Use:\s*"([^"]+)"', ext.read_text(), re.M):
            verbs.add(u.split()[0])
        for v in sorted(verbs):
            if v not in skill_text:
                err(f"drift: CLI verb `{v}` is not documented in SKILL.md")
    sdk_txt = "".join(f.read_text() for f in (repo / "sdk").glob("*.go"))
    for const, val in re.findall(r'(Env(?:Server|Credential))\s*=\s*"(P[A-Z_]+)"', sdk_txt):
        if val not in skill_text:
            err(f"drift: SDK env var {val} ({const}) is not documented in SKILL.md")
    if not re.search(r'"args":\s*\[\s*"mcp",\s*"external",\s*"--network"', skill_text):
        err("drift: SKILL.md MCP config no longer matches `pagnet mcp external --network`")


def main():
    skill_text = check_skill()
    mcp = check_json(".mcp.json")
    plugin = check_json(".claude-plugin/plugin.json")
    market = check_json(".claude-plugin/marketplace.json")
    check_manifests(mcp, plugin, market)
    if len(sys.argv) > 1:
        check_drift(skill_text, pathlib.Path(sys.argv[1]).resolve())
    if errors:
        print("\n".join("FAIL: " + e for e in errors))
        sys.exit(1)
    print("validate: ok")


if __name__ == "__main__":
    main()
