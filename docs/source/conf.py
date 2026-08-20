"""Sphinx configuration for UrbanCode."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from urbancode import __version__

project = "UrbanCode"
copyright = "2024–2026, Sijie Yang"
author = "Sijie Yang"
version = __version__
release = __version__

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
]

exclude_patterns = [
    "tutorials/**",
    "user_guide/**",
    "gallery/**",
    "architecture/**",
    "catalog/*.rst",
    "workflows/punggol_end_to_end.rst",
    "workflows/climate_heat_stress.rst",
    "workflows/real_heat_stress.rst",
    "workflows/streetview_to_grid.rst",
    "workflows/multi_city_contract.rst",
    "workflows/real_multi_city.rst",
]
html_static_path = ["_static"]
html_theme = "sphinx_rtd_theme"
html_last_updated_fmt = "%b %d, %Y"

autodoc_typehints = "description"
autodoc_default_options = {
    "members": False,
    "undoc-members": False,
    "show-inheritance": True,
}
# Heavy extras are mocked so RTD can document public street-view
# signatures without installing torch / OpenCV / transformers.
autodoc_mock_imports = [
    "torch",
    "torchvision",
    "cv2",
    "transformers",
    "sklearn",
    "tqdm",
    "tensorboard",
    "scipy",
    "osmnx",
    "geopandas",
    "momepy",
    "networkx",
    "matplotlib",
    "rasterio",
    "rioxarray",
    "zensvi",
    "streetlevel",
    "city2graph",
    "pythermalcomfort",
]
napoleon_google_docstring = True
napoleon_numpy_docstring = True

# Offline docs builds must not fail on inventory download.
intersphinx_mapping: dict[str, tuple[str, str | None]] = {}

nitpicky = True
nitpick_ignore = [
    ("py:class", "Path"),
    ("py:class", "pathlib.Path"),
    ("py:class", "Any"),
    ("py:class", "Mapping"),
    ("py:class", "Iterable"),
    ("py:class", "LayerKind"),
    ("py:class", "City"),
    ("py:class", "numpy.ndarray"),
    ("py:class", "optional"),
    ("py:class", "pd.DataFrame"),
    ("py:class", "DataFrame"),
    ("py:class", "nx.MultiDiGraph"),
    ("py:class", "networkx.MultiDiGraph"),
    ("py:class", "networkx.classes.multidigraph.MultiDiGraph"),
    ("py:class", "gpd.GeoDataFrame"),
    ("py:class", "geopandas.GeoDataFrame"),
    ("py:class", "geopandas.geodataframe.GeoDataFrame"),
    ("py:class", "urbancode.errors.MissingExtraError"),
    ("py:class", "Layer"),
    ("py:class", "urbancode.city.Layer"),
    ("py:class", "numpy.ndarray | Layer"),
    ("py:class", "Path | Any"),
    ("py:exc", "ContractError"),
]

_WORKFLOW_REDIRECTS = {
    "workflows/punggol_end_to_end.html": "punggol_urban_profile.html",
    "workflows/climate_heat_stress.html": "heat_exposure.html",
    "workflows/real_heat_stress.html": "heat_exposure.html",
    "workflows/streetview_to_grid.html": "street_experience.html",
    "workflows/multi_city_contract.html": "multi_city_comparison.html",
    "workflows/real_multi_city.html": "multi_city_comparison.html",
}


def setup(app) -> None:
    def _write_redirects(app_obj, exception) -> None:
        if exception is not None:
            return
        out = Path(app_obj.outdir)
        for src, dest in _WORKFLOW_REDIRECTS.items():
            path = out / src
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                "<!DOCTYPE html><html><head>"
                f'<meta http-equiv="refresh" content="0; url={dest}">'
                f"<title>Moved</title></head><body><p>Moved to "
                f'<a href="{dest}">{dest}</a>.</p></body></html>\n',
                encoding="utf-8",
            )

    app.connect("build-finished", _write_redirects)
