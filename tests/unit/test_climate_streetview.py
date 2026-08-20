from __future__ import annotations

import urbancode as uc


def test_climate_and_streetview_are_lazy() -> None:
    import os
    import subprocess
    import sys
    from pathlib import Path

    assert "climate" in uc.__all__
    assert "streetview" in uc.__all__
    root = Path(__file__).resolve().parents[2]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root) + os.pathsep + env.get("PYTHONPATH", "")
    code = (
        "import sys, urbancode as uc; "
        "c = uc.climate; s = uc.streetview; "
        "assert c.__name__ == 'urbancode.climate'; "
        "assert s.__name__ == 'urbancode.streetview'; "
        "heavy = ('torch', 'pythermalcomfort', 'zensvi'); "
        "bad = [m for m in heavy if m in sys.modules]; "
        "assert not bad, bad"
    )
    subprocess.check_call([sys.executable, "-c", code], env=env)


def test_streetview_aliases_svi() -> None:
    import warnings

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        assert uc.svi.comfort is uc.streetview.comfort
        assert uc.svi.fetch is uc.streetview.fetch
    assert any("uc.svi is deprecated" in str(w.message) for w in caught)


def test_streetview_color_does_not_import_torch() -> None:
    import os
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root) + os.pathsep + env.get("PYTHONPATH", "")
    code = (
        "import sys, urbancode as uc; "
        "fn = uc.streetview.filename; "
        "color = uc.streetview.color; "
        "assert callable(fn) and callable(color); "
        "assert 'torch' not in sys.modules"
    )
    subprocess.check_call([sys.executable, "-c", code], env=env)


def test_imagery_utci_is_climate_utci() -> None:
    assert uc.imagery.utci is uc.climate.utci
