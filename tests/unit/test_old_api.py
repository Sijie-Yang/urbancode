def test_import_stays_light() -> None:
    import os
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root) + os.pathsep + env.get("PYTHONPATH", "")
    code = (
        "import sys, urbancode as uc; "
        "assert uc.__version__; "
        "heavy = ('torch', 'osmnx', 'zensvi', 'streetlevel', 'pythermalcomfort', 'geopandas', 'rasterio'); "
        "bad = [m for m in heavy if m in sys.modules]; "
        "assert not bad, bad"
    )
    subprocess.check_call([sys.executable, "-c", code], env=env)


def test_public_exports_exist() -> None:
    import urbancode as uc

    for name in (
        "download_network",
        "save_network",
        "load_saved_network",
        "graph_to_gdf",
        "graph_from_gdf",
        "calculate_accessibility_metrics",
        "svi",
        "streetview",
        "climate",
        "network",
        "adapters",
        "backends",
        "units",
        "fusion",
        "images",
        "perception",
        "StudyArea",
        "fetch",
        "City",
        "Layer",
        "load",
    ):
        assert name in uc.__all__
    assert uc.__version__ == "0.3.0"
