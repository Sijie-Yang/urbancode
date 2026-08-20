Installation
============

UrbanCode requires Python 3.10 or newer on macOS, Linux, or Windows.
The core wheel is small. GIS and deep-learning stacks are extras.

There is no ``uc doctor`` command. After install, probe extras with
:func:`urbancode.backends.status` or :func:`urbancode.backends.available`.

Minimal core
------------

::

   pip install urbancode
   python -c "import urbancode as uc; print(uc.__version__)"

Unlocks ``StudyArea``, ``City``, ``Layer``, ``IndicatorResult``,
``uc.backends``, and the CLI. Does not import GeoPandas, OSMnx,
rasterio, or torch. You can inspect metadata and run ``uc --version``.
You cannot build a grid or compute NDVI until you add extras.

Extras
------

.. list-table::
   :header-rows: 1
   :widths: 16 28 28 28

   * - Extra
     - Capabilities
     - Important backends
     - Typical workflow
   * - ``vector``
     - City I/O, :doc:`/domains/units`, :doc:`/domains/fusion`
     - GeoPandas, Shapely, pyproj, pyogrio
     - Load a pocket and aggregate polygons
   * - ``network``
     - :doc:`/domains/network` (includes vector)
     - OSMnx, NetworkX, momepy
     - Walk graph, centrality, reachability
   * - ``imagery``
     - :doc:`/domains/imagery`
     - Rasterio, rioxarray, Xarray, pystac-client
     - NDVI, terrain, zonal stats
   * - ``climate``
     - :doc:`/domains/climate`
     - pythermalcomfort
     - UTCI (rasters still need ``imagery``)
   * - ``streetview``
     - :doc:`/domains/streetview`
     - Pillow, OpenCV, PyTorch, ZenSVI
     - Color, live fetch, deprecated comfort
   * - ``perception``
     - :func:`urbancode.perception.thermal_affordance`
     - PyTorch, TorchVision, OpenCV
     - TCIS VATA / VPI
   * - ``research``
     - perception + streetview + climate + viz
     - Torch plus GIS extras
     - Research-case reproduction
   * - ``spatial-stats``
     - Phase 2 extras only; no public API yet
     - h3, libpysal, esda
     - City Landscape (not implemented)
   * - ``viz``
     - matplotlib plotting
     - Matplotlib, Pillow
     - ``Layer.plot`` / ``IndicatorResult.plot``
   * - ``standard``
     - vector + network + imagery + climate + viz
     - GIS stack, no torch
     - :doc:`/workflows/punggol_urban_profile`
   * - ``all``
     - standard + streetview + perception + survey + graph
     - torch, ZenSVI, city2graph
     - Full local development
   * - ``dev``
     - pytest, linters, build
     - pytest, black, flake8
     - Package tests
   * - ``docs``
     - Sphinx HTML
     - sphinx, sphinx-rtd-theme
     - ``sphinx-build -W``

``svi`` and ``download`` remain install aliases of ``streetview``.
``gallery`` is an alias of ``viz``. Torch is not in ``standard``.

When to install ``all``
-----------------------

Install ``urbancode[all]`` only if you need street-view models and
every optional adapter in one environment. Perception models also
install with ``urbancode[perception]`` or ``urbancode[research]``.
For research on networks and imagery, ``urbancode[standard]`` is
enough.

Heavyweight notes
-----------------

* Rasterio / GDAL wheels usually install from PyPI. If your platform
  needs a system GDAL, follow the Rasterio install guide.
* ``streetview`` pulls PyTorch. CPU wheels are large; GPU builds are
  your choice, not an UrbanCode extra.
* Live ``uc.fetch`` and ``uc.streetview.fetch`` need network access.
  Offline docs and CI use committed fixtures under
  ``examples/data/real/``.

Downloads go to ``~/.cache/urbancode/`` (or ``URBANCODE_CACHE_DIR``).

Development
-----------

::

   pip install -e ".[dev,docs]"
   python -c "import urbancode as uc; print(uc.backends.status())"
   sphinx-build -W --keep-going -b html docs/source docs/build/html

See also: :doc:`/reference/extras`, :doc:`/reference/ecosystem`,
:doc:`quickstart`.
