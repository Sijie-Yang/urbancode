from __future__ import annotations

import ast
from pathlib import Path

FORBIDDEN = {
    "rasterio",
    "geopandas",
    "networkx",
    "shapely",
    "urbancode.imagery.write",
}

OFFLINE = Path(__file__).resolve().parents[2] / "examples" / "offline"


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
            names.add(node.module)
    return names


def test_offline_examples_do_not_import_gis_libs() -> None:
    scripts = sorted(OFFLINE.glob("0*.py"))
    assert scripts, "expected numbered offline examples"
    for path in scripts:
        imported = _imported_modules(path)
        bad = imported & FORBIDDEN
        assert not bad, f"{path.name} imports {sorted(bad)}"
        allowed_roots = {"urbancode", "pathlib", "__future__"}
        roots = {name.split(".")[0] for name in imported}
        unexpected = roots - allowed_roots
        assert not unexpected, f"{path.name} has unexpected imports: {sorted(unexpected)}"
