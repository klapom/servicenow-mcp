"""Drift-protection test for the bundled hints rules.yaml (Sprint 16.5).

Ensures the YAML shipped with the package validates against the live set
of registered MCP tool names. Tool renames or removals fail at CI, not
at server boot.
"""

from __future__ import annotations

import re
from pathlib import Path

_PKG = "servicenow_mcp"
_RULES_PATH = Path(__file__).resolve().parents[2] / "src" / _PKG / "hints" / "rules.yaml"


def _registered_public_tools() -> set[str]:
    """Scan src/ for ``@mcp.tool(name="...")`` decorators, excluding internal_*."""
    src_dir = Path(__file__).resolve().parents[2] / "src" / _PKG
    pattern = re.compile(r'@mcp\.tool\(name="([^"]+)"\)')
    found: set[str] = set()
    for path in src_dir.rglob("*.py"):
        for m in pattern.finditer(path.read_text(encoding="utf-8")):
            found.add(m.group(1))
    return {t for t in found if not t.startswith("internal_")}


def test_bundled_rules_yaml_loads_against_registry():
    """The shipped rules.yaml validates without ValueError against the
    actually-registered public-tool set."""
    from mcp_toolkit_py.hints import load_rules_for_known_tools

    known = _registered_public_tools()
    assert known, "no @mcp.tool(name=...) decorators found in src/ — scan broken?"

    rs = load_rules_for_known_tools(_RULES_PATH, known_tools=known)
    assert rs.version == 1
    assert len(rs.tools) >= 1


def test_every_rules_yaml_target_is_registered():
    """Every source-tool key and every hint target in rules.yaml must be
    a tool the server actually serves."""
    import yaml

    registered = _registered_public_tools()
    data = yaml.safe_load(_RULES_PATH.read_text(encoding="utf-8"))

    referenced: set[str] = set()
    for src_tool, body in (data.get("tools") or {}).items():
        referenced.add(src_tool)
        for hint in body.get("hints", []):
            referenced.add(hint["tool"])

    unknown = referenced - registered
    assert not unknown, (
        f"rules.yaml references tools that aren't registered on the server: {unknown}"
    )
